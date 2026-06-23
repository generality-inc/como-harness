from __future__ import annotations

import httpx
import pytest
import respx
from como_core import Cost
from como_core.profile import Profile

from como import AsyncComo, Como, ComoAuthError, ComoBadRequestError


@pytest.mark.parametrize(
    "raw, expected",
    [
        (["Python", "Leadership"], ["Python", "Leadership"]),  # current upstream shape
        ([], None),  # the exact body that caused the Jun 2026 profile-get outage
        ([" ML ", None, "", "ABM"], ["ML", "ABM"]),  # blanks/None pruned, trimmed
        ("Demand Generation", ["Demand Generation"]),  # legacy scalar string is coerced
        ("   ", None),
        (None, None),
        ({"unexpected": "shape"}, None),  # any other shape is dropped, never raises
    ],
)
def test_profile_top_skills_accepts_any_upstream_shape(raw, expected):
    # topSkills drifted str -> list upstream; the model must coerce every shape to
    # list[str] | None and NEVER raise (a raise becomes a 502 for the whole profile).
    assert Profile.model_validate({"id": "abc", "topSkills": raw}).top_skills == expected


def test_profile_omitted_top_skills_is_none():
    assert Profile.model_validate({"id": "abc"}).top_skills is None

BASE = "https://api.test.local"


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("COMO_API_KEY", "test-key")
    monkeypatch.setenv("COMO_API_BASE_URL", BASE)


@respx.mock
def test_profile_get_unwraps_element_and_maps_camel_case():
    respx.get(f"{BASE}/v1/ghost/profile").mock(
        return_value=httpx.Response(
            200,
            json={
                "element": {
                    "id": "abc",
                    "publicIdentifier": "kayla",
                    "firstName": "Kayla",
                    "lastName": "Lee",
                    "headline": "Engineer",
                    "linkedinUrl": "https://www.linkedin.com/in/kayla",
                    "connectionsCount": 500,
                    "openToWork": False,
                    "location": {
                        "linkedinText": "San Francisco",
                        "parsed": {"city": "San Francisco", "countryCode": "us"},
                    },
                    "experience": [
                        {"companyName": "Acme", "position": "Engineer", "duration": "2 yrs"},
                    ],
                },
                "status": "ok",
                "error": "",
                "query": {"publicIdentifier": "kayla"},
                "cost": {"amount": "0.060000", "currency": "USD"},
            },
        )
    )
    with Como() as c:
        profile = c.profile.get(public_identifier="kayla")
    assert profile.first_name == "Kayla"
    assert profile.public_identifier == "kayla"
    assert profile.connections_count == 500
    assert profile.location is not None and profile.location.linkedin_text == "San Francisco"
    assert profile.experience and profile.experience[0].company_name == "Acme"
    assert profile.cost == Cost(amount="0.060000", currency="USD")


@respx.mock
def test_profile_get_sends_bearer_auth_and_cleaned_params():
    route = respx.get(f"{BASE}/v1/ghost/profile").mock(
        return_value=httpx.Response(200, json={"element": {"id": "x"}, "status": "ok"})
    )
    with Como() as c:
        c.profile.get(url="https://example/in/x", find_email=True, main=False)
    assert route.called
    req = route.calls.last.request
    assert req.headers["authorization"] == "Bearer test-key"
    assert req.url.params["url"] == "https://example/in/x"
    assert req.url.params["findEmail"] == "true"
    # main was False which is still a value — should serialize, not be dropped
    assert req.url.params["main"] == "false"


def test_profile_get_requires_one_of():
    with Como() as c, pytest.raises(ValueError):
        c.profile.get()


@respx.mock
def test_profile_search_parses_pagination():
    respx.get(f"{BASE}/v1/ghost/profile-search").mock(
        return_value=httpx.Response(
            200,
            json={
                "elements": [
                    {"id": "a", "name": "Alice", "linkedinUrl": "https://x/a"},
                    {"id": "b", "name": "Bob", "linkedinUrl": "https://x/b"},
                ],
                "pagination": {
                    "totalPages": 3,
                    "totalElements": 25,
                    "pageNumber": 1,
                    "pageSize": 10,
                    "paginationToken": "tok-1",
                },
                "status": "ok",
                "cost": {"amount": "0.060000", "currency": "USD"},
            },
        )
    )
    with Como() as c:
        result = c.profile.search(search="alice")
    assert len(result.elements) == 2
    assert result.elements[0].name == "Alice"
    assert result.pagination is not None
    assert result.pagination.total_pages == 3
    assert result.pagination.pagination_token == "tok-1"
    assert result.cost.amount == "0.060000"


@respx.mock
def test_auth_error_mapping():
    respx.get(f"{BASE}/v1/ghost/profile").mock(
        return_value=httpx.Response(401, json={"error": 401, "message": "bad key"})
    )
    with Como() as c, pytest.raises(ComoAuthError) as ei:
        c.profile.get(url="https://x")
    assert ei.value.status_code == 401
    assert "bad key" in str(ei.value)


@respx.mock
def test_bad_request_error_mapping():
    respx.get(f"{BASE}/v1/ghost/profile").mock(
        return_value=httpx.Response(400, json={"error": 400, "message": "missing param"})
    )
    with Como() as c, pytest.raises(ComoBadRequestError):
        c.profile.get(url="https://x")


@respx.mock
async def test_async_profile_get():
    respx.get(f"{BASE}/v1/ghost/profile").mock(
        return_value=httpx.Response(
            200,
            json={"element": {"id": "async", "firstName": "Async"}, "status": "ok"},
        )
    )
    async with AsyncComo() as c:
        profile = await c.profile.get(profile_id="async")
    assert profile.first_name == "Async"


@respx.mock
def test_pagination_helper_iterates_all_pages():
    from como import iter_pages

    route = respx.get(f"{BASE}/v1/ghost/profile-search")

    def respond(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params.get("page", "1"))
        return httpx.Response(
            200,
            json={
                "elements": [{"id": f"p{page}-a"}, {"id": f"p{page}-b"}],
                "pagination": {
                    "totalPages": 3,
                    "pageNumber": page,
                    "paginationToken": f"tok-{page}",
                },
                "status": "ok",
            },
        )

    route.side_effect = respond
    with Como() as c:
        pages = list(iter_pages(c.profile.search, search="x"))
    assert len(pages) == 3
    assert [p.pagination.page_number for p in pages] == [1, 2, 3]
