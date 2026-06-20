"""CRM attributes (catalog) resource — the columns on an object, their options,
and paired relationships. Wraps ``/v1/crm/attributes``.
"""

from __future__ import annotations

from typing import Any

from como_core.crm import Attribute, AttributeOption, RelationshipAttributePair

from .._params import clean_params
from ._base import AsyncResource, SyncResource

_BASE = "/v1/crm/attributes"


def _create_body(
    *,
    object_id: str,
    slug: str,
    name: str,
    type: str,
    description: str | None,
    config: dict | None,
    is_required: bool,
    is_unique: bool,
) -> dict:
    body: dict[str, Any] = {
        "object_id": object_id,
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


def _update_body(
    *,
    name: str | None,
    description: str | None,
    config: dict | None,
    is_required: bool | None,
    is_unique: bool | None,
    default_value: Any | None,
) -> dict:
    body: dict[str, Any] = {}
    for k, v in (
        ("name", name),
        ("description", description),
        ("config", config),
        ("is_required", is_required),
        ("is_unique", is_unique),
        ("default_value", default_value),
    ):
        if v is not None:
            body[k] = v
    return body


def _option_body(*, slug: str, label: str, color: str | None) -> dict:
    body: dict[str, Any] = {"slug": slug, "label": label}
    if color is not None:
        body["color"] = color
    return body


class AttributesResource(SyncResource):
    def list(self, *, object_id: str) -> list[Attribute]:
        body = self._t.get(_BASE, params=clean_params({"object_id": object_id}))
        return [Attribute.model_validate(a) for a in body or []]

    def create(
        self,
        *,
        object_id: str,
        slug: str,
        name: str,
        type: str,
        description: str | None = None,
        config: dict | None = None,
        is_required: bool = False,
        is_unique: bool = False,
    ) -> Attribute:
        body = _create_body(
            object_id=object_id,
            slug=slug,
            name=name,
            type=type,
            description=description,
            config=config,
            is_required=is_required,
            is_unique=is_unique,
        )
        return Attribute.model_validate(self._t.post(_BASE, json=body))

    def create_relationship(
        self,
        *,
        left_object_id: str,
        left_slug: str,
        left_name: str,
        left_cardinality: str,
        right_object_id: str,
        right_slug: str,
        right_name: str,
        right_cardinality: str,
    ) -> RelationshipAttributePair:
        body = {
            "left_object_id": left_object_id,
            "left_slug": left_slug,
            "left_name": left_name,
            "left_cardinality": left_cardinality,
            "right_object_id": right_object_id,
            "right_slug": right_slug,
            "right_name": right_name,
            "right_cardinality": right_cardinality,
        }
        return RelationshipAttributePair.model_validate(self._t.post(f"{_BASE}/relationships", json=body))

    def update(
        self,
        attribute_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        config: dict | None = None,
        is_required: bool | None = None,
        is_unique: bool | None = None,
        default_value: Any | None = None,
    ) -> Attribute:
        body = _update_body(
            name=name,
            description=description,
            config=config,
            is_required=is_required,
            is_unique=is_unique,
            default_value=default_value,
        )
        return Attribute.model_validate(self._t.patch(f"{_BASE}/{attribute_id}", json=body))

    def archive(self, attribute_id: str) -> None:
        self._t.delete(f"{_BASE}/{attribute_id}")

    def duplicate(self, attribute_id: str) -> Attribute:
        return Attribute.model_validate(self._t.post(f"{_BASE}/{attribute_id}/duplicate", json={}))

    def reorder(self, *, object_id: str, ordered_attribute_ids: list[str]) -> list[Attribute]:
        body = {"object_id": object_id, "ordered_attribute_ids": ordered_attribute_ids}
        rows = self._t.patch(f"{_BASE}/positions", json=body)
        return [Attribute.model_validate(a) for a in rows or []]

    def add_option(self, attribute_id: str, *, slug: str, label: str, color: str | None = None) -> AttributeOption:
        body = _option_body(slug=slug, label=label, color=color)
        return AttributeOption.model_validate(self._t.post(f"{_BASE}/{attribute_id}/options", json=body))

    def update_option(
        self, attribute_id: str, option_id: str, *, label: str | None = None, color: str | None = None
    ) -> AttributeOption:
        body: dict[str, Any] = {}
        if label is not None:
            body["label"] = label
        if color is not None:
            body["color"] = color
        return AttributeOption.model_validate(self._t.patch(f"{_BASE}/{attribute_id}/options/{option_id}", json=body))

    def archive_option(self, attribute_id: str, option_id: str) -> None:
        self._t.delete(f"{_BASE}/{attribute_id}/options/{option_id}")


class AsyncAttributesResource(AsyncResource):
    async def list(self, *, object_id: str) -> list[Attribute]:
        body = await self._t.get(_BASE, params=clean_params({"object_id": object_id}))
        return [Attribute.model_validate(a) for a in body or []]

    async def create(
        self,
        *,
        object_id: str,
        slug: str,
        name: str,
        type: str,
        description: str | None = None,
        config: dict | None = None,
        is_required: bool = False,
        is_unique: bool = False,
    ) -> Attribute:
        body = _create_body(
            object_id=object_id,
            slug=slug,
            name=name,
            type=type,
            description=description,
            config=config,
            is_required=is_required,
            is_unique=is_unique,
        )
        return Attribute.model_validate(await self._t.post(_BASE, json=body))

    async def create_relationship(
        self,
        *,
        left_object_id: str,
        left_slug: str,
        left_name: str,
        left_cardinality: str,
        right_object_id: str,
        right_slug: str,
        right_name: str,
        right_cardinality: str,
    ) -> RelationshipAttributePair:
        body = {
            "left_object_id": left_object_id,
            "left_slug": left_slug,
            "left_name": left_name,
            "left_cardinality": left_cardinality,
            "right_object_id": right_object_id,
            "right_slug": right_slug,
            "right_name": right_name,
            "right_cardinality": right_cardinality,
        }
        return RelationshipAttributePair.model_validate(await self._t.post(f"{_BASE}/relationships", json=body))

    async def update(
        self,
        attribute_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        config: dict | None = None,
        is_required: bool | None = None,
        is_unique: bool | None = None,
        default_value: Any | None = None,
    ) -> Attribute:
        body = _update_body(
            name=name,
            description=description,
            config=config,
            is_required=is_required,
            is_unique=is_unique,
            default_value=default_value,
        )
        return Attribute.model_validate(await self._t.patch(f"{_BASE}/{attribute_id}", json=body))

    async def archive(self, attribute_id: str) -> None:
        await self._t.delete(f"{_BASE}/{attribute_id}")

    async def duplicate(self, attribute_id: str) -> Attribute:
        return Attribute.model_validate(await self._t.post(f"{_BASE}/{attribute_id}/duplicate", json={}))

    async def reorder(self, *, object_id: str, ordered_attribute_ids: list[str]) -> list[Attribute]:
        body = {"object_id": object_id, "ordered_attribute_ids": ordered_attribute_ids}
        rows = await self._t.patch(f"{_BASE}/positions", json=body)
        return [Attribute.model_validate(a) for a in rows or []]

    async def add_option(
        self, attribute_id: str, *, slug: str, label: str, color: str | None = None
    ) -> AttributeOption:
        body = _option_body(slug=slug, label=label, color=color)
        return AttributeOption.model_validate(await self._t.post(f"{_BASE}/{attribute_id}/options", json=body))

    async def update_option(
        self, attribute_id: str, option_id: str, *, label: str | None = None, color: str | None = None
    ) -> AttributeOption:
        body: dict[str, Any] = {}
        if label is not None:
            body["label"] = label
        if color is not None:
            body["color"] = color
        return AttributeOption.model_validate(
            await self._t.patch(f"{_BASE}/{attribute_id}/options/{option_id}", json=body)
        )

    async def archive_option(self, attribute_id: str, option_id: str) -> None:
        await self._t.delete(f"{_BASE}/{attribute_id}/options/{option_id}")
