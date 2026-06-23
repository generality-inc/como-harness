"""CRM records resource — full CRUD + references + merge + catalog reads.

The single source of truth for how the SDK and CLI talk to the platform's
record endpoints. Request shaping, the ``/v1/crm`` route map, and response
parsing all live here; the CLI is a thin wrapper over these methods.
"""

from __future__ import annotations

from typing import Any

from como_core.crm import (
    BulkDeleteResult,
    DuplicateCandidate,
    ListMembership,
    Record,
    RelatedRecord,
    UpsertResult,
)

from .._params import clean_params
from ._base import AsyncResource, SyncResource

_BASE = "/v1/crm"
_RECORDS = f"{_BASE}/records"


def _create_body(
    *,
    object_id: str,
    name: str | None,
    data: dict[str, Any] | None,
    list_id: str | None,
    evidence: dict[str, Any] | None,
) -> dict:
    body: dict[str, Any] = {"object_id": object_id, "name": name, "data": data or {}}
    if list_id is not None:
        body["list_id"] = list_id
    if evidence is not None:
        body["evidence"] = evidence
    return body


def _upsert_body(
    *,
    object_id: str,
    identity_slug: str,
    identity_value: str | list[str],
    name: str | None,
    data: dict[str, Any] | None,
    list_id: str | None,
    evidence: dict[str, Any] | None,
) -> dict:
    body: dict[str, Any] = {
        "object_id": object_id,
        "identity_slug": identity_slug,
        "identity_value": identity_value,
        "name": name,
        "data": data or {},
    }
    if list_id is not None:
        body["list_id"] = list_id
    if evidence is not None:
        body["evidence"] = evidence
    return body


def _update_body(
    *,
    name: str | None,
    data: dict[str, Any] | None,
    status: str | None,
    owner_member_id: str | None,
    unset_owner: bool,
    evidence: dict[str, Any] | None,
) -> dict:
    """Only the fields explicitly supplied — a server-side partial update."""
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if data is not None:
        body["data"] = data
    if status is not None:
        body["status"] = status
    if owner_member_id is not None:
        body["owner_member_id"] = owner_member_id
    if unset_owner:
        body["unset_owner"] = True
    if evidence is not None:
        body["evidence"] = evidence
    return body


def _search_body(*, q: str, limit: int, object_id: str | None) -> dict:
    body: dict[str, Any] = {"q": q, "limit": limit}
    if object_id is not None:
        body["object_id"] = object_id
    return body


class RecordsResource(SyncResource):
    def create(
        self,
        *,
        object_id: str,
        name: str | None = None,
        data: dict[str, Any] | None = None,
        list_id: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> Record:
        body = _create_body(object_id=object_id, name=name, data=data, list_id=list_id, evidence=evidence)
        return Record.model_validate(self._t.post(_RECORDS, json=body))

    def upsert(
        self,
        *,
        object_id: str,
        identity_slug: str,
        identity_value: str | list[str],
        name: str | None = None,
        data: dict[str, Any] | None = None,
        list_id: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> UpsertResult:
        body = _upsert_body(
            object_id=object_id,
            identity_slug=identity_slug,
            identity_value=identity_value,
            name=name,
            data=data,
            list_id=list_id,
            evidence=evidence,
        )
        return UpsertResult.model_validate(self._t.post(f"{_RECORDS}/upsert", json=body))

    def get(self, record_id: str) -> Record:
        return Record.model_validate(self._t.get(f"{_RECORDS}/{record_id}"))

    def list(self, *, object_id: str, limit: int = 50, offset: int = 0, view_id: str | None = None) -> list[Record]:
        params = clean_params({"object_id": object_id, "limit": limit, "offset": offset, "view_id": view_id})
        body = self._t.get(_RECORDS, params=params)
        return [Record.model_validate(r) for r in body or []]

    def related(self, record_id: str) -> list[RelatedRecord]:
        body = self._t.get(f"{_RECORDS}/{record_id}/related")
        return [RelatedRecord.model_validate(r) for r in body or []]

    def duplicates(
        self, *, object_id: str, name: str | None = None, data: dict[str, Any] | None = None
    ) -> list[DuplicateCandidate]:
        body = self._t.post(f"{_RECORDS}/duplicates", json={"object_id": object_id, "name": name, "data": data or {}})
        return [DuplicateCandidate.model_validate(d) for d in body or []]

    def search(self, *, q: str, limit: int = 20, object_id: str | None = None) -> list[Record]:
        body = self._t.post(f"{_RECORDS}/search", json=_search_body(q=q, limit=limit, object_id=object_id))
        return [Record.model_validate(r) for r in body or []]

    def update(
        self,
        record_id: str,
        *,
        name: str | None = None,
        data: dict[str, Any] | None = None,
        status: str | None = None,
        owner_member_id: str | None = None,
        unset_owner: bool = False,
        evidence: dict[str, Any] | None = None,
    ) -> Record:
        body = _update_body(
            name=name,
            data=data,
            status=status,
            owner_member_id=owner_member_id,
            unset_owner=unset_owner,
            evidence=evidence,
        )
        return Record.model_validate(self._t.patch(f"{_RECORDS}/{record_id}", json=body))

    def delete(self, record_id: str) -> None:
        self._t.delete(f"{_RECORDS}/{record_id}")

    def bulk_delete(self, record_ids: list[str]) -> BulkDeleteResult:
        body = self._t.post(f"{_RECORDS}/bulk-delete", json={"record_ids": record_ids})
        return BulkDeleteResult.model_validate(body)

    def restore(self, record_id: str) -> Record:
        return Record.model_validate(self._t.post(f"{_RECORDS}/{record_id}/restore", json={}))

    def set_references(self, record_id: str, *, attribute_id: str, target_record_ids: list[str]) -> None:
        self._t.put(
            f"{_RECORDS}/{record_id}/references",
            json={"attribute_id": attribute_id, "target_record_ids": target_record_ids},
        )

    def merge(self, record_id: str, *, victim_id: str) -> Record:
        return Record.model_validate(self._t.post(f"{_RECORDS}/{record_id}/merge", json={"victim_id": victim_id}))

    def lists(self, record_id: str) -> list[ListMembership]:
        body = self._t.get(f"{_RECORDS}/{record_id}/lists")
        return [ListMembership.model_validate(m) for m in body or []]


class AsyncRecordsResource(AsyncResource):
    async def create(
        self,
        *,
        object_id: str,
        name: str | None = None,
        data: dict[str, Any] | None = None,
        list_id: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> Record:
        body = _create_body(object_id=object_id, name=name, data=data, list_id=list_id, evidence=evidence)
        return Record.model_validate(await self._t.post(_RECORDS, json=body))

    async def upsert(
        self,
        *,
        object_id: str,
        identity_slug: str,
        identity_value: str | list[str],
        name: str | None = None,
        data: dict[str, Any] | None = None,
        list_id: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> UpsertResult:
        body = _upsert_body(
            object_id=object_id,
            identity_slug=identity_slug,
            identity_value=identity_value,
            name=name,
            data=data,
            list_id=list_id,
            evidence=evidence,
        )
        return UpsertResult.model_validate(await self._t.post(f"{_RECORDS}/upsert", json=body))

    async def get(self, record_id: str) -> Record:
        return Record.model_validate(await self._t.get(f"{_RECORDS}/{record_id}"))

    async def list(
        self, *, object_id: str, limit: int = 50, offset: int = 0, view_id: str | None = None
    ) -> list[Record]:
        params = clean_params({"object_id": object_id, "limit": limit, "offset": offset, "view_id": view_id})
        body = await self._t.get(_RECORDS, params=params)
        return [Record.model_validate(r) for r in body or []]

    async def related(self, record_id: str) -> list[RelatedRecord]:
        body = await self._t.get(f"{_RECORDS}/{record_id}/related")
        return [RelatedRecord.model_validate(r) for r in body or []]

    async def duplicates(
        self, *, object_id: str, name: str | None = None, data: dict[str, Any] | None = None
    ) -> list[DuplicateCandidate]:
        body = await self._t.post(
            f"{_RECORDS}/duplicates", json={"object_id": object_id, "name": name, "data": data or {}}
        )
        return [DuplicateCandidate.model_validate(d) for d in body or []]

    async def search(self, *, q: str, limit: int = 20, object_id: str | None = None) -> list[Record]:
        body = await self._t.post(f"{_RECORDS}/search", json=_search_body(q=q, limit=limit, object_id=object_id))
        return [Record.model_validate(r) for r in body or []]

    async def update(
        self,
        record_id: str,
        *,
        name: str | None = None,
        data: dict[str, Any] | None = None,
        status: str | None = None,
        owner_member_id: str | None = None,
        unset_owner: bool = False,
        evidence: dict[str, Any] | None = None,
    ) -> Record:
        body = _update_body(
            name=name,
            data=data,
            status=status,
            owner_member_id=owner_member_id,
            unset_owner=unset_owner,
            evidence=evidence,
        )
        return Record.model_validate(await self._t.patch(f"{_RECORDS}/{record_id}", json=body))

    async def delete(self, record_id: str) -> None:
        await self._t.delete(f"{_RECORDS}/{record_id}")

    async def bulk_delete(self, record_ids: list[str]) -> BulkDeleteResult:
        body = await self._t.post(f"{_RECORDS}/bulk-delete", json={"record_ids": record_ids})
        return BulkDeleteResult.model_validate(body)

    async def restore(self, record_id: str) -> Record:
        return Record.model_validate(await self._t.post(f"{_RECORDS}/{record_id}/restore", json={}))

    async def set_references(self, record_id: str, *, attribute_id: str, target_record_ids: list[str]) -> None:
        await self._t.put(
            f"{_RECORDS}/{record_id}/references",
            json={"attribute_id": attribute_id, "target_record_ids": target_record_ids},
        )

    async def merge(self, record_id: str, *, victim_id: str) -> Record:
        body = await self._t.post(f"{_RECORDS}/{record_id}/merge", json={"victim_id": victim_id})
        return Record.model_validate(body)

    async def lists(self, record_id: str) -> list[ListMembership]:
        body = await self._t.get(f"{_RECORDS}/{record_id}/lists")
        return [ListMembership.model_validate(m) for m in body or []]
