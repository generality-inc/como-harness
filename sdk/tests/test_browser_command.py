"""`como browser create` / `stop` — broker calls mocked with respx."""

from __future__ import annotations

import httpx
import pytest
import respx
from typer.testing import CliRunner

from como.cli import _app


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("COMO_API_KEY", "como_live_x")
    monkeypatch.setenv("COMO_API_BASE_URL", "http://api.test")


@respx.mock
def test_browser_create_prints_session(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    respx.post("http://api.test/v1/browser").mock(
        return_value=httpx.Response(200, json={"id": "bu_1", "cdp_url": "wss://cdp/ws", "live_url": "https://live"})
    )
    result = CliRunner().invoke(_app.app, ["browser", "create"])
    assert result.exit_code == 0, result.output
    assert "bu_1" in result.output
    assert "wss://cdp/ws" in result.output


@respx.mock
def test_browser_stop(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    route = respx.delete("http://api.test/v1/browser/bu_1").mock(return_value=httpx.Response(204))
    result = CliRunner().invoke(_app.app, ["browser", "stop", "bu_1"])
    assert result.exit_code == 0, result.output
    assert route.called
