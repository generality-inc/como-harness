"""SDK-level tests for the platform resources (browser / agents / gateway /
account) — the same FMODE-692 principle as CRM: usable from code via the SDK
client, not only through the CLI. respx-mocked, no network."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from como import AsyncComo, Como

BASE = "https://api.test.local"


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("COMO_API_KEY", "test-key")
    monkeypatch.setenv("COMO_API_BASE_URL", BASE)


def test_client_exposes_platform_resources():
    with Como() as c:
        for name in ("account", "agents", "browser", "gateway", "views"):
            assert hasattr(c, name)


# ---------- browser ----------


@respx.mock
def test_browser_create_session_and_stop():
    respx.post(f"{BASE}/v1/browser").mock(
        return_value=httpx.Response(200, json={"id": "bu_1", "cdp_url": "wss://cdp", "live_url": "https://live"})
    )
    stop = respx.delete(f"{BASE}/v1/browser/bu_1").mock(return_value=httpx.Response(204))
    with Como() as c:
        session = c.browser.create_session()
        assert c.browser.stop_session("bu_1") is None
    assert session.id == "bu_1"
    assert session.cdp_url == "wss://cdp"
    assert stop.called


@respx.mock
def test_browser_profiles_and_login():
    profile = {"id": "p1", "name": "Bookface", "status": "new", "cookie_domains": ["x.com"]}
    respx.get(f"{BASE}/v1/browser/profiles").mock(return_value=httpx.Response(200, json=[profile]))
    login = respx.post(f"{BASE}/v1/browser/profile/p1/login").mock(
        return_value=httpx.Response(200, json={"browser_id": "b1", "cdp_url": "https://cdp", "live_url": "https://l"})
    )
    with Como() as c:
        profiles = c.browser.profiles()
        session = c.browser.start_login("p1", login_url="https://site")
    assert profiles[0].name == "Bookface"
    assert profiles[0].cookie_domains == ["x.com"]
    assert session.browser_id == "b1"
    assert json.loads(login.calls.last.request.content) == {"login_url": "https://site"}


# ---------- agents ----------


@respx.mock
def test_agents_list_create_link_run():
    agent = {"id": "a1", "slug": "offshore", "name": "Offshore", "output_fields": {"count": "integer"}}
    respx.get(f"{BASE}/v1/crm/agents").mock(return_value=httpx.Response(200, json=[agent]))
    create = respx.post(f"{BASE}/v1/crm/agents").mock(return_value=httpx.Response(200, json=agent))
    patch = respx.patch(f"{BASE}/v1/crm/agents/a1").mock(
        return_value=httpx.Response(200, json={**agent, "browser_profile_id": None})
    )
    batch = respx.post(f"{BASE}/v1/crm/agent-batches").mock(
        return_value=httpx.Response(200, json={"id": "batch1", "total_runs": 12})
    )
    with Como() as c:
        assert c.agents.list()[0].slug == "offshore"
        c.agents.create({"name": "Offshore"})
        c.agents.set_browser_profile("a1", profile_id=None)
        result = c.agents.run_batch(attribute_id="col1", list_id="list1")
    assert json.loads(create.calls.last.request.content) == {"name": "Offshore"}
    # unlink sends an explicit null, not an omitted key.
    assert json.loads(patch.calls.last.request.content) == {"browser_profile_id": None}
    assert result.id == "batch1" and result.total_runs == 12
    assert json.loads(batch.calls.last.request.content) == {"attribute_id": "col1", "list_id": "list1"}


# ---------- gateway ----------


@respx.mock
def test_gateway_create_key():
    respx.post(f"{BASE}/v1/llm-gateway/key").mock(
        return_value=httpx.Response(200, json={"api_key": "sk-v", "base_url": "https://llm", "models": ["m"]})
    )
    with Como() as c:
        key = c.gateway.create_key()
    assert key.api_key == "sk-v"
    assert key.base_url == "https://llm"


# ---------- account ----------


@respx.mock
def test_account_me_and_keys():
    respx.get(f"{BASE}/v1/me").mock(
        return_value=httpx.Response(200, json={"user": {"email": "a@b.co"}, "workspace": {"slug": "ws"}})
    )
    respx.get(f"{BASE}/v1/cli/keys").mock(
        return_value=httpx.Response(200, json=[{"id": "k1", "prefix": "como_live_ab"}])
    )
    delete = respx.delete(f"{BASE}/v1/cli/keys/k1").mock(return_value=httpx.Response(204))
    with Como() as c:
        me = c.account.me()
        keys = c.account.list_keys()
        c.account.delete_key("k1")
    assert me.user.get("email") == "a@b.co"
    assert me.workspace.get("slug") == "ws"
    assert keys[0].prefix == "como_live_ab"
    assert delete.called


# ---------- views ----------


@respx.mock
def test_views_create_columns_sorts_filter_and_operators():
    view = {
        "id": "v1",
        "workspace_id": "w1",
        "object_id": "o1",
        "list_id": "l1",
        "slug": "hot",
        "name": "Hot",
        "view_type": "table",
        "is_system": False,
        "is_default": False,
        "columns": [],
        "sorts": [],
    }
    create = respx.post(f"{BASE}/v1/crm/views").mock(return_value=httpx.Response(201, json=view))
    by_list = respx.get(f"{BASE}/v1/crm/views").mock(return_value=httpx.Response(200, json=[view]))
    cols = respx.put(f"{BASE}/v1/crm/views/v1/columns").mock(return_value=httpx.Response(200, json=view))
    sorts = respx.put(f"{BASE}/v1/crm/views/v1/sorts").mock(
        return_value=httpx.Response(200, json={**view, "sorts": [{"attribute_id": "a1", "direction": "asc"}]})
    )
    filt = respx.put(f"{BASE}/v1/crm/views/v1/filter").mock(return_value=httpx.Response(200, json=view))
    respx.get(f"{BASE}/v1/crm/views/operators").mock(return_value=httpx.Response(200, json={"text": ["is"]}))

    with Como() as c:
        created = c.views.create(list_id="l1", name="Hot", view_type="table")
        listed = c.views.list_for_list("l1")
        c.views.set_columns("v1", columns=[{"attribute_id": "a1"}])
        sorted_view = c.views.set_sorts("v1", sorts=[{"attribute_id": "a1", "direction": "asc"}])
        c.views.set_filter("v1", filter=None)
        ops = c.views.operators()

    assert created.id == "v1" and created.list_id == "l1"
    assert listed[0].name == "Hot"
    assert json.loads(create.calls.last.request.content) == {"name": "Hot", "view_type": "table", "list_id": "l1"}
    assert json.loads(cols.calls.last.request.content) == {"columns": [{"attribute_id": "a1"}]}
    assert json.loads(sorts.calls.last.request.content) == {"sorts": [{"attribute_id": "a1", "direction": "asc"}]}
    assert sorted_view.sorts[0].direction == "asc"
    assert json.loads(filt.calls.last.request.content) == {"filter": None}
    assert ops == {"text": ["is"]}
    assert by_list.calls.last.request.url.params["list_id"] == "l1"


@pytest.mark.asyncio
@respx.mock
async def test_async_agents_list():
    respx.get(f"{BASE}/v1/crm/agents").mock(
        return_value=httpx.Response(200, json=[{"id": "a1", "name": "X", "slug": "x"}])
    )
    async with AsyncComo() as c:
        agents = await c.agents.list()
    assert agents[0].id == "a1"
