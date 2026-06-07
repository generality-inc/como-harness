from __future__ import annotations

from como_core.company import Company, CompanySearchResult
from como_core.post import PostsResult

from .._params import clean_params, require_one_of
from ._base import AsyncResource, SyncResource

_PATH_GET = "/v1/ghost/company"
_PATH_SEARCH = "/v1/ghost/company-search"
_PATH_POSTS = "/v1/ghost/company-posts"


def _get_params(*, url, universal_name, search) -> dict[str, str]:
    require_one_of(url=url, universal_name=universal_name, search=search)
    return clean_params(
        {
            "url": url,
            "universalName": universal_name,
            "search": search,
        }
    )


def _search_params(**kwargs) -> dict[str, str]:
    return clean_params(
        {
            "search": kwargs.get("search"),
            "location": kwargs.get("location"),
            "geoId": kwargs.get("geo_id"),
            "companySize": kwargs.get("company_size"),
            "industryId": kwargs.get("industry_id"),
            "page": kwargs.get("page"),
        }
    )


def _posts_params(
    *, company, company_id, company_universal_name, posted_limit, scrape_posted_limit, page, pagination_token
) -> dict[str, str]:
    require_one_of(company=company, company_id=company_id, company_universal_name=company_universal_name)
    return clean_params(
        {
            "company": company,
            "companyId": company_id,
            "companyUniversalName": company_universal_name,
            "postedLimit": posted_limit,
            "scrapePostedLimit": scrape_posted_limit,
            "page": page,
            "paginationToken": pagination_token,
        }
    )


class CompanyResource(SyncResource):
    def get(
        self,
        *,
        url: str | None = None,
        universal_name: str | None = None,
        search: str | None = None,
    ) -> Company:
        params = _get_params(url=url, universal_name=universal_name, search=search)
        body = self._t.get(_PATH_GET, params=params)
        return Company.model_validate(body.get("element") or {})

    def search(
        self,
        *,
        search: str | None = None,
        location: str | None = None,
        geo_id: str | None = None,
        company_size: str | None = None,
        industry_id: str | None = None,
        page: int | None = None,
    ) -> CompanySearchResult:
        params = _search_params(
            search=search,
            location=location,
            geo_id=geo_id,
            company_size=company_size,
            industry_id=industry_id,
            page=page,
        )
        body = self._t.get(_PATH_SEARCH, params=params)
        return CompanySearchResult.model_validate(body)

    def posts(
        self,
        *,
        company: str | None = None,
        company_id: str | None = None,
        company_universal_name: str | None = None,
        posted_limit: str | None = None,
        scrape_posted_limit: str | None = None,
        page: int | None = None,
        pagination_token: str | None = None,
    ) -> PostsResult:
        params = _posts_params(
            company=company,
            company_id=company_id,
            company_universal_name=company_universal_name,
            posted_limit=posted_limit,
            scrape_posted_limit=scrape_posted_limit,
            page=page,
            pagination_token=pagination_token,
        )
        body = self._t.get(_PATH_POSTS, params=params)
        return PostsResult.model_validate(body)


class AsyncCompanyResource(AsyncResource):
    async def get(
        self,
        *,
        url: str | None = None,
        universal_name: str | None = None,
        search: str | None = None,
    ) -> Company:
        params = _get_params(url=url, universal_name=universal_name, search=search)
        body = await self._t.get(_PATH_GET, params=params)
        return Company.model_validate(body.get("element") or {})

    async def search(
        self,
        *,
        search: str | None = None,
        location: str | None = None,
        geo_id: str | None = None,
        company_size: str | None = None,
        industry_id: str | None = None,
        page: int | None = None,
    ) -> CompanySearchResult:
        params = _search_params(
            search=search,
            location=location,
            geo_id=geo_id,
            company_size=company_size,
            industry_id=industry_id,
            page=page,
        )
        body = await self._t.get(_PATH_SEARCH, params=params)
        return CompanySearchResult.model_validate(body)

    async def posts(
        self,
        *,
        company: str | None = None,
        company_id: str | None = None,
        company_universal_name: str | None = None,
        posted_limit: str | None = None,
        scrape_posted_limit: str | None = None,
        page: int | None = None,
        pagination_token: str | None = None,
    ) -> PostsResult:
        params = _posts_params(
            company=company,
            company_id=company_id,
            company_universal_name=company_universal_name,
            posted_limit=posted_limit,
            scrape_posted_limit=scrape_posted_limit,
            page=page,
            pagination_token=pagination_token,
        )
        body = await self._t.get(_PATH_POSTS, params=params)
        return PostsResult.model_validate(body)
