"""WorkOS User Management token exchange + refresh for ``como auth login``.

Pure HTTP against WorkOS's public ``/user_management/authenticate`` endpoint:
swap a PKCE authorization ``code`` (with its verifier) for access + refresh
tokens, and later refresh them. Both accept an injectable ``transport`` so the
request shape + response parsing are unit-tested without hitting WorkOS.
"""

from __future__ import annotations

import secrets
import webbrowser
from dataclasses import dataclass

import httpx

from . import _pkce

AUTHENTICATE_URL = "https://api.workos.com/user_management/authenticate"


@dataclass(frozen=True)
class Tokens:
    access_token: str
    refresh_token: str
    user_id: str | None = None
    organization_id: str | None = None


def _parse(data: dict) -> Tokens:
    return Tokens(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        user_id=(data.get("user") or {}).get("id"),
        organization_id=data.get("organization_id"),
    )


def exchange_code(
    *, client_id: str, code: str, code_verifier: str, transport: httpx.BaseTransport | None = None
) -> Tokens:
    """Exchange a PKCE authorization code for tokens (public client — no secret)."""
    with httpx.Client(timeout=30.0, transport=transport) as client:
        resp = client.post(
            AUTHENTICATE_URL,
            data={
                "client_id": client_id,
                "grant_type": "authorization_code",
                "code": code,
                "code_verifier": code_verifier,
            },
        )
        resp.raise_for_status()
        return _parse(resp.json())


def refresh_tokens(
    *,
    client_id: str,
    refresh_token: str,
    organization_id: str | None = None,
    transport: httpx.BaseTransport | None = None,
) -> Tokens:
    """Get a fresh access token (and a rotated refresh token — persist it).

    Passing ``organization_id`` switches the new access token to that org (its
    ``org_id``/role/permission claims), which is how a multi-org CLI selects a
    workspace.
    """
    body = {"client_id": client_id, "grant_type": "refresh_token", "refresh_token": refresh_token}
    if organization_id:
        body["organization_id"] = organization_id
    with httpx.Client(timeout=30.0, transport=transport) as client:
        resp = client.post(AUTHENTICATE_URL, data=body)
        resp.raise_for_status()
        return _parse(resp.json())


def login_via_pkce(*, client_id: str, port: int = _pkce.LOOPBACK_PORT, open_browser: bool = True) -> Tokens:
    """Full AuthKit PKCE login: generate the verifier/challenge, open the browser
    to WorkOS, capture the code on the loopback, validate the CSRF ``state``, and
    exchange the code for tokens. Returns the WorkOS tokens; the caller persists
    them. The pure helpers it composes are unit-tested in test_pkce; this glue is
    unit-tested with the I/O mocked (test_workos_auth)."""
    verifier, challenge = _pkce.generate_pkce()
    state = secrets.token_urlsafe(24)
    url = _pkce.build_authorize_url(client_id=client_id, code_challenge=challenge, state=state, port=port)
    if open_browser:
        webbrowser.open(url)
    result = _pkce.wait_for_callback(port=port)
    if result.error:
        raise RuntimeError(f"WorkOS sign-in failed: {result.error}")
    if not result.code:
        raise RuntimeError("no authorization code received (sign-in timed out?)")
    if result.state != state:
        raise RuntimeError("state mismatch — possible CSRF; aborting login")
    return exchange_code(client_id=client_id, code=result.code, code_verifier=verifier)
