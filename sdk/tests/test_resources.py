"""End-to-end mocked tests for every non-profile resource."""

from __future__ import annotations

import httpx
import pytest
import respx
from como_core import Cost

from como import (
    AsyncComo,
    Como,
    ComoAuthError,
    ComoNotFoundError,
    ComoRateLimitError,
    ComoServerError,
)

BASE = "https://api.test.local"

_COST = {"amount": "0.060000", "currency": "USD"}


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("COMO_API_KEY", "test-key")
    monkeypatch.setenv("COMO_API_BASE_URL", BASE)


def _envelope(element: dict) -> dict:
    return {"element": element, "status": "ok", "error": "", "query": {}, "cost": dict(_COST)}


def _list(elements: list[dict], *, page: int = 1, total: int = 1, token: str | None = None) -> dict:
    return {
        "elements": elements,
        "pagination": {
            "totalPages": total,
            "totalElements": len(elements) * total,
            "pageNumber": page,
            "pageSize": len(elements),
            "paginationToken": token,
        },
        "status": "ok",
        "cost": dict(_COST),
    }


# ---------- company ----------


@respx.mock
def test_company_get_unwraps_and_parses():
    respx.get(f"{BASE}/v1/ghost/company").mock(
        return_value=httpx.Response(
            200,
            json=_envelope(
                {
                    "id": "1337",
                    "universalName": "acme",
                    "name": "Acme",
                    "tagline": "We make things",
                    "linkedinUrl": "https://www.linkedin.com/company/acme",
                    "employeeCount": 250,
                    "followerCount": 9001,
                    "headquarter": {"city": "SF", "country": "USA"},
                }
            ),
        )
    )
    with Como() as c:
        company = c.company.get(universal_name="acme")
    assert company.name == "Acme"
    assert company.universal_name == "acme"
    assert company.employee_count == 250
    assert company.cost == Cost(amount="0.060000", currency="USD")


def test_company_get_requires_one_of():
    with Como() as c, pytest.raises(ValueError):
        c.company.get()


@respx.mock
def test_company_search_paginated():
    respx.get(f"{BASE}/v1/ghost/company-search").mock(
        return_value=httpx.Response(
            200,
            json=_list([{"id": "1", "name": "Acme"}], page=1, total=3, token="tok"),
        )
    )
    with Como() as c:
        result = c.company.search(search="acme")
    assert len(result.elements) == 1
    assert result.pagination.total_pages == 3
    assert result.cost.amount == "0.060000"


@respx.mock
def test_company_posts_routes_to_company_posts_path():
    route = respx.get(f"{BASE}/v1/ghost/company-posts").mock(
        return_value=httpx.Response(200, json=_list([{"id": "p1", "content": "hi"}]))
    )
    with Como() as c:
        result = c.company.posts(company_universal_name="acme")
    assert route.called
    assert result.elements[0].content == "hi"


# ---------- post ----------


@respx.mock
def test_post_get_requires_url_and_parses():
    respx.get(f"{BASE}/v1/ghost/post").mock(
        return_value=httpx.Response(
            200,
            json=_envelope(
                {
                    "id": "urn:li:activity:1",
                    "content": "Hello world",
                    "author": {"name": "Bill", "linkedinUrl": "https://x/in/bill"},
                    "engagement": {"likes": 100, "comments": 5},
                }
            ),
        )
    )
    with Como() as c:
        post = c.post.get(url="https://www.linkedin.com/feed/update/x")
    assert post.id == "urn:li:activity:1"
    assert post.author.name == "Bill"
    assert post.engagement.likes == 100
    assert post.cost == Cost(amount="0.060000", currency="USD")


@respx.mock
def test_post_company_posts_shares_path_with_company_posts():
    route = respx.get(f"{BASE}/v1/ghost/company-posts").mock(
        return_value=httpx.Response(200, json=_list([{"id": "p"}]))
    )
    with Como() as c:
        c.post.company_posts(company="https://x/company/acme")
    assert route.called


@respx.mock
def test_post_user_posts_shares_path_with_profile_posts():
    route = respx.get(f"{BASE}/v1/ghost/profile-posts").mock(
        return_value=httpx.Response(200, json=_list([{"id": "p"}]))
    )
    with Como() as c:
        c.post.user_posts(profile_public_identifier="bill")
    assert route.called


@respx.mock
def test_post_comments_and_reactions():
    respx.get(f"{BASE}/v1/ghost/post-comments").mock(
        return_value=httpx.Response(
            200,
            json=_list([{"id": "c1", "commentary": "nice", "actor": {"name": "Sue"}}]),
        )
    )
    respx.get(f"{BASE}/v1/ghost/post-reactions").mock(
        return_value=httpx.Response(
            200,
            json=_list([{"id": "r1", "reactionType": "LIKE", "actor": {"name": "Sue"}}]),
        )
    )
    with Como() as c:
        comments = c.post.comments(post="https://x/p/1")
        reactions = c.post.reactions(post="https://x/p/1")
    assert comments.elements[0].commentary == "nice"
    assert reactions.elements[0].reaction_type == "LIKE"


@respx.mock
def test_post_comment_replies_and_reactions():
    respx.get(f"{BASE}/v1/ghost/post-comment-replies").mock(
        return_value=httpx.Response(200, json=_list([{"id": "r1", "commentary": "reply"}]))
    )
    respx.get(f"{BASE}/v1/ghost/comment-reactions").mock(
        return_value=httpx.Response(
            200,
            json=_list([{"id": "cr1", "reactionType": "PRAISE"}]),
        )
    )
    with Como() as c:
        replies = c.post.comment_replies(comment="urn:li:comment:1")
        creactions = c.post.comment_reactions(comment="urn:li:comment:1")
    assert replies.elements[0].commentary == "reply"
    assert creactions.elements[0].reaction_type == "PRAISE"


# ---------- job ----------


@respx.mock
def test_job_get_and_search():
    respx.get(f"{BASE}/v1/ghost/job").mock(
        return_value=httpx.Response(
            200,
            json=_envelope(
                {
                    "id": "job-1",
                    "title": "Staff Eng",
                    "companyName": "Acme",
                    "workplaceType": "Remote",
                }
            ),
        )
    )
    respx.get(f"{BASE}/v1/ghost/job-search").mock(
        return_value=httpx.Response(200, json=_list([{"id": "job-1", "title": "Staff Eng"}]))
    )
    with Como() as c:
        job = c.job.get(job_id="job-1")
        results = c.job.search(search="staff eng")
    assert job.company_name == "Acme"
    assert job.cost == Cost(amount="0.060000", currency="USD")
    assert results.elements[0].title == "Staff Eng"
    assert results.cost.amount == "0.060000"


def test_job_get_requires_one_of():
    with Como() as c, pytest.raises(ValueError):
        c.job.get()


# ---------- group ----------


@respx.mock
def test_group_get_and_search():
    respx.get(f"{BASE}/v1/ghost/group").mock(
        return_value=httpx.Response(
            200,
            json=_envelope({"id": "g1", "name": "Python Devs", "memberCount": 42_000}),
        )
    )
    respx.get(f"{BASE}/v1/ghost/group-search").mock(
        return_value=httpx.Response(200, json=_list([{"id": "g1", "name": "Python Devs"}]))
    )
    with Como() as c:
        group = c.group.get(group_id="g1")
        results = c.group.search(search="python")
    assert group.name == "Python Devs"
    assert group.member_count == 42_000
    assert group.cost == Cost(amount="0.060000", currency="USD")
    assert results.elements[0].name == "Python Devs"


def test_group_get_requires_one_of():
    with Como() as c, pytest.raises(ValueError):
        c.group.get()


# ---------- ads ----------


@respx.mock
def test_ads_get_unwrapped_body():
    # Ad spec returns the ad object directly, NOT wrapped in {element: ...}.
    respx.get(f"{BASE}/v1/ghost/ad").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "ad-1",
                "variants": [{"advertiser": {"name": "Acme"}, "creativeType": "single-image"}],
                "about": {"format": "Sponsored content", "advertiserName": "Acme"},
                "cost": dict(_COST),
            },
        )
    )
    with Como() as c:
        ad = c.ads.get(ad_id="ad-1")
    assert ad.id == "ad-1"
    assert ad.variants[0].advertiser.name == "Acme"
    assert ad.about.advertiser_name == "Acme"
    assert ad.cost.amount == "0.060000"


def test_ads_get_requires_one_of():
    with Como() as c, pytest.raises(ValueError):
        c.ads.get()


@respx.mock
def test_ads_search():
    respx.get(f"{BASE}/v1/ghost/ad-search").mock(return_value=httpx.Response(200, json=_list([{"id": "ad-1"}])))
    with Como() as c:
        results = c.ads.search(keyword="cloud", countries="US,GB")
    assert len(results.elements) == 1


# ---------- service ----------


@respx.mock
def test_service_search():
    respx.get(f"{BASE}/v1/ghost/service-search").mock(
        return_value=httpx.Response(
            200,
            json=_list([{"id": "s1", "name": "Jane Designer", "linkedinUrl": "https://x"}]),
        )
    )
    with Como() as c:
        results = c.service.search(search="designer")
    assert results.elements[0].name == "Jane Designer"


# ---------- leads ----------


@respx.mock
def test_leads_search_passes_csv_filters():
    route = respx.get(f"{BASE}/v1/ghost/lead-search").mock(
        return_value=httpx.Response(200, json=_list([{"id": "l1", "firstName": "Ada"}]))
    )
    with Como() as c:
        result = c.leads.search(
            search="engineer",
            current_companies="urn:li:company:1,urn:li:company:2",
            recently_changed_jobs=True,
            geo_ids="103644278",
        )
    assert route.called
    req = route.calls.last.request
    assert req.url.params["currentCompanies"] == "urn:li:company:1,urn:li:company:2"
    assert req.url.params["recentlyChangedJobs"] == "true"
    assert req.url.params["geoIds"] == "103644278"
    assert result.elements[0].first_name == "Ada"


# ---------- geo ----------


@respx.mock
def test_geo_search_special_shape():
    # geo/search returns {id, elements: [{geoId, title}], ...} (no envelope).
    respx.get(f"{BASE}/v1/ghost/geo-id-search").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "103644278",
                "elements": [
                    {"geoId": "103644278", "title": "United States"},
                    {"geoId": "105080838", "title": "USA Metro"},
                ],
                "status": "ok",
            },
        )
    )
    with Como() as c:
        result = c.geo.search(search="united states")
    assert result.id == "103644278"
    assert result.elements[0].geo_id == "103644278"
    assert result.elements[1].title == "USA Metro"


def test_geo_search_requires_search():
    with Como() as c, pytest.raises(ValueError):
        c.geo.search(search=None)  # type: ignore[arg-type]


# ---------- error mapping (cross-cutting) ----------


@respx.mock
def test_rate_limit_maps_to_specific_error():
    respx.get(f"{BASE}/v1/ghost/profile-search").mock(
        return_value=httpx.Response(429, json={"error": 429, "message": "slow down"})
    )
    with Como() as c, pytest.raises(ComoRateLimitError) as ei:
        c.profile.search(search="x")
    assert ei.value.status_code == 429


@respx.mock
def test_not_found_maps():
    respx.get(f"{BASE}/v1/ghost/job").mock(
        return_value=httpx.Response(404, json={"error": 404, "message": "no such job"})
    )
    with Como() as c, pytest.raises(ComoNotFoundError):
        c.job.get(job_id="missing")


@respx.mock
def test_server_error_maps():
    respx.get(f"{BASE}/v1/ghost/company").mock(return_value=httpx.Response(503, text="upstream down"))
    with Como() as c, pytest.raises(ComoServerError):
        c.company.get(universal_name="acme")


@respx.mock
def test_unauthorized_maps():
    respx.get(f"{BASE}/v1/ghost/post").mock(return_value=httpx.Response(401, json={"error": 401, "message": "bad key"}))
    with Como() as c, pytest.raises(ComoAuthError):
        c.post.get(url="https://x")


# ---------- async smoke (one per shape) ----------


@respx.mock
async def test_async_post_get_and_geo_search():
    respx.get(f"{BASE}/v1/ghost/post").mock(
        return_value=httpx.Response(200, json=_envelope({"id": "p", "content": "hi"}))
    )
    respx.get(f"{BASE}/v1/ghost/geo-id-search").mock(
        return_value=httpx.Response(
            200,
            json={"id": "1", "elements": [{"geoId": "1", "title": "Place"}], "status": "ok"},
        )
    )
    async with AsyncComo() as c:
        post = await c.post.get(url="https://x")
        geo = await c.geo.search(search="place")
    assert post.content == "hi"
    assert geo.elements[0].title == "Place"
