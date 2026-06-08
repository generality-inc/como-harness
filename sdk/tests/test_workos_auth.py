"""Unit tests for the WorkOS token exchange/refresh (mocked transport)."""

from __future__ import annotations

import urllib.parse

import httpx

from como._workos_auth import AUTHENTICATE_URL, exchange_code, refresh_tokens


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
