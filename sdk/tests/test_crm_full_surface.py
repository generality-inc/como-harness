"""SDK + CLI coverage for the full records/lists/objects/attributes surface
added so Claude Code can drive the CRM. respx-mocked, no network."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from typer.testing import CliRunner

from como import Como
from como.cli import _app

BASE = "https://api.test.local"
_OBJ = {"id": "o1", "slug": "companies", "singular_name": "Company", "plural_name": "Companies"}
_LIST = {"id": "l1", "slug": "pipe", "name": "Pipe", "parent_object_id": "o1"}


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("COMO_API_KEY", "test-key")
    monkeypatch.setenv("COMO_API_BASE_URL", BASE)


# ---------------- SDK: records additions ----------------


@respx.mock
def test_records_related_and_duplicates():
    respx.get(f"{BASE}/v1/crm/records/r1/related").mock(
        return_value=httpx.Response(200, json=[{"record_id": "r2", "attribute_id": "a1", "direction": "forward"}])
    )
    dup = respx.post(f"{BASE}/v1/crm/records/duplicates").mock(
        return_value=httpx.Response(200, json=[{"id": "r9", "name": "Acme", "data": {"domain": "acme.com"}}])
    )
    with Como() as c:
        edges = c.records.related("r1")
        hits = c.records.duplicates(object_id="o1", name="Acme", data={"domain": "acme.com"})
    assert edges[0].direction == "forward"
    assert hits[0].id == "r9"
    assert json.loads(dup.calls.last.request.content) == {
        "object_id": "o1",
        "name": "Acme",
        "data": {"domain": "acme.com"},
    }


@respx.mock
def test_records_list_passes_view_id():
    route = respx.get(f"{BASE}/v1/crm/records").mock(return_value=httpx.Response(200, json=[]))
    with Como() as c:
        c.records.list(object_id="o1", view_id="v1", limit=10)
    params = route.calls.last.request.url.params
    assert params["object_id"] == "o1" and params["view_id"] == "v1" and params["limit"] == "10"


# ---------------- SDK: lists full lifecycle ----------------


@respx.mock
def test_lists_update_remove_entry_data_and_attrs():
    respx.patch(f"{BASE}/v1/crm/lists/l1").mock(return_value=httpx.Response(200, json={**_LIST, "name": "Hot"}))
    single_del = respx.delete(f"{BASE}/v1/crm/lists/l1/entries/r1").mock(return_value=httpx.Response(204))
    bulk_del = respx.delete(f"{BASE}/v1/crm/lists/l1/entries/bulk").mock(
        return_value=httpx.Response(200, json={"removed_count": 2})
    )
    entry = respx.patch(f"{BASE}/v1/crm/lists/l1/entries/r1").mock(
        return_value=httpx.Response(200, json={"id": "e1", "record_id": "r1", "data": {"stage": "warm"}})
    )
    attr = respx.post(f"{BASE}/v1/crm/lists/l1/attributes").mock(
        return_value=httpx.Response(201, json={"id": "a1", "slug": "stage", "name": "Stage", "type": "text"})
    )
    respx.get(f"{BASE}/v1/crm/lists/l1/records").mock(
        return_value=httpx.Response(
            200, json=[{"id": "r1", "name": "Acme", "data": {"x": 1}, "list_data": {"stage": "warm"}}]
        )
    )
    with Como() as c:
        assert c.lists.update("l1", name="Hot").name == "Hot"
        assert c.lists.remove_entry("l1", record_id="r1") is None
        assert c.lists.remove_entries("l1", record_ids=["r1", "r2"]).removed_count == 2
        assert c.lists.update_entry_data("l1", record_id="r1", data={"stage": "warm"}).data["stage"] == "warm"
        assert c.lists.create_attribute("l1", slug="stage", name="Stage", type="text").slug == "stage"
        rowlist = c.lists.records("l1")
    assert single_del.called
    assert json.loads(bulk_del.calls.last.request.content) == {"record_ids": ["r1", "r2"]}
    assert json.loads(entry.calls.last.request.content) == {"data": {"stage": "warm"}}
    assert attr.called
    # The list_data drop is fixed: the row carries both data and list_data.
    assert rowlist[0].data == {"x": 1} and rowlist[0].list_data == {"stage": "warm"}


@respx.mock
def test_views_update_sets_default_and_renames():
    route = respx.patch(f"{BASE}/v1/crm/views/v1").mock(
        return_value=httpx.Response(200, json={"id": "v1", "name": "Hot", "is_default": True, "view_type": "table"})
    )
    with Como() as c:
        v = c.views.update("v1", name="Hot", is_default=True)
    assert v.is_default is True and v.name == "Hot"
    assert json.loads(route.calls.last.request.content) == {"name": "Hot", "is_default": True}


# ---------------- SDK: objects + attributes catalog ----------------


@respx.mock
def test_objects_and_attributes_catalog():
    respx.get(f"{BASE}/v1/crm/objects").mock(return_value=httpx.Response(200, json=[_OBJ]))
    obj_create = respx.post(f"{BASE}/v1/crm/objects").mock(return_value=httpx.Response(201, json=_OBJ))
    attr_create = respx.post(f"{BASE}/v1/crm/attributes").mock(
        return_value=httpx.Response(
            201, json={"id": "a1", "slug": "tier", "name": "Tier", "type": "select", "options": []}
        )
    )
    opt = respx.post(f"{BASE}/v1/crm/attributes/a1/options").mock(
        return_value=httpx.Response(201, json={"id": "op1", "slug": "lead", "label": "Lead"})
    )
    with Como() as c:
        assert c.objects.list()[0].slug == "companies"
        c.objects.create(slug="investors", singular_name="Investor", plural_name="Investors")
        attr = c.attributes.create(object_id="o1", slug="tier", name="Tier", type="select")
        option = c.attributes.add_option("a1", slug="lead", label="Lead")
    assert json.loads(obj_create.calls.last.request.content)["slug"] == "investors"
    assert attr.type == "select"
    assert json.loads(attr_create.calls.last.request.content) == {
        "object_id": "o1",
        "slug": "tier",
        "name": "Tier",
        "type": "select",
        "is_required": False,
        "is_unique": False,
    }
    assert option.label == "Lead" and json.loads(opt.calls.last.request.content) == {"slug": "lead", "label": "Lead"}


# ---------------- CLI: a few of the new commands (slug resolution + parsing) ----------------


def _env(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("COMO_API_KEY", "como_live_x")
    monkeypatch.setenv("COMO_API_BASE_URL", BASE)


@respx.mock
def test_cli_lists_create_resolves_object_slug(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    respx.get(f"{BASE}/v1/crm/objects").mock(return_value=httpx.Response(200, json=[_OBJ]))
    post = respx.post(f"{BASE}/v1/crm/lists").mock(return_value=httpx.Response(201, json=_LIST))
    res = CliRunner().invoke(_app.app, ["crm", "lists", "create", "Pipe", "--object", "companies"])
    assert res.exit_code == 0, res.output
    assert json.loads(post.calls.last.request.content) == {"parent_object_id": "o1", "name": "Pipe"}


@respx.mock
def test_cli_lists_entry_data_merges(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    respx.get(f"{BASE}/v1/crm/lists").mock(return_value=httpx.Response(200, json=[_LIST]))
    patch = respx.patch(f"{BASE}/v1/crm/lists/l1/entries/r1").mock(
        return_value=httpx.Response(200, json={"id": "e1", "record_id": "r1", "data": {"stage": "hot"}})
    )
    res = CliRunner().invoke(_app.app, ["crm", "lists", "entry-data", "Pipe", "r1", "--data", '{"stage": "hot"}'])
    assert res.exit_code == 0, res.output
    assert json.loads(patch.calls.last.request.content) == {"data": {"stage": "hot"}}


@respx.mock
def test_cli_delete_emits_structured_json(monkeypatch, tmp_path):
    # Uniform output contract: mutations emit parseable JSON, not prose.
    _env(monkeypatch, tmp_path)
    respx.get(f"{BASE}/v1/crm/lists").mock(return_value=httpx.Response(200, json=[_LIST]))
    respx.delete(f"{BASE}/v1/crm/lists/l1").mock(return_value=httpx.Response(204))
    res = CliRunner().invoke(_app.app, ["crm", "lists", "rm", "Pipe"])
    assert res.exit_code == 0, res.output
    assert json.loads(res.output) == {"deleted": True, "list_id": "l1"}

    respx.get(f"{BASE}/v1/crm/objects").mock(return_value=httpx.Response(200, json=[_OBJ]))
    respx.delete(f"{BASE}/v1/crm/objects/o1").mock(return_value=httpx.Response(204))
    res2 = CliRunner().invoke(_app.app, ["crm", "objects", "rm", "companies"])
    assert res2.exit_code == 0, res2.output
    assert json.loads(res2.output) == {"deleted": True, "object_id": "o1"}


@respx.mock
def test_cli_records_update_owner(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    patch = respx.patch(f"{BASE}/v1/crm/records/r1").mock(
        return_value=httpx.Response(200, json={"id": "r1", "object_id": "o1", "name": "Acme"})
    )
    res = CliRunner().invoke(_app.app, ["crm", "records", "update", "r1", "--owner", "m1"])
    assert res.exit_code == 0, res.output
    assert json.loads(patch.calls.last.request.content) == {"owner_member_id": "m1"}


@respx.mock
def test_cli_records_unlink_clears_refs(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    rec = {"id": "r1", "object_id": "o1", "name": "Acme"}
    respx.get(f"{BASE}/v1/crm/records/r1").mock(return_value=httpx.Response(200, json=rec))
    respx.get(f"{BASE}/v1/crm/attributes").mock(
        return_value=httpx.Response(200, json=[{"id": "a1", "slug": "investors", "object_id": "o1"}])
    )
    put = respx.put(f"{BASE}/v1/crm/records/r1/references").mock(return_value=httpx.Response(204))
    res = CliRunner().invoke(_app.app, ["crm", "records", "unlink", "r1", "--attribute", "investors"])
    assert res.exit_code == 0, res.output
    assert json.loads(put.calls.last.request.content) == {"attribute_id": "a1", "target_record_ids": []}
