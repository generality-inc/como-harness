"""`como run -- <cmd>` injects the gateway SDK env into the child process and
exits with its status. The broker call + the actual exec are mocked."""

from __future__ import annotations

import httpx
import pytest
import respx
from typer.testing import CliRunner

from como.cli import _app
from como.cli import run as run_cli


@respx.mock
def test_run_injects_gateway_env_into_child(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("COMO_API_KEY", "como_live_abc")
    monkeypatch.setenv("COMO_API_BASE_URL", "http://api.test")

    respx.post("http://api.test/v1/llm-gateway/key").mock(
        return_value=httpx.Response(
            200,
            json={
                "api_key": "sk-virtual",
                "base_url": "https://llm.test",
                "models": ["claude-haiku-4-5"],
                "expires": None,
            },
        )
    )

    captured: dict[str, object] = {}

    class _Proc:
        returncode = 0

    def fake_run(cmd: list[str], env: dict[str, str]) -> _Proc:  # type: ignore[override]
        captured["cmd"] = cmd
        captured["env"] = env
        return _Proc()

    monkeypatch.setattr(run_cli.subprocess, "run", fake_run)

    result = CliRunner().invoke(_app.app, ["run", "--", "python", "score.py"])
    assert result.exit_code == 0, result.output
    assert captured["cmd"] == ["python", "score.py"]
    env = captured["env"]
    assert env["ANTHROPIC_BASE_URL"] == "https://llm.test"
    assert env["ANTHROPIC_API_KEY"] == "sk-virtual"
    assert env["ANTHROPIC_AUTH_TOKEN"] == "sk-virtual"
    assert env["OPENAI_BASE_URL"] == "https://llm.test/v1"
    assert env["OPENAI_API_KEY"] == "sk-virtual"
