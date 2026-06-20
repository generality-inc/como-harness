"""``como records create`` / ``upsert`` — record-write endpoints mocked with respx."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from typer.testing import CliRunner

from como.cli import _app

_OBJECT = {"id": "11111111-1111-1111-1111-111111111111", "slug": "companies", "name": "Companies"}
_RECORD = {
    "id": "22222222-2222-2222-2222-222222222222",
    "object_id": _OBJECT["id"],
    "name": "Acme",
    "status": "active",
    "data": {"domain": "acme.com"},
    "created_via": "api",
}


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("COMO_API_KEY", "como_live_x")
    monkeypatch.setenv("COMO_BASE_URL", "http://api.test")


@respx.mock
def test_records_create_resolves_object_slug(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    respx.get("http://api.test/v1/crm/objects").mock(return_value=httpx.Response(200, json=[_OBJECT]))
    post = respx.post("http://api.test/v1/crm/records").mock(return_value=httpx.Response(200, json=_RECORD))

    result = CliRunner().invoke(
        _app.app,
        ["crm", "records", "create", "--object", "companies", "--name", "Acme", "--data", '{"domain": "acme.com"}'],
    )
    assert result.exit_code == 0, result.output
    assert post.called
    body = json.loads(post.calls.last.request.content)
    assert body["object_id"] == _OBJECT["id"]
    assert body["name"] == "Acme"
    assert body["data"] == {"domain": "acme.com"}
    # The created record is emitted as JSON.
    assert json.loads(result.output)["id"] == _RECORD["id"]


@respx.mock
def test_records_create_with_list(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    lst = {"id": "33333333-3333-3333-3333-333333333333", "slug": "targets", "name": "Targets"}
    respx.get("http://api.test/v1/crm/objects").mock(return_value=httpx.Response(200, json=[_OBJECT]))
    respx.get("http://api.test/v1/crm/lists").mock(return_value=httpx.Response(200, json=[lst]))
    post = respx.post("http://api.test/v1/crm/records").mock(return_value=httpx.Response(200, json=_RECORD))

    result = CliRunner().invoke(
        _app.app,
        ["crm", "records", "create", "--object", "companies", "--list", "Targets"],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(post.calls.last.request.content)["list_id"] == lst["id"]


@respx.mock
def test_records_upsert_parses_match(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    respx.get("http://api.test/v1/crm/objects").mock(return_value=httpx.Response(200, json=[_OBJECT]))
    resp = {"record": _RECORD, "created": True, "changed_fields": ["domain"]}
    post = respx.post("http://api.test/v1/crm/records/upsert").mock(return_value=httpx.Response(200, json=resp))

    result = CliRunner().invoke(
        _app.app,
        ["crm", "records", "upsert", "--object", "companies", "--match", "domain=acme.com", "--name", "Acme"],
    )
    assert result.exit_code == 0, result.output
    assert post.called
    body = json.loads(post.calls.last.request.content)
    assert body["object_id"] == _OBJECT["id"]
    assert body["identity_slug"] == "domain"
    assert body["identity_value"] == "acme.com"
    out = json.loads(result.output)
    assert out["created"] is True
    assert out["changed_fields"] == ["domain"]


@respx.mock
def test_records_create_object_by_id_skips_lookup(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    objects = respx.get("http://api.test/v1/crm/objects").mock(return_value=httpx.Response(200, json=[_OBJECT]))
    post = respx.post("http://api.test/v1/crm/records").mock(return_value=httpx.Response(200, json=_RECORD))

    result = CliRunner().invoke(_app.app, ["crm", "records", "create", "--object", _OBJECT["id"]])
    assert result.exit_code == 0, result.output
    # A bare id resolves without hitting GET /objects.
    assert not objects.called
    assert json.loads(post.calls.last.request.content)["object_id"] == _OBJECT["id"]


@respx.mock
def test_records_create_unknown_object_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    respx.get("http://api.test/v1/crm/objects").mock(return_value=httpx.Response(200, json=[_OBJECT]))

    result = CliRunner().invoke(_app.app, ["crm", "records", "create", "--object", "nope"])
    assert result.exit_code == 1
    assert "No object matching" in result.output


def test_records_create_bad_data_json(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    result = CliRunner().invoke(
        _app.app,
        ["crm", "records", "create", "--object", _OBJECT["id"], "--data", "{not json}"],
    )
    assert result.exit_code == 1
    assert "not valid JSON" in result.output


def test_records_upsert_bad_match(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    result = CliRunner().invoke(
        _app.app,
        ["crm", "records", "upsert", "--object", _OBJECT["id"], "--match", "domain"],
    )
    assert result.exit_code == 1
    assert "--match must be" in result.output


@respx.mock
def test_records_get(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    route = respx.get(f"http://api.test/v1/crm/records/{_RECORD['id']}").mock(
        return_value=httpx.Response(200, json=_RECORD)
    )
    result = CliRunner().invoke(_app.app, ["crm", "records", "get", _RECORD["id"]])
    assert result.exit_code == 0, result.output
    assert route.called
    assert json.loads(result.output)["id"] == _RECORD["id"]


@respx.mock
def test_records_list_resolves_object_slug(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    respx.get("http://api.test/v1/crm/objects").mock(return_value=httpx.Response(200, json=[_OBJECT]))
    route = respx.get("http://api.test/v1/crm/records").mock(return_value=httpx.Response(200, json=[_RECORD]))

    result = CliRunner().invoke(_app.app, ["crm", "records", "list", "--object", "companies", "--limit", "10"])
    assert result.exit_code == 0, result.output
    assert route.called
    params = route.calls.last.request.url.params
    assert params["object_id"] == _OBJECT["id"]
    assert params["limit"] == "10"
    assert params["offset"] == "0"
    assert json.loads(result.output)[0]["id"] == _RECORD["id"]


@respx.mock
def test_records_search(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    respx.get("http://api.test/v1/crm/objects").mock(return_value=httpx.Response(200, json=[_OBJECT]))
    hit = {"id": _RECORD["id"], "object_id": _OBJECT["id"], "name": "Acme", "status": "active"}
    post = respx.post("http://api.test/v1/crm/records/search").mock(return_value=httpx.Response(200, json=[hit]))

    result = CliRunner().invoke(_app.app, ["crm", "records", "search", "acme", "--object", "companies", "--limit", "5"])
    assert result.exit_code == 0, result.output
    body = json.loads(post.calls.last.request.content)
    assert body == {"q": "acme", "limit": 5, "object_id": _OBJECT["id"]}
    assert json.loads(result.output)[0]["id"] == _RECORD["id"]


@respx.mock
def test_records_update_sends_only_provided_fields(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    patch = respx.patch(f"http://api.test/v1/crm/records/{_RECORD['id']}").mock(
        return_value=httpx.Response(200, json=_RECORD)
    )

    result = CliRunner().invoke(
        _app.app,
        ["crm", "records", "update", _RECORD["id"], "--name", "Acme Inc", "--status", "active"],
    )
    assert result.exit_code == 0, result.output
    body = json.loads(patch.calls.last.request.content)
    # Only the fields passed are in the body — no data/owner/unset_owner keys.
    assert body == {"name": "Acme Inc", "status": "active"}


def test_records_update_nothing_to_change(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    result = CliRunner().invoke(_app.app, ["crm", "records", "update", _RECORD["id"]])
    assert result.exit_code == 1
    assert "Nothing to update" in result.output


@respx.mock
def test_records_rm_single_uses_delete(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    route = respx.delete(f"http://api.test/v1/crm/records/{_RECORD['id']}").mock(return_value=httpx.Response(204))

    result = CliRunner().invoke(_app.app, ["crm", "records", "rm", _RECORD["id"]])
    assert result.exit_code == 0, result.output
    assert route.called
    assert json.loads(result.output)["deleted_count"] == 1


@respx.mock
def test_records_rm_multiple_uses_bulk(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    ids = [_RECORD["id"], "44444444-4444-4444-4444-444444444444"]
    post = respx.post("http://api.test/v1/crm/records/bulk-delete").mock(
        return_value=httpx.Response(200, json={"deleted_count": 2})
    )

    result = CliRunner().invoke(_app.app, ["crm", "records", "rm", ",".join(ids)])
    assert result.exit_code == 0, result.output
    assert json.loads(post.calls.last.request.content) == {"record_ids": ids}
    assert json.loads(result.output)["deleted_count"] == 2


@respx.mock
def test_records_restore(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    route = respx.post(f"http://api.test/v1/crm/records/{_RECORD['id']}/restore").mock(
        return_value=httpx.Response(200, json=_RECORD)
    )
    result = CliRunner().invoke(_app.app, ["crm", "records", "restore", _RECORD["id"]])
    assert result.exit_code == 0, result.output
    assert route.called
    assert json.loads(result.output)["id"] == _RECORD["id"]


@respx.mock
def test_records_link_resolves_attribute_then_puts(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    attr = {"id": "55555555-5555-5555-5555-555555555555", "slug": "employees", "object_id": _OBJECT["id"]}
    target = "66666666-6666-6666-6666-666666666666"
    get_rec = respx.get(f"http://api.test/v1/crm/records/{_RECORD['id']}").mock(
        return_value=httpx.Response(200, json=_RECORD)
    )
    get_attrs = respx.get("http://api.test/v1/crm/attributes").mock(return_value=httpx.Response(200, json=[attr]))
    put = respx.put(f"http://api.test/v1/crm/records/{_RECORD['id']}/references").mock(
        return_value=httpx.Response(204)
    )

    result = CliRunner().invoke(
        _app.app,
        ["crm", "records", "link", _RECORD["id"], "--attribute", "employees", "--to", target],
    )
    assert result.exit_code == 0, result.output
    assert get_rec.called  # GET the source record to learn its object_id
    assert get_attrs.calls.last.request.url.params["object_id"] == _OBJECT["id"]
    body = json.loads(put.calls.last.request.content)
    assert body == {"attribute_id": attr["id"], "target_record_ids": [target]}


@respx.mock
def test_records_merge(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    victim = "77777777-7777-7777-7777-777777777777"
    post = respx.post(f"http://api.test/v1/crm/records/{_RECORD['id']}/merge").mock(
        return_value=httpx.Response(200, json=_RECORD)
    )
    result = CliRunner().invoke(_app.app, ["crm", "records", "merge", _RECORD["id"], "--victim", victim])
    assert result.exit_code == 0, result.output
    assert json.loads(post.calls.last.request.content) == {"victim_id": victim}
    assert json.loads(result.output)["id"] == _RECORD["id"]


@respx.mock
def test_records_lists(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    _env(monkeypatch, tmp_path)
    membership = {
        "list_id": "88888888-8888-8888-8888-888888888888",
        "list_name": "Targets",
        "list_emoji": None,
        "parent_object_id": _OBJECT["id"],
        "entry_data": {},
        "added_at": "2026-01-01T00:00:00Z",
    }
    route = respx.get(f"http://api.test/v1/crm/records/{_RECORD['id']}/lists").mock(
        return_value=httpx.Response(200, json=[membership])
    )
    result = CliRunner().invoke(_app.app, ["crm", "records", "lists", _RECORD["id"]])
    assert result.exit_code == 0, result.output
    assert route.called
    assert json.loads(result.output)[0]["list_name"] == "Targets"
