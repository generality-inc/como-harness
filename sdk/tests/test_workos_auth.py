"""Unit tests for the WorkOS token exchange/refresh (mocked transport)."""

from __future__ import annotations

import types
import urllib.parse

import httpx
import pytest

from como import _pkce, _workos_auth
from como._workos_auth import AUTHENTICATE_URL, Tokens, exchange_code, login_via_pkce, refresh_tokens


def _form(request: httpx.Request) -> dict[str, str]:
    return dict(urllib.parse.parse_qsl(request.content.decode()))


def test_exchange_code_sends_pkce_and_parses_tokens() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == AUTHENTICATE_URL
        body = _form(request)
        assert body["grant_type"] == "authorization_code"
        assert body["client_id"] == "client_01ABC"
        assert body["code"] == "THECODE"
        assert body["code_verifier"] == "THEVERIFIER"
        assert "client_secret" not in body  # public PKCE client
        return httpx.Response(
            200,
            json={
                "access_token": "AT",
                "refresh_token": "RT",
                "user": {"id": "user_1"},
                "organization_id": "org_1",
            },
        )

    tok = exchange_code(
        client_id="client_01ABC",
        code="THECODE",
        code_verifier="THEVERIFIER",
        transport=httpx.MockTransport(handler),
    )
    assert (tok.access_token, tok.refresh_token, tok.user_id, tok.organization_id) == (
        "AT",
        "RT",
        "user_1",
        "org_1",
    )


def test_refresh_rotates_and_supports_org_switch() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = _form(request)
        assert body["grant_type"] == "refresh_token"
        assert body["refresh_token"] == "OLD_RT"
        assert body["organization_id"] == "org_2"
        return httpx.Response(200, json={"access_token": "AT2", "refresh_token": "NEW_RT"})

    tok = refresh_tokens(
        client_id="client_01ABC",
        refresh_token="OLD_RT",
        organization_id="org_2",
        transport=httpx.MockTransport(handler),
    )
    assert tok.access_token == "AT2"
    assert tok.refresh_token == "NEW_RT"  # caller must persist the rotated token


def test_login_via_pkce_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(_pkce, "generate_pkce", lambda: ("VER", "CHAL"))

    def fake_url(*, client_id: str, code_challenge: str, state: str, port: int = 0) -> str:
        captured.update(client_id=client_id, challenge=code_challenge, state=state)
        return "https://workos/authorize?x=1"

    monkeypatch.setattr(_pkce, "build_authorize_url", fake_url)
    monkeypatch.setattr(
        _workos_auth, "webbrowser", types.SimpleNamespace(open=lambda u: captured.update(opened=u))
    )
    monkeypatch.setattr(
        _pkce,
        "wait_for_callback",
        lambda *, port=0, timeout=0.0: _pkce.CallbackResult(code="CODE", state=captured["state"]),
    )

    def fake_exchange(*, client_id: str, code: str, code_verifier: str, transport=None) -> Tokens:
        captured["exchanged"] = (client_id, code, code_verifier)
        return Tokens(access_token="AT", refresh_token="RT", user_id="u1", organization_id="o1")

    monkeypatch.setattr(_workos_auth, "exchange_code", fake_exchange)

    tok = login_via_pkce(client_id="cid", open_browser=True)
    assert tok.access_token == "AT"
    assert captured["client_id"] == "cid"
    assert captured["opened"] == "https://workos/authorize?x=1"  # browser opened the authz URL
    assert captured["exchanged"] == ("cid", "CODE", "VER")  # code+verifier forwarded to exchange


def test_login_via_pkce_rejects_state_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_pkce, "generate_pkce", lambda: ("VER", "CHAL"))
    monkeypatch.setattr(_pkce, "build_authorize_url", lambda **kw: "url")
    monkeypatch.setattr(_workos_auth, "webbrowser", types.SimpleNamespace(open=lambda u: None))
    monkeypatch.setattr(
        _pkce,
        "wait_for_callback",
        lambda *, port=0, timeout=0.0: _pkce.CallbackResult(code="CODE", state="WRONG"),
    )
    monkeypatch.setattr(_workos_auth, "exchange_code", lambda **kw: Tokens("x", "y"))
    with pytest.raises(RuntimeError, match="state mismatch"):
        login_via_pkce(client_id="cid", open_browser=False)
