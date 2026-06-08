"""The SyncTransport refreshes a WorkOS access token once on 401 and retries."""

from __future__ import annotations

import httpx
import pytest

from como import _transport
from como._transport import SyncTransport
from como.errors import ComoError


def test_get_refreshes_workos_token_on_401(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, object] = {"n": 0, "auth": []}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] = int(calls["n"]) + 1  # type: ignore[arg-type]
        calls["auth"].append(request.headers.get("authorization"))  # type: ignore[attr-defined]
        if calls["n"] == 1:
            return httpx.Response(401, json={"detail": "token expired"})
        return httpx.Response(200, json={"ok": True})

    client = httpx.Client(
        base_url="http://testserver",
        transport=httpx.MockTransport(handler),
        headers={"Authorization": "Bearer OLD"},
    )
    # WorkOS session present → refresh yields a new access token.
    monkeypatch.setattr(_transport, "refresh_bearer", lambda: "NEWTOKEN")

    transport = SyncTransport(api_key="OLD", http_client=client)
    assert transport.get("/v1/ghost/profile") == {"ok": True}
    assert calls["n"] == 2  # retried once after refresh
    assert calls["auth"][1] == "Bearer NEWTOKEN"  # retry used the refreshed token


def test_get_does_not_retry_for_static_key(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(401, json={"detail": "unauthorized"})

    client = httpx.Client(
        base_url="http://testserver",
        transport=httpx.MockTransport(handler),
        headers={"Authorization": "Bearer KEY"},
    )
    # Static API key → nothing to refresh.
    monkeypatch.setattr(_transport, "refresh_bearer", lambda: None)

    transport = SyncTransport(api_key="KEY", http_client=client)
    with pytest.raises(ComoError):
        transport.get("/v1/x")
    assert calls["n"] == 1  # no retry
