from __future__ import annotations

from como_core.geo import GeoSearchResult

from .._params import clean_params
from ._base import AsyncResource, SyncResource

_PATH_SEARCH = "/v1/ghost/geo-id-search"


def _search_params(*, search) -> dict[str, str]:
    if search is None:
        raise ValueError("search is required.")
    return clean_params({"search": search})


class GeoResource(SyncResource):
    def search(self, *, search: str) -> GeoSearchResult:
        params = _search_params(search=search)
        body = self._t.get(_PATH_SEARCH, params=params)
        return GeoSearchResult.model_validate(body)


class AsyncGeoResource(AsyncResource):
    async def search(self, *, search: str) -> GeoSearchResult:
        params = _search_params(search=search)
        body = await self._t.get(_PATH_SEARCH, params=params)
        return GeoSearchResult.model_validate(body)
