"""CRM views resource — saved table/kanban views over an object or a list.

The single source of truth for the ``/v1/crm/views`` route map: create a view,
set its columns/sorts/filter/kanban layout, read the operator catalog. Mirrors
``resources/lists.py``; the CLI wraps these methods.
"""

from __future__ import annotations

from typing import Any

from como_core.platform import View

from .._params import clean_params
from ._base import AsyncResource, SyncResource

_BASE = "/v1/crm/views"


def _create_body(
    *,
    name: str,
    object_id: str | None,
    list_id: str | None,
    view_type: str,
    description: str | None,
    duplicate_of: str | None,
    kanban_config: dict[str, Any] | None,
) -> dict:
    body: dict[str, Any] = {"name": name, "view_type": view_type}
    for key, val in (
        ("object_id", object_id),
        ("list_id", list_id),
        ("description", description),
        ("duplicate_of", duplicate_of),
        ("kanban_config", kanban_config),
    ):
        if val is not None:
            body[key] = val
    return body


def _update_body(
    *,
    name: str | None,
    description: str | None,
    is_default: bool | None,
    view_type: str | None,
    kanban_config: dict[str, Any] | None,
) -> dict:
    body: dict[str, Any] = {}
    for key, val in (
        ("name", name),
        ("description", description),
        ("is_default", is_default),
        ("view_type", view_type),
        ("kanban_config", kanban_config),
    ):
        if val is not None:
            body[key] = val
    return body


class ViewsResource(SyncResource):
    def create(
        self,
        *,
        name: str,
        object_id: str | None = None,
        list_id: str | None = None,
        view_type: str = "table",
        description: str | None = None,
        duplicate_of: str | None = None,
        kanban_config: dict[str, Any] | None = None,
    ) -> View:
        body = _create_body(
            name=name,
            object_id=object_id,
            list_id=list_id,
            view_type=view_type,
            description=description,
            duplicate_of=duplicate_of,
            kanban_config=kanban_config,
        )
        return View.model_validate(self._t.post(_BASE, json=body))

    def get(self, view_id: str) -> View:
        return View.model_validate(self._t.get(f"{_BASE}/{view_id}"))

    def list_for_object(self, object_id: str) -> list[View]:
        body = self._t.get(_BASE, params=clean_params({"object_id": object_id}))
        return [View.model_validate(v) for v in body or []]

    def list_for_list(self, list_id: str) -> list[View]:
        body = self._t.get(_BASE, params=clean_params({"list_id": list_id}))
        return [View.model_validate(v) for v in body or []]

    def update(
        self,
        view_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        is_default: bool | None = None,
        view_type: str | None = None,
        kanban_config: dict[str, Any] | None = None,
    ) -> View:
        body = _update_body(
            name=name,
            description=description,
            is_default=is_default,
            view_type=view_type,
            kanban_config=kanban_config,
        )
        return View.model_validate(self._t.patch(f"{_BASE}/{view_id}", json=body))

    def set_columns(self, view_id: str, *, columns: list[dict[str, Any]]) -> View:
        return View.model_validate(self._t.put(f"{_BASE}/{view_id}/columns", json={"columns": columns}))

    def set_sorts(self, view_id: str, *, sorts: list[dict[str, Any]]) -> View:
        return View.model_validate(self._t.put(f"{_BASE}/{view_id}/sorts", json={"sorts": sorts}))

    def set_filter(self, view_id: str, *, filter: dict[str, Any] | None) -> View:
        return View.model_validate(self._t.put(f"{_BASE}/{view_id}/filter", json={"filter": filter}))

    def set_kanban_config(self, view_id: str, *, kanban_config: dict[str, Any]) -> View:
        body = {"kanban_config": kanban_config}
        return View.model_validate(self._t.put(f"{_BASE}/{view_id}/kanban-config", json=body))

    def delete(self, view_id: str, *, promote_to: str | None = None) -> None:
        suffix = f"?promote={promote_to}" if promote_to else ""
        self._t.delete(f"{_BASE}/{view_id}{suffix}")

    def operators(self) -> dict[str, list[str]]:
        return dict(self._t.get(f"{_BASE}/operators") or {})


class AsyncViewsResource(AsyncResource):
    async def create(
        self,
        *,
        name: str,
        object_id: str | None = None,
        list_id: str | None = None,
        view_type: str = "table",
        description: str | None = None,
        duplicate_of: str | None = None,
        kanban_config: dict[str, Any] | None = None,
    ) -> View:
        body = _create_body(
            name=name,
            object_id=object_id,
            list_id=list_id,
            view_type=view_type,
            description=description,
            duplicate_of=duplicate_of,
            kanban_config=kanban_config,
        )
        return View.model_validate(await self._t.post(_BASE, json=body))

    async def get(self, view_id: str) -> View:
        return View.model_validate(await self._t.get(f"{_BASE}/{view_id}"))

    async def list_for_object(self, object_id: str) -> list[View]:
        body = await self._t.get(_BASE, params=clean_params({"object_id": object_id}))
        return [View.model_validate(v) for v in body or []]

    async def list_for_list(self, list_id: str) -> list[View]:
        body = await self._t.get(_BASE, params=clean_params({"list_id": list_id}))
        return [View.model_validate(v) for v in body or []]

    async def update(
        self,
        view_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        is_default: bool | None = None,
        view_type: str | None = None,
        kanban_config: dict[str, Any] | None = None,
    ) -> View:
        body = _update_body(
            name=name,
            description=description,
            is_default=is_default,
            view_type=view_type,
            kanban_config=kanban_config,
        )
        return View.model_validate(await self._t.patch(f"{_BASE}/{view_id}", json=body))

    async def set_columns(self, view_id: str, *, columns: list[dict[str, Any]]) -> View:
        return View.model_validate(await self._t.put(f"{_BASE}/{view_id}/columns", json={"columns": columns}))

    async def set_sorts(self, view_id: str, *, sorts: list[dict[str, Any]]) -> View:
        return View.model_validate(await self._t.put(f"{_BASE}/{view_id}/sorts", json={"sorts": sorts}))

    async def set_filter(self, view_id: str, *, filter: dict[str, Any] | None) -> View:
        return View.model_validate(await self._t.put(f"{_BASE}/{view_id}/filter", json={"filter": filter}))

    async def set_kanban_config(self, view_id: str, *, kanban_config: dict[str, Any]) -> View:
        body = {"kanban_config": kanban_config}
        return View.model_validate(await self._t.put(f"{_BASE}/{view_id}/kanban-config", json=body))

    async def delete(self, view_id: str, *, promote_to: str | None = None) -> None:
        suffix = f"?promote={promote_to}" if promote_to else ""
        await self._t.delete(f"{_BASE}/{view_id}{suffix}")

    async def operators(self) -> dict[str, list[str]]:
        return dict(await self._t.get(f"{_BASE}/operators") or {})
