"""WorkOS AuthKit CLI Auth — the OAuth 2.0 Device Authorization Grant (RFC 8628).

``como auth login`` uses WorkOS's CLI Auth: request a device code, show the user
a short ``user_code`` + URL, and poll WorkOS for tokens while they approve in a
browser. There is **no loopback server, no port, and no redirect URI** — so it
works over SSH / headless and can't collide on a fixed port. Tokens come back
from the same ``/user_management/authenticate`` endpoint as every other AuthKit
flow, so storage, refresh, and JWT validation are all shared and unchanged.

The CLI is a **public client**: no ``client_secret`` is ever sent (RFC 8628
§5.6 forbids embedding secrets in device clients). ``refresh_tokens`` is the same
public-client call (``grant_type=refresh_token``, ``client_id`` only).
"""

from __future__ import annotations

import time
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass

import httpx

WORKOS_BASE = "https://api.workos.com"
DEVICE_AUTHORIZE_URL = f"{WORKOS_BASE}/user_management/authorize/device"
AUTHENTICATE_URL = f"{WORKOS_BASE}/user_management/authenticate"
DEVICE_CODE_GRANT = "urn:ietf:params:oauth:grant-type:device_code"

# RFC 8628 §3.5: default poll interval if the server omits one; on `slow_down`
# the client MUST increase the interval by 5 seconds.
_DEFAULT_INTERVAL_SECONDS = 5
_SLOW_DOWN_INCREMENT_SECONDS = 5


@dataclass(frozen=True)
class Tokens:
    access_token: str
    refresh_token: str
    user_id: str | None = None
    organization_id: str | None = None


@dataclass(frozen=True)
class DeviceAuthorization:
    """The device-authorization response the user acts on (RFC 8628 §3.2)."""

    device_code: str  # secret — polled, never shown to the user
    user_code: str  # short human code the user confirms (e.g. "RRGQ-BJVS")
    verification_uri: str  # where the user goes to enter the code
    verification_uri_complete: str | None  # same URL with the code pre-filled
    expires_in: int  # seconds the device/user code remain valid
    interval: int  # minimum seconds between polls


class DeviceAuthError(RuntimeError):
    """Login could not be completed (declined, expired, or a protocol error)."""


def _parse_tokens(data: dict) -> Tokens:
    return Tokens(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        user_id=(data.get("user") or {}).get("id"),
        organization_id=data.get("organization_id"),
    )


def _oauth_error(resp: httpx.Response) -> str | None:
    """The OAuth 2.0 ``error`` code from a 400 token response, if any."""
    try:
        return resp.json().get("error")
    except ValueError:
        return None


def request_device_authorization(
    *, client_id: str, transport: httpx.BaseTransport | None = None
) -> DeviceAuthorization:
    """Step 1 (RFC 8628 §3.1) — get a device + user code. Public client: the only
    parameter is ``client_id`` (no secret)."""
    with httpx.Client(timeout=30.0, transport=transport) as client:
        resp = client.post(DEVICE_AUTHORIZE_URL, data={"client_id": client_id})
        resp.raise_for_status()
        data = resp.json()
    return DeviceAuthorization(
        device_code=data["device_code"],
        user_code=data["user_code"],
        verification_uri=data["verification_uri"],
        verification_uri_complete=data.get("verification_uri_complete"),
        expires_in=int(data.get("expires_in", 300)),
        interval=int(data.get("interval", _DEFAULT_INTERVAL_SECONDS)),
    )


def poll_for_tokens(
    *,
    client_id: str,
    device: DeviceAuthorization,
    transport: httpx.BaseTransport | None = None,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], float] = time.monotonic,
) -> Tokens:
    """Step 3 (RFC 8628 sections 3.4-3.5) — poll ``/authenticate`` until approved.

    Honors the server ``interval``, backs off 5s on ``slow_down``, treats
    ``access_denied``/``expired_token`` as terminal, and gives up once
    ``expires_in`` elapses. ``sleep``/``now`` are injectable for tests.
    """
    interval = max(device.interval, 1)
    deadline = now() + device.expires_in
    body = {
        "client_id": client_id,
        "grant_type": DEVICE_CODE_GRANT,
        "device_code": device.device_code,
    }
    with httpx.Client(timeout=30.0, transport=transport) as client:
        while True:
            if now() >= deadline:
                raise DeviceAuthError("Sign-in timed out before it was approved.")
            sleep(interval)
            try:
                resp = client.post(AUTHENTICATE_URL, data=body)
            except httpx.HTTPError:
                # Transient network error — back off and keep trying until the
                # deadline (RFC 8628 §3.5 recommends backing off on timeouts).
                interval += _SLOW_DOWN_INCREMENT_SECONDS
                continue
            if resp.status_code == 200:
                return _parse_tokens(resp.json())
            error = _oauth_error(resp)
            if error == "authorization_pending":
                continue
            if error == "slow_down":
                interval += _SLOW_DOWN_INCREMENT_SECONDS
                continue
            if error == "access_denied":
                raise DeviceAuthError("Sign-in was declined.")
            if error == "expired_token":
                raise DeviceAuthError("The sign-in code expired. Run `como auth login` again.")
            raise DeviceAuthError(f"WorkOS sign-in failed: {error or resp.text}")


def refresh_tokens(
    *,
    client_id: str,
    refresh_token: str,
    organization_id: str | None = None,
    transport: httpx.BaseTransport | None = None,
) -> Tokens:
    """Get a fresh access token (and a rotated refresh token — persist it).

    Public client: ``client_id`` only, no ``client_secret``. Passing
    ``organization_id`` switches the new access token to that org (its
    ``org_id``/role/permission claims), which is how a multi-org CLI selects a
    workspace.
    """
    body = {"client_id": client_id, "grant_type": "refresh_token", "refresh_token": refresh_token}
    if organization_id:
        body["organization_id"] = organization_id
    with httpx.Client(timeout=30.0, transport=transport) as client:
        resp = client.post(AUTHENTICATE_URL, data=body)
        resp.raise_for_status()
        return _parse_tokens(resp.json())


def login_via_device(
    *,
    client_id: str,
    open_browser: bool = True,
    transport: httpx.BaseTransport | None = None,
    on_prompt: Callable[[DeviceAuthorization], None] | None = None,
) -> Tokens:
    """Full CLI Auth (device grant) login: request a code, prompt the user to
    approve it in the browser, then poll for tokens. ``on_prompt`` is how the CLI
    shows the ``user_code`` + URL; if ``open_browser`` is set we also open
    ``verification_uri_complete`` (the code pre-filled) for a one-click approval.
    Returns the WorkOS tokens; the caller persists them."""
    device = request_device_authorization(client_id=client_id, transport=transport)
    if on_prompt is not None:
        on_prompt(device)
    if open_browser and device.verification_uri_complete:
        webbrowser.open(device.verification_uri_complete)
    return poll_for_tokens(client_id=client_id, device=device, transport=transport)
