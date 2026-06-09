"""`como auth login` command glue: discovers client id, runs the PKCE flow,
persists the WorkOS session (flow + browser mocked; creds isolated to tmp)."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from como import _config
from como._workos_auth import Tokens
from como.cli import auth as auth_cli


def test_login_command_persists_workos_session(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))  # isolate credentials.json
    monkeypatch.delenv("COMO_API_KEY", raising=False)
    monkeypatch.setattr(auth_cli, "_fetch_workos_client_id", lambda base: "client_X")

    captured: dict[str, object] = {}

    def fake_login(*, client_id: str, open_browser: bool, on_prompt: object = None) -> Tokens:
        captured["client_id"] = client_id
        captured["open_browser"] = open_browser
        return Tokens(access_token="AT", refresh_token="RT", user_id="u1", organization_id="org1")

    monkeypatch.setattr(auth_cli, "login_via_device", fake_login)

    result = CliRunner().invoke(auth_cli.app, ["login", "--base-url", "http://api.test", "--no-browser"])
    assert result.exit_code == 0, result.output
    assert captured == {"client_id": "client_X", "open_browser": False}

    creds = _config.load_credentials()
    assert creds is not None
    assert creds["workos_access_token"] == "AT"
    assert creds["workos_refresh_token"] == "RT"
    assert creds["workos_client_id"] == "client_X"
    assert creds["base_url"] == "http://api.test"
    # The transport's bearer resolves to the WorkOS access token now.
    assert _config.resolve_bearer(None) == "AT"
