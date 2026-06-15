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


_PROFILES = [{"id": "p1", "name": "Bookface", "status": "new"}]


@respx.mock
def test_profile_login_open_is_non_blocking(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    """`--open` resolves the profile, opens the browser, prints the session JSON
    (incl. expires_at), and exits — it must NOT block on input or call complete."""
    _env(monkeypatch, tmp_path)
    respx.get("http://api.test/v1/browser/profiles").mock(return_value=httpx.Response(200, json=_PROFILES))
    opened = respx.post("http://api.test/v1/browser/profile/p1/login").mock(
        return_value=httpx.Response(
            200, json={"browser_id": "b1", "live_url": "https://live/1", "expires_at": "2026-06-15T05:00:00+00:00"}
        )
    )
    completed = respx.post("http://api.test/v1/browser/profile/p1/login/complete")

    result = CliRunner().invoke(_app.app, ["browser", "profile", "login", "Bookface", "--open"])

    assert result.exit_code == 0, result.output
    assert opened.called
    assert not completed.called  # --open never finalizes
    assert "https://live/1" in result.output
    assert "expires_at" in result.output


@respx.mock
def test_profile_login_finish_completes(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    respx.get("http://api.test/v1/browser/profiles").mock(return_value=httpx.Response(200, json=_PROFILES))
    opened = respx.post("http://api.test/v1/browser/profile/p1/login")
    completed = respx.post("http://api.test/v1/browser/profile/p1/login/complete").mock(
        return_value=httpx.Response(200, json={"id": "p1", "name": "Bookface", "status": "ready"})
    )

    result = CliRunner().invoke(_app.app, ["browser", "profile", "login", "Bookface", "--finish"])

    assert result.exit_code == 0, result.output
    assert completed.called
    assert not opened.called  # --finish never opens a new browser
    assert "Saved" in result.output


@respx.mock
def test_profile_login_open_and_finish_are_exclusive(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    result = CliRunner().invoke(_app.app, ["browser", "profile", "login", "Bookface", "--open", "--finish"])
    assert result.exit_code == 1
    assert "not both" in result.output


@respx.mock
def test_profile_cancel(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    respx.get("http://api.test/v1/browser/profiles").mock(return_value=httpx.Response(200, json=_PROFILES))
    cancelled = respx.post("http://api.test/v1/browser/profile/p1/login/cancel").mock(
        return_value=httpx.Response(200, json={"id": "p1", "name": "Bookface", "status": "new"})
    )

    result = CliRunner().invoke(_app.app, ["browser", "profile", "cancel", "Bookface"])

    assert result.exit_code == 0, result.output
    assert cancelled.called
    assert "Cancelled" in result.output
