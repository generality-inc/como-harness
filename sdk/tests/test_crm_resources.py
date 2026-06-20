"""SDK-level tests for the CRM resources (``client.records`` / ``client.lists``).

The point of FMODE-692: CRM must be usable from code via the SDK client, not
only through the CLI. These exercise the resource classes directly, mocked with
respx — no network, no CLI.
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from como import AsyncComo, Como

BASE = "https://api.test.local"

_OBJECT = {"id": "11111111-1111-1111-1111-111111111111", "slug": "companies", "name": "Companies"}
_RECORD = {
    "id": "22222222-2222-2222-2222-222222222222",
    "object_id": _OBJECT["id"],
    "name": "Acme",
    "status": "active",
    "data": {"domain": "acme.com"},
    "created_via": "api",
}


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("COMO_API_KEY", "test-key")
    monkeypatch.setenv("COMO_API_BASE_URL", BASE)


def test_client_exposes_crm_resources():
    with Como() as c:
        assert hasattr(c, "records")
        assert hasattr(c, "lists")
    # The whole bug: `from como import Como` must give you CRM, not just LinkedIn.


@respx.mock
def test_records_create_posts_and_parses():
    route = respx.post(f"{BASE}/v1/crm/records").mock(return_value=httpx.Response(200, json=_RECORD))
    with Como() as c:
        record = c.records.create(object_id=_OBJECT["id"], name="Acme", data={"domain": "acme.com"})
    assert record.id == _RECORD["id"]
    assert record.data == {"domain": "acme.com"}
    body = json.loads(route.calls.last.request.content)
    assert body == {"object_id": _OBJECT["id"], "name": "Acme", "data": {"domain": "acme.com"}}


@respx.mock
def test_records_upsert_returns_typed_result():
    resp = {"record": _RECORD, "created": True, "changed_fields": ["domain"]}
    respx.post(f"{BASE}/v1/crm/records/upsert").mock(return_value=httpx.Response(200, json=resp))
    with Como() as c:
        result = c.records.upsert(object_id=_OBJECT["id"], identity_slug="domain", identity_value="acme.com")
    assert result.created is True
    assert result.changed_fields == ["domain"]
    assert result.record is not None and result.record.id == _RECORD["id"]


@respx.mock
def test_records_get_and_list():
    respx.get(f"{BASE}/v1/crm/records/{_RECORD['id']}").mock(return_value=httpx.Response(200, json=_RECORD))
    list_route = respx.get(f"{BASE}/v1/crm/records").mock(return_value=httpx.Response(200, json=[_RECORD]))
    with Como() as c:
        assert c.records.get(_RECORD["id"]).name == "Acme"
        rows = c.records.list(object_id=_OBJECT["id"], limit=10, offset=5)
    assert [r.id for r in rows] == [_RECORD["id"]]
    params = list_route.calls.last.request.url.params
    assert params["object_id"] == _OBJECT["id"]
    assert params["limit"] == "10"
    assert params["offset"] == "5"


@respx.mock
def test_records_search_body():
    hit = {"id": _RECORD["id"], "object_id": _OBJECT["id"], "name": "Acme"}
    route = respx.post(f"{BASE}/v1/crm/records/search").mock(return_value=httpx.Response(200, json=[hit]))
    with Como() as c:
        rows = c.records.search(q="acme", limit=5, object_id=_OBJECT["id"])
    assert [r.id for r in rows] == [_RECORD["id"]]
    assert json.loads(route.calls.last.request.content) == {"q": "acme", "limit": 5, "object_id": _OBJECT["id"]}


@respx.mock
def test_records_update_sends_only_provided():
    route = respx.patch(f"{BASE}/v1/crm/records/{_RECORD['id']}").mock(return_value=httpx.Response(200, json=_RECORD))
    with Como() as c:
        c.records.update(_RECORD["id"], name="Acme Inc", status="active")
    assert json.loads(route.calls.last.request.content) == {"name": "Acme Inc", "status": "active"}


@respx.mock
def test_records_delete_and_bulk_delete():
    single = respx.delete(f"{BASE}/v1/crm/records/{_RECORD['id']}").mock(return_value=httpx.Response(204))
    bulk = respx.post(f"{BASE}/v1/crm/records/bulk-delete").mock(
        return_value=httpx.Response(200, json={"deleted_count": 2})
    )
    ids = [_RECORD["id"], "44444444-4444-4444-4444-444444444444"]
    with Como() as c:
        assert c.records.delete(_RECORD["id"]) is None
        result = c.records.bulk_delete(ids)
    assert single.called
    assert result.deleted_count == 2
    assert json.loads(bulk.calls.last.request.content) == {"record_ids": ids}


@respx.mock
def test_records_set_references_puts():
    route = respx.put(f"{BASE}/v1/crm/records/{_RECORD['id']}/references").mock(return_value=httpx.Response(204))
    with Como() as c:
        c.records.set_references(_RECORD["id"], attribute_id="aaa", target_record_ids=["t1", "t2"])
    assert json.loads(route.calls.last.request.content) == {
        "attribute_id": "aaa",
        "target_record_ids": ["t1", "t2"],
    }


@respx.mock
def test_catalog_reads_via_dedicated_resources():
    # Objects/attributes live on their own resources (not bolted onto records).
    attr = {"id": "55555555-5555-5555-5555-555555555555", "slug": "employees", "object_id": _OBJECT["id"]}
    respx.get(f"{BASE}/v1/crm/objects").mock(return_value=httpx.Response(200, json=[_OBJECT]))
    attrs_route = respx.get(f"{BASE}/v1/crm/attributes").mock(return_value=httpx.Response(200, json=[attr]))
    with Como() as c:
        objs = c.objects.list()
        attributes = c.attributes.list(object_id=_OBJECT["id"])
    assert objs[0].slug == "companies"
    assert attributes[0].slug == "employees"
    assert attrs_route.calls.last.request.url.params["object_id"] == _OBJECT["id"]


@respx.mock
def test_lists_list_create_and_add():
    lst = {"id": "33333333-3333-3333-3333-333333333333", "slug": "targets", "name": "Targets"}
    respx.get(f"{BASE}/v1/crm/lists").mock(return_value=httpx.Response(200, json=[lst]))
    create = respx.post(f"{BASE}/v1/crm/lists").mock(return_value=httpx.Response(200, json=lst))
    add = respx.post(f"{BASE}/v1/crm/lists/{lst['id']}/entries").mock(return_value=httpx.Response(200, json={}))
    bulk = respx.post(f"{BASE}/v1/crm/lists/{lst['id']}/entries/bulk").mock(
        return_value=httpx.Response(200, json={"added_count": 3})
    )
    with Como() as c:
        assert c.lists.list()[0].name == "Targets"
        c.lists.create(parent_object_id=_OBJECT["id"], name="Targets")
        c.lists.add_entry(lst["id"], record_id="r1")
        result = c.lists.add_entries(lst["id"], record_ids=["r1", "r2", "r3"])
    assert json.loads(create.calls.last.request.content) == {"parent_object_id": _OBJECT["id"], "name": "Targets"}
    assert json.loads(add.calls.last.request.content) == {"record_id": "r1"}
    assert result.added_count == 3
    assert json.loads(bulk.calls.last.request.content) == {"record_ids": ["r1", "r2", "r3"]}


@pytest.mark.asyncio
@respx.mock
async def test_async_records_create():
    respx.post(f"{BASE}/v1/crm/records").mock(return_value=httpx.Response(200, json=_RECORD))
    async with AsyncComo() as c:
        record = await c.records.create(object_id=_OBJECT["id"], name="Acme")
    assert record.id == _RECORD["id"]
