from __future__ import annotations

from como_core.group import Group, GroupSearchResult

from .._params import clean_params, require_one_of
from ._base import AsyncResource, SyncResource, lift_cost

_PATH_GET = "/v1/ghost/group"
_PATH_SEARCH = "/v1/ghost/group-search"


def _get_params(*, url, group_id) -> dict[str, str]:
    require_one_of(url=url, group_id=group_id)
    return clean_params({"url": url, "groupId": group_id})


def _search_params(*, search, page) -> dict[str, str]:
    return clean_params({"search": search, "page": page})


class GroupResource(SyncResource):
    def get(
        self,
        *,
        url: str | None = None,
        group_id: str | None = None,
    ) -> Group:
        params = _get_params(url=url, group_id=group_id)
        body = self._t.get(_PATH_GET, params=params)
        return lift_cost(Group.model_validate(body.get("element") or {}), body)

    def search(
        self,
        *,
        search: str | None = None,
        page: int | None = None,
    ) -> GroupSearchResult:
        params = _search_params(search=search, page=page)
        body = self._t.get(_PATH_SEARCH, params=params)
        return GroupSearchResult.model_validate(body)


class AsyncGroupResource(AsyncResource):
    async def get(
        self,
        *,
        url: str | None = None,
        group_id: str | None = None,
    ) -> Group:
        params = _get_params(url=url, group_id=group_id)
        body = await self._t.get(_PATH_GET, params=params)
        return lift_cost(Group.model_validate(body.get("element") or {}), body)

    async def search(
        self,
        *,
        search: str | None = None,
        page: int | None = None,
    ) -> GroupSearchResult:
        params = _search_params(search=search, page=page)
        body = await self._t.get(_PATH_SEARCH, params=params)
        return GroupSearchResult.model_validate(body)
