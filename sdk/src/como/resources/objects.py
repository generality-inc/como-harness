"""CRM objects (catalog) resource — the object *types* (Companies, People, …).

Wraps ``/v1/crm/objects``. There is no get-by-id route; use ``list()`` (the CLI
resolves a slug to an id by scanning it).
"""

from __future__ import annotations

from typing import Any

from como_core.crm import CrmObject

from ._base import AsyncResource, SyncResource

_BASE = "/v1/crm/objects"


def _create_body(*, slug: str, singular_name: str, plural_name: str, icon: str | None, color: str | None) -> dict:
    body: dict[str, Any] = {"slug": slug, "singular_name": singular_name, "plural_name": plural_name}
    if icon is not None:
        body["icon"] = icon
    if color is not None:
        body["color"] = color
    return body


def _update_body(*, singular_name: str | None, plural_name: str | None, icon: str | None, color: str | None) -> dict:
    body: dict[str, Any] = {}
    for k, v in (("singular_name", singular_name), ("plural_name", plural_name), ("icon", icon), ("color", color)):
        if v is not None:
            body[k] = v
    return body


class ObjectsResource(SyncResource):
    def list(self) -> list[CrmObject]:
        body = self._t.get(_BASE)
        return [CrmObject.model_validate(o) for o in body or []]

    def create(
        self, *, slug: str, singular_name: str, plural_name: str, icon: str | None = None, color: str | None = None
    ) -> CrmObject:
        body = _create_body(slug=slug, singular_name=singular_name, plural_name=plural_name, icon=icon, color=color)
        return CrmObject.model_validate(self._t.post(_BASE, json=body))

    def update(
        self,
        object_id: str,
        *,
        singular_name: str | None = None,
        plural_name: str | None = None,
        icon: str | None = None,
        color: str | None = None,
    ) -> CrmObject:
        body = _update_body(singular_name=singular_name, plural_name=plural_name, icon=icon, color=color)
        return CrmObject.model_validate(self._t.patch(f"{_BASE}/{object_id}", json=body))

    def delete(self, object_id: str) -> None:
        self._t.delete(f"{_BASE}/{object_id}")


class AsyncObjectsResource(AsyncResource):
    async def list(self) -> list[CrmObject]:
        body = await self._t.get(_BASE)
        return [CrmObject.model_validate(o) for o in body or []]

    async def create(
        self, *, slug: str, singular_name: str, plural_name: str, icon: str | None = None, color: str | None = None
    ) -> CrmObject:
        body = _create_body(slug=slug, singular_name=singular_name, plural_name=plural_name, icon=icon, color=color)
        return CrmObject.model_validate(await self._t.post(_BASE, json=body))

    async def update(
        self,
        object_id: str,
        *,
        singular_name: str | None = None,
        plural_name: str | None = None,
        icon: str | None = None,
        color: str | None = None,
    ) -> CrmObject:
        body = _update_body(singular_name=singular_name, plural_name=plural_name, icon=icon, color=color)
        return CrmObject.model_validate(await self._t.patch(f"{_BASE}/{object_id}", json=body))

    async def delete(self, object_id: str) -> None:
        await self._t.delete(f"{_BASE}/{object_id}")
