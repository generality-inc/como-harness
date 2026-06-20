"""CRM lists resource — read and build lists, manage entries + list-scoped columns.

The single source of truth for the ``/v1/crm/lists`` route map; the CLI wraps
these methods. Lists are resolved to ids by the caller (the CLI resolves
name/slug → id); the SDK deals in ids.
"""

from __future__ import annotations

from typing import Any

from como_core.crm import (
    Attribute,
    ListEntriesRemovedResult,
    ListEntriesResult,
    ListEntry,
    RecordList,
    RecordRow,
    ReorderResult,
)

from ._base import AsyncResource, SyncResource

_BASE = "/v1/crm/lists"


def _create_body(*, parent_object_id: str, name: str, emoji: str | None) -> dict:
    body: dict[str, Any] = {"parent_object_id": parent_object_id, "name": name}
    if emoji is not None:
        body["emoji"] = emoji
    return body


def _update_body(*, name: str | None, emoji: str | None) -> dict:
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if emoji is not None:
        body["emoji"] = emoji
    return body


def _attr_body(
    *, slug: str, name: str, type: str, description: str | None, config: dict | None, is_required: bool, is_unique: bool
) -> dict:
    body: dict[str, Any] = {
        "slug": slug,
        "name": name,
        "type": type,
        "is_required": is_required,
        "is_unique": is_unique,
    }
    if description is not None:
        body["description"] = description
    if config is not None:
        body["config"] = config
    return body


class ListsResource(SyncResource):
    # --- list CRUD --------------------------------------------------------
    def list(self) -> list[RecordList]:
        body = self._t.get(_BASE)
        return [RecordList.model_validate(lst) for lst in body or []]

    def get(self, list_id: str) -> RecordList:
        return RecordList.model_validate(self._t.get(f"{_BASE}/{list_id}"))

    def create(self, *, parent_object_id: str, name: str, emoji: str | None = None) -> RecordList:
        return RecordList.model_validate(
            self._t.post(_BASE, json=_create_body(parent_object_id=parent_object_id, name=name, emoji=emoji))
        )

    def update(self, list_id: str, *, name: str | None = None, emoji: str | None = None) -> RecordList:
        return RecordList.model_validate(self._t.patch(f"{_BASE}/{list_id}", json=_update_body(name=name, emoji=emoji)))

    def delete(self, list_id: str) -> None:
        self._t.delete(f"{_BASE}/{list_id}")

    def duplicate(self, list_id: str) -> RecordList:
        return RecordList.model_validate(self._t.post(f"{_BASE}/{list_id}/duplicate", json={}))

    def change_parent_object(self, list_id: str, *, parent_object_id: str) -> RecordList:
        body = {"parent_object_id": parent_object_id}
        return RecordList.model_validate(self._t.patch(f"{_BASE}/{list_id}/parent-object", json=body))

    def reorder(self, *, ordered_list_ids: list[str]) -> ReorderResult:
        return ReorderResult.model_validate(
            self._t.patch(f"{_BASE}/positions", json={"ordered_list_ids": ordered_list_ids})
        )

    # --- reads ------------------------------------------------------------
    def records(self, list_id: str) -> list[RecordRow]:
        """Rows in the list — each carries the record's ``data`` plus the
        list-scoped ``list_data`` (the entry's per-list column values)."""
        body = self._t.get(f"{_BASE}/{list_id}/records")
        return [RecordRow.model_validate(r) for r in body or []]

    def entries(self, list_id: str) -> list[ListEntry]:
        body = self._t.get(f"{_BASE}/{list_id}/entries")
        return [ListEntry.model_validate(e) for e in body or []]

    # --- entries ----------------------------------------------------------
    def add_entry(self, list_id: str, *, record_id: str) -> ListEntry:
        return ListEntry.model_validate(self._t.post(f"{_BASE}/{list_id}/entries", json={"record_id": record_id}))

    def add_entries(self, list_id: str, *, record_ids: list[str]) -> ListEntriesResult:
        body = self._t.post(f"{_BASE}/{list_id}/entries/bulk", json={"record_ids": record_ids})
        return ListEntriesResult.model_validate(body)

    def remove_entry(self, list_id: str, *, record_id: str) -> None:
        self._t.delete(f"{_BASE}/{list_id}/entries/{record_id}")

    def remove_entries(self, list_id: str, *, record_ids: list[str]) -> ListEntriesRemovedResult:
        body = self._t.delete(f"{_BASE}/{list_id}/entries/bulk", json={"record_ids": record_ids})
        return ListEntriesRemovedResult.model_validate(body)

    def update_entry_data(self, list_id: str, *, record_id: str, data: dict[str, Any]) -> ListEntry:
        """Merge list-scoped column values into a record's entry (PATCH semantics)."""
        return ListEntry.model_validate(self._t.patch(f"{_BASE}/{list_id}/entries/{record_id}", json={"data": data}))

    def reorder_entries(self, list_id: str, *, ordered_record_ids: list[str]) -> ReorderResult:
        body = {"ordered_record_ids": ordered_record_ids}
        return ReorderResult.model_validate(self._t.patch(f"{_BASE}/{list_id}/entries/positions", json=body))

    # --- list-scoped attributes (the entry_data columns) -----------------
    def attributes(self, list_id: str) -> list[Attribute]:
        body = self._t.get(f"{_BASE}/{list_id}/attributes")
        return [Attribute.model_validate(a) for a in body or []]

    def create_attribute(
        self,
        list_id: str,
        *,
        slug: str,
        name: str,
        type: str,
        description: str | None = None,
        config: dict | None = None,
        is_required: bool = False,
        is_unique: bool = False,
    ) -> Attribute:
        body = _attr_body(
            slug=slug,
            name=name,
            type=type,
            description=description,
            config=config,
            is_required=is_required,
            is_unique=is_unique,
        )
        return Attribute.model_validate(self._t.post(f"{_BASE}/{list_id}/attributes", json=body))


class AsyncListsResource(AsyncResource):
    async def list(self) -> list[RecordList]:
        body = await self._t.get(_BASE)
        return [RecordList.model_validate(lst) for lst in body or []]

    async def get(self, list_id: str) -> RecordList:
        return RecordList.model_validate(await self._t.get(f"{_BASE}/{list_id}"))

    async def create(self, *, parent_object_id: str, name: str, emoji: str | None = None) -> RecordList:
        return RecordList.model_validate(
            await self._t.post(_BASE, json=_create_body(parent_object_id=parent_object_id, name=name, emoji=emoji))
        )

    async def update(self, list_id: str, *, name: str | None = None, emoji: str | None = None) -> RecordList:
        return RecordList.model_validate(
            await self._t.patch(f"{_BASE}/{list_id}", json=_update_body(name=name, emoji=emoji))
        )

    async def delete(self, list_id: str) -> None:
        await self._t.delete(f"{_BASE}/{list_id}")

    async def duplicate(self, list_id: str) -> RecordList:
        return RecordList.model_validate(await self._t.post(f"{_BASE}/{list_id}/duplicate", json={}))

    async def change_parent_object(self, list_id: str, *, parent_object_id: str) -> RecordList:
        body = {"parent_object_id": parent_object_id}
        return RecordList.model_validate(await self._t.patch(f"{_BASE}/{list_id}/parent-object", json=body))

    async def reorder(self, *, ordered_list_ids: list[str]) -> ReorderResult:
        return ReorderResult.model_validate(
            await self._t.patch(f"{_BASE}/positions", json={"ordered_list_ids": ordered_list_ids})
        )

    async def records(self, list_id: str) -> list[RecordRow]:
        body = await self._t.get(f"{_BASE}/{list_id}/records")
        return [RecordRow.model_validate(r) for r in body or []]

    async def entries(self, list_id: str) -> list[ListEntry]:
        body = await self._t.get(f"{_BASE}/{list_id}/entries")
        return [ListEntry.model_validate(e) for e in body or []]

    async def add_entry(self, list_id: str, *, record_id: str) -> ListEntry:
        return ListEntry.model_validate(await self._t.post(f"{_BASE}/{list_id}/entries", json={"record_id": record_id}))

    async def add_entries(self, list_id: str, *, record_ids: list[str]) -> ListEntriesResult:
        body = await self._t.post(f"{_BASE}/{list_id}/entries/bulk", json={"record_ids": record_ids})
        return ListEntriesResult.model_validate(body)

    async def remove_entry(self, list_id: str, *, record_id: str) -> None:
        await self._t.delete(f"{_BASE}/{list_id}/entries/{record_id}")

    async def remove_entries(self, list_id: str, *, record_ids: list[str]) -> ListEntriesRemovedResult:
        body = await self._t.delete(f"{_BASE}/{list_id}/entries/bulk", json={"record_ids": record_ids})
        return ListEntriesRemovedResult.model_validate(body)

    async def update_entry_data(self, list_id: str, *, record_id: str, data: dict[str, Any]) -> ListEntry:
        return ListEntry.model_validate(
            await self._t.patch(f"{_BASE}/{list_id}/entries/{record_id}", json={"data": data})
        )

    async def reorder_entries(self, list_id: str, *, ordered_record_ids: list[str]) -> ReorderResult:
        body = {"ordered_record_ids": ordered_record_ids}
        return ReorderResult.model_validate(await self._t.patch(f"{_BASE}/{list_id}/entries/positions", json=body))

    async def attributes(self, list_id: str) -> list[Attribute]:
        body = await self._t.get(f"{_BASE}/{list_id}/attributes")
        return [Attribute.model_validate(a) for a in body or []]

    async def create_attribute(
        self,
        list_id: str,
        *,
        slug: str,
        name: str,
        type: str,
        description: str | None = None,
        config: dict | None = None,
        is_required: bool = False,
        is_unique: bool = False,
    ) -> Attribute:
        body = _attr_body(
            slug=slug,
            name=name,
            type=type,
            description=description,
            config=config,
            is_required=is_required,
            is_unique=is_unique,
        )
        return Attribute.model_validate(await self._t.post(f"{_BASE}/{list_id}/attributes", json=body))
