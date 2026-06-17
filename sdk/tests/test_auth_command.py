"""`como auth login` device-code flow: starts the flow, polls, and persists the
minted key. The two anonymous como endpoints are mocked with respx; the user's
browser approval (which happens on the web app) is simulated by the poll
returning ``approved``.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from typer.testing import CliRunner

from como import _config
from como.cli import auth as auth_cli


@respx.mock
def test_login_persists_minted_key(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))  # isolate credentials.json
    monkeypatch.delenv("COMO_API_KEY", raising=False)
    monkeypatch.setattr(auth_cli.time, "sleep", lambda _s: None)  # don't actually wait

    base = "http://api.test"
    monkeypatch.setenv("COMO_BASE_URL", base)  # backend is injected via env, not a flag
    respx.post(f"{base}/v1/cli/device-code").mock(
        return_value=httpx.Response(
            200,
            json={
                "device_code": "DEVCODE",
                "user_code": "ABCD-2345",
                "verification_url": f"{base}/cli",
                "verification_url_complete": f"{base}/cli/ABCD-2345",
                "expires_in": 600,
                "interval": 2,
            },
        )
    )
    # First poll still pending (user hasn't approved), then approved with the key.
    poll_route = respx.post(f"{base}/v1/cli/poll")
    poll_route.side_effect = [
        httpx.Response(200, json={"status": "pending"}),
        httpx.Response(
            200,
            json={
                "status": "approved",
                "key": "como_live_secretkey",
                "workspace_id": "11111111-1111-1111-1111-111111111111",
                "user_id": "22222222-2222-2222-2222-222222222222",
            },
        ),
    ]

    result = CliRunner().invoke(auth_cli.app, ["login", "--no-browser"])
    assert result.exit_code == 0, result.output
    assert "ABCD-2345" in result.output  # the one-time code is shown to the user

    creds = _config.load_credentials()
    assert creds is not None
    assert creds["api_key"] == "como_live_secretkey"
    assert "base_url" not in creds  # base URL is env-injected / prod-default, never persisted
    assert creds["workspace_id"] == "11111111-1111-1111-1111-111111111111"
    # The transport resolves this key for subsequent calls.
    assert _config.resolve_api_key(None) == "como_live_secretkey"
