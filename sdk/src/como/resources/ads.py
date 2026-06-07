from __future__ import annotations

from como_core.ads import Ad, AdSearchResult

from .._params import clean_params, require_one_of
from ._base import AsyncResource, SyncResource

_PATH_GET = "/v1/ghost/ad"
_PATH_SEARCH = "/v1/ghost/ad-search"


def _get_params(*, ad_id, url) -> dict[str, str]:
    require_one_of(ad_id=ad_id, url=url)
    return clean_params({"adId": ad_id, "url": url})


def _search_params(**kwargs) -> dict[str, str]:
    return clean_params(
        {
            "searchUrl": kwargs.get("search_url"),
            "keyword": kwargs.get("keyword"),
            "accountOwner": kwargs.get("account_owner"),
            "countries": kwargs.get("countries"),
            "dateOption": kwargs.get("date_option"),
            "startdate": kwargs.get("startdate"),
            "enddate": kwargs.get("enddate"),
            "paginationToken": kwargs.get("pagination_token"),
        }
    )


class AdsResource(SyncResource):
    def get(
        self,
        *,
        ad_id: str | None = None,
        url: str | None = None,
    ) -> Ad:
        params = _get_params(ad_id=ad_id, url=url)
        body = self._t.get(_PATH_GET, params=params)
        return Ad.model_validate(body)

    def search(
        self,
        *,
        search_url: str | None = None,
        keyword: str | None = None,
        account_owner: str | None = None,
        countries: str | None = None,
        date_option: str | None = None,
        startdate: str | None = None,
        enddate: str | None = None,
        pagination_token: str | None = None,
    ) -> AdSearchResult:
        params = _search_params(
            search_url=search_url,
            keyword=keyword,
            account_owner=account_owner,
            countries=countries,
            date_option=date_option,
            startdate=startdate,
            enddate=enddate,
            pagination_token=pagination_token,
        )
        body = self._t.get(_PATH_SEARCH, params=params)
        return AdSearchResult.model_validate(body)


class AsyncAdsResource(AsyncResource):
    async def get(
        self,
        *,
        ad_id: str | None = None,
        url: str | None = None,
    ) -> Ad:
        params = _get_params(ad_id=ad_id, url=url)
        body = await self._t.get(_PATH_GET, params=params)
        return Ad.model_validate(body)

    async def search(
        self,
        *,
        search_url: str | None = None,
        keyword: str | None = None,
        account_owner: str | None = None,
        countries: str | None = None,
        date_option: str | None = None,
        startdate: str | None = None,
        enddate: str | None = None,
        pagination_token: str | None = None,
    ) -> AdSearchResult:
        params = _search_params(
            search_url=search_url,
            keyword=keyword,
            account_owner=account_owner,
            countries=countries,
            date_option=date_option,
            startdate=startdate,
            enddate=enddate,
            pagination_token=pagination_token,
        )
        body = await self._t.get(_PATH_SEARCH, params=params)
        return AdSearchResult.model_validate(body)
