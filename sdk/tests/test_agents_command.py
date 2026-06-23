"""`como agents link` / `unlink` / `ls` — broker calls mocked with respx."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from typer.testing import CliRunner

from como.cli import _app

_AGENT = {"id": "a1", "slug": "offshore", "name": "Offshore ops", "output_fields": {"count": "integer"}}
_PROFILE = {"id": "p1", "name": "Bookface"}
_BATCH = {"id": "b1", "agent_id": "a1", "status": "running", "total_runs": 3, "succeeded_runs": 1}
_RUN = {"id": "r1", "record_name": "Acme", "status": "succeeded", "cost_usd": "0.42", "reused": False}


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("COMO_API_KEY", "como_live_x")
    monkeypatch.setenv("COMO_API_BASE_URL", "http://api.test")


@respx.mock
def test_agents_link_resolves_profile_by_name(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    respx.get("http://api.test/v1/crm/agents").mock(return_value=httpx.Response(200, json=[_AGENT]))
    respx.get("http://api.test/v1/browser/profiles").mock(return_value=httpx.Response(200, json=[_PROFILE]))
    patch = respx.patch("http://api.test/v1/crm/agents/a1").mock(
        return_value=httpx.Response(200, json={**_AGENT, "browser_profile_id": "p1"})
    )

    # Link by the profile's *name* — the CLI resolves it to the id.
    result = CliRunner().invoke(_app.app, ["agents", "link", "offshore", "--profile", "Bookface"])
    assert result.exit_code == 0, result.output
    assert patch.called
    assert json.loads(patch.calls.last.request.content)["browser_profile_id"] == "p1"
    assert "Linked" in result.output


@respx.mock
def test_agents_unlink_sends_null(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    respx.get("http://api.test/v1/crm/agents").mock(return_value=httpx.Response(200, json=[_AGENT]))
    patch = respx.patch("http://api.test/v1/crm/agents/a1").mock(
        return_value=httpx.Response(200, json={**_AGENT, "browser_profile_id": None})
    )

    result = CliRunner().invoke(_app.app, ["agents", "unlink", "offshore"])
    assert result.exit_code == 0, result.output
    assert patch.called
    assert json.loads(patch.calls.last.request.content)["browser_profile_id"] is None


@respx.mock
def test_agents_link_unknown_profile_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    respx.get("http://api.test/v1/crm/agents").mock(return_value=httpx.Response(200, json=[_AGENT]))
    respx.get("http://api.test/v1/browser/profiles").mock(return_value=httpx.Response(200, json=[_PROFILE]))

    result = CliRunner().invoke(_app.app, ["agents", "link", "offshore", "--profile", "Nope"])
    assert result.exit_code == 1
    assert "No browser profile" in result.output


@respx.mock
def test_agents_ls_shows_profile_name(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    linked = {**_AGENT, "browser_profile_id": "p1"}
    respx.get("http://api.test/v1/crm/agents").mock(return_value=httpx.Response(200, json=[linked]))
    respx.get("http://api.test/v1/browser/profiles").mock(return_value=httpx.Response(200, json=[_PROFILE]))

    # JSON is the default; the human table (with resolved profile name) is --table.
    result = CliRunner().invoke(_app.app, ["agents", "ls", "--table"])
    assert result.exit_code == 0, result.output
    assert "PROFILE" in result.output
    assert "Bookface" in result.output

    # Default output is machine-parseable JSON (no table headers).
    as_json = CliRunner().invoke(_app.app, ["agents", "ls"])
    assert as_json.exit_code == 0
    assert json.loads(as_json.output)[0]["id"] == "a1"


@respx.mock
def test_agents_batches_lists_run_history(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    route = respx.get("http://api.test/v1/crm/agents/a1/batches").mock(return_value=httpx.Response(200, json=[_BATCH]))

    result = CliRunner().invoke(_app.app, ["agents", "batches", "a1"])
    assert result.exit_code == 0, result.output
    assert route.called
    assert json.loads(result.output)[0]["id"] == "b1"


@respx.mock
def test_agents_batch_shows_progress(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    route = respx.get("http://api.test/v1/crm/agent-batches/b1").mock(return_value=httpx.Response(200, json=_BATCH))

    result = CliRunner().invoke(_app.app, ["agents", "batch", "b1"])
    assert result.exit_code == 0, result.output
    assert route.called
    assert json.loads(result.output)["status"] == "running"


@respx.mock
def test_agents_runs_lists_per_record_runs(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    route = respx.get("http://api.test/v1/crm/agent-batches/b1/runs").mock(
        return_value=httpx.Response(200, json=[_RUN])
    )

    result = CliRunner().invoke(_app.app, ["agents", "runs", "b1"])
    assert result.exit_code == 0, result.output
    assert route.called
    assert json.loads(result.output)[0]["record_name"] == "Acme"


@respx.mock
def test_agents_active_passes_query_and_emits_batch(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    route = respx.get("http://api.test/v1/crm/agent-batches/active").mock(return_value=httpx.Response(200, json=_BATCH))

    result = CliRunner().invoke(_app.app, ["agents", "active", "--attribute", "at1", "--list", "li1"])
    assert result.exit_code == 0, result.output
    assert route.called
    # snake_case query keys — the CRM API reads attribute_id / list_id.
    assert dict(route.calls.last.request.url.params) == {"attribute_id": "at1", "list_id": "li1"}
    assert json.loads(result.output)["id"] == "b1"


@respx.mock
def test_agents_active_none_emits_null(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    respx.get("http://api.test/v1/crm/agent-batches/active").mock(return_value=httpx.Response(200, json=None))

    result = CliRunner().invoke(_app.app, ["agents", "active", "--attribute", "at1", "--list", "li1"])
    assert result.exit_code == 0, result.output
    assert "No active batch" in result.stderr  # the note goes to stderr
    assert json.loads(result.stdout) is None  # stdout stays machine-parseable null
