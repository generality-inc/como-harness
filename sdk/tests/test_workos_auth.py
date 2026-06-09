"""WorkOS CLI Auth (device authorization grant) — request, poll, and refresh.

All WorkOS I/O is mocked with ``httpx.MockTransport`` so the request shape and
the RFC 8628 polling state machine are exercised without hitting the network.
"""

from __future__ import annotations

import httpx
import pytest

from como import _workos_auth
from como._workos_auth import (
    DeviceAuthError,
    DeviceAuthorization,
    Tokens,
    login_via_device,
    poll_for_tokens,
    refresh_tokens,
    request_device_authorization,
)


def _form(request: httpx.Request) -> dict[str, str]:
    return dict(httpx.QueryParams(request.content.decode()))


def _device(**over: object) -> DeviceAuthorization:
    base: dict[str, object] = {
        "device_code": "DC",
        "user_code": "WXYZ-1234",
        "verification_uri": "https://auth.example/device",
        "verification_uri_complete": "https://auth.example/device?code=WXYZ-1234",
        "expires_in": 300,
        "interval": 5,
    }
    base.update(over)
    return DeviceAuthorization(**base)  # type: ignore[arg-type]


def test_request_device_authorization_is_public_and_parses_fields() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == _workos_auth.DEVICE_AUTHORIZE_URL
        assert _form(request) == {"client_id": "cid"}  # public client: client_id only
        return httpx.Response(
            200,
            json={
                "device_code": "DC",
                "user_code": "WXYZ-1234",
                "verification_uri": "https://auth.example/device",
                "verification_uri_complete": "https://auth.example/device?code=WXYZ-1234",
                "expires_in": 300,
                "interval": 5,
            },
        )

    dev = request_device_authorization(client_id="cid", transport=httpx.MockTransport(handler))
    assert dev.device_code == "DC"
    assert dev.user_code == "WXYZ-1234"
    assert dev.verification_uri_complete is not None
    assert dev.verification_uri_complete.endswith("code=WXYZ-1234")
    assert dev.interval == 5


def test_poll_authorization_pending_then_success() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        body = _form(request)
        assert body["grant_type"] == "urn:ietf:params:oauth:grant-type:device_code"
        assert body["device_code"] == "DC"
        assert body["client_id"] == "cid"
        assert "client_secret" not in body  # public client — never a secret
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(400, json={"error": "authorization_pending"})
        return httpx.Response(
            200,
            json={
                "access_token": "AT",
                "refresh_token": "RT",
                "user": {"id": "u1"},
                "organization_id": "org1",
            },
        )

    tok = poll_for_tokens(
        client_id="cid",
        device=_device(),
        transport=httpx.MockTransport(handler),
        sleep=lambda _s: None,
        now=lambda: 0.0,
    )
    assert tok == Tokens("AT", "RT", "u1", "org1")
    assert calls["n"] == 3


def test_poll_slow_down_increases_interval_by_5s() -> None:
    seq = ["slow_down", "authorization_pending", "ok"]
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        which = seq[calls["n"]]
        calls["n"] += 1
        if which == "ok":
            return httpx.Response(200, json={"access_token": "AT", "refresh_token": "RT"})
        return httpx.Response(400, json={"error": which})

    slept: list[float] = []
    poll_for_tokens(
        client_id="cid",
        device=_device(interval=5),
        transport=httpx.MockTransport(handler),
        sleep=slept.append,
        now=lambda: 0.0,
    )
    # first wait 5s; after slow_down the next wait is 10s.
    assert slept[0] == 5
    assert slept[1] == 10


@pytest.mark.parametrize(
    ("error", "match"),
    [("access_denied", "declined"), ("expired_token", "expired")],
)
def test_poll_terminal_errors_raise(error: str, match: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": error})

    with pytest.raises(DeviceAuthError, match=match):
        poll_for_tokens(
            client_id="cid",
            device=_device(),
            transport=httpx.MockTransport(handler),
            sleep=lambda _s: None,
            now=lambda: 0.0,
        )


def test_poll_gives_up_at_deadline() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "authorization_pending"})

    ticks = iter([0.0, 0.0, 1.0, 9999.0])  # deadline calc, ok, ok, expired

    with pytest.raises(DeviceAuthError, match="timed out"):
        poll_for_tokens(
            client_id="cid",
            device=_device(expires_in=10),
            transport=httpx.MockTransport(handler),
            sleep=lambda _s: None,
            now=lambda: next(ticks),
        )


def test_refresh_tokens_is_public_and_rotates() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = _form(request)
        assert body["grant_type"] == "refresh_token"
        assert body["client_id"] == "cid"
        assert body["refresh_token"] == "OLD"
        assert body["organization_id"] == "org1"
        assert "client_secret" not in body
        return httpx.Response(200, json={"access_token": "AT2", "refresh_token": "NEW", "organization_id": "org1"})

    tok = refresh_tokens(
        client_id="cid",
        refresh_token="OLD",
        organization_id="org1",
        transport=httpx.MockTransport(handler),
    )
    assert tok.access_token == "AT2"
    assert tok.refresh_token == "NEW"  # rotated


def test_login_via_device_prompts_opens_and_polls(monkeypatch: pytest.MonkeyPatch) -> None:
    dev = _device()
    monkeypatch.setattr(_workos_auth, "request_device_authorization", lambda **_kw: dev)
    monkeypatch.setattr(_workos_auth, "poll_for_tokens", lambda **_kw: Tokens("AT", "RT", "u1", "org1"))
    opened: dict[str, str] = {}
    monkeypatch.setattr(_workos_auth.webbrowser, "open", lambda url: opened.setdefault("url", url))
    prompted: dict[str, str] = {}

    tok = login_via_device(
        client_id="cid",
        open_browser=True,
        on_prompt=lambda d: prompted.setdefault("code", d.user_code),
    )
    assert tok.access_token == "AT"
    assert opened["url"] == dev.verification_uri_complete  # one-click URL
    assert prompted["code"] == "WXYZ-1234"
