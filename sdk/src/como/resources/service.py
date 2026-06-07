from __future__ import annotations

from como_core.service import ServiceSearchResult

from .._params import clean_params
from ._base import AsyncResource, SyncResource

_PATH_SEARCH = "/v1/ghost/service-search"


def _search_params(*, search, location, geo_id, page) -> dict[str, str]:
    if search is None:
        raise ValueError("search is required.")
    return clean_params(
        {
            "search": search,
            "location": location,
            "geoId": geo_id,
            "page": page,
        }
    )


class ServiceResource(SyncResource):
    def search(
        self,
        *,
        search: str,
        location: str | None = None,
        geo_id: str | None = None,
        page: int | None = None,
    ) -> ServiceSearchResult:
        params = _search_params(search=search, location=location, geo_id=geo_id, page=page)
        body = self._t.get(_PATH_SEARCH, params=params)
        return ServiceSearchResult.model_validate(body)


class AsyncServiceResource(AsyncResource):
    async def search(
        self,
        *,
        search: str,
        location: str | None = None,
        geo_id: str | None = None,
        page: int | None = None,
    ) -> ServiceSearchResult:
        params = _search_params(search=search, location=location, geo_id=geo_id, page=page)
        body = await self._t.get(_PATH_SEARCH, params=params)
        return ServiceSearchResult.model_validate(body)
