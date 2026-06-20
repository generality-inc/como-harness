"""CRM models — first-party Como objects (records, lists, the catalog).

Unlike the LinkedIn ghost models (``_common.BaseModel``, camelCase wire format),
the CRM API speaks **snake_case** on the wire, so these inherit a plain base
with NO alias generator. Everything is optional with ``extra="allow"`` — a
record's ``data`` is a per-workspace, schema-less bag, and the catalog grows
over time, so we never want validation to drop or reject an unknown field.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel as _PydanticBase
from pydantic import ConfigDict


class CrmBaseModel(_PydanticBase):
    """Base for CRM models: snake_case fields (no camelCase aliasing), extras kept."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Record(CrmBaseModel):
    """A single row of a CRM object (a Company, a Person, …). ``data`` holds the
    record's attribute values keyed by attribute slug."""

    id: str | None = None
    object_id: str | None = None
    workspace_id: str | None = None
    name: str | None = None
    owner_member_id: str | None = None
    status: str | None = None
    data: dict[str, Any] = {}
    created_by_member_id: str | None = None
    created_via: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None


class UpsertResult(CrmBaseModel):
    """Outcome of an idempotent upsert: the record plus whether it was created
    and which fields changed."""

    record: Record | None = None
    created: bool | None = None
    changed_fields: list[str] = []


class BulkDeleteResult(CrmBaseModel):
    deleted_count: int | None = None


class CrmObject(CrmBaseModel):
    """A CRM object type in the catalog (Companies, People, …)."""

    id: str | None = None
    workspace_id: str | None = None
    slug: str | None = None
    # ``name`` is kept for the lightweight resolution path; the objects API
    # itself returns singular/plural rather than a single ``name``.
    name: str | None = None
    singular_name: str | None = None
    plural_name: str | None = None
    icon: str | None = None
    color: str | None = None
    is_system: bool | None = None
    is_restricted: bool | None = None
    record_label_attribute_id: str | None = None
    record_image_attribute_id: str | None = None
    created_at: str | None = None


class AttributeOption(CrmBaseModel):
    """A choice on a select/multi_select/status attribute."""

    id: str | None = None
    attribute_id: str | None = None
    workspace_id: str | None = None
    slug: str | None = None
    label: str | None = None
    color: str | None = None
    position: int | None = None
    is_archived: bool | None = None


class Attribute(CrmBaseModel):
    """A column/attribute on a CRM object (or, when ``list_id`` is set, a
    list-scoped column whose values live in a list entry's ``data``)."""

    id: str | None = None
    workspace_id: str | None = None
    slug: str | None = None
    object_id: str | None = None
    list_id: str | None = None
    name: str | None = None
    description: str | None = None
    type: str | None = None
    config: dict[str, Any] = {}
    is_required: bool | None = None
    is_unique: bool | None = None
    is_system: bool | None = None
    is_system_value: bool | None = None
    is_archived: bool | None = None
    default_value: dict[str, Any] | None = None
    position: int | None = None
    # Relationship/reference metadata (set when type is record_reference/relationship).
    target_object_id: str | None = None
    cardinality: str | None = None
    inverse_attribute_id: str | None = None
    options: list[AttributeOption] = []
    created_at: str | None = None


class RelationshipAttributePair(CrmBaseModel):
    """The two paired sides created by a relationship attribute."""

    left: Attribute | None = None
    right: Attribute | None = None


class RecordList(CrmBaseModel):
    """A curated container of records (a target account list, etc.)."""

    id: str | None = None
    workspace_id: str | None = None
    slug: str | None = None
    name: str | None = None
    emoji: str | None = None
    parent_object_id: str | None = None
    position: int | None = None
    created_by_member_id: str | None = None
    created_at: str | None = None


class ListMembership(CrmBaseModel):
    """One of the lists a record belongs to, with that membership's list-scoped data."""

    list_id: str | None = None
    list_name: str | None = None
    list_emoji: str | None = None
    parent_object_id: str | None = None
    entry_data: dict[str, Any] = {}
    added_at: str | None = None


class ListEntriesResult(CrmBaseModel):
    """Outcome of a bulk add-to-list."""

    added_count: int | None = None


class ListEntriesRemovedResult(CrmBaseModel):
    """Outcome of a bulk remove-from-list."""

    removed_count: int | None = None


class ListEntry(CrmBaseModel):
    """A record's membership row in a list — carries the list-scoped ``data``."""

    id: str | None = None
    workspace_id: str | None = None
    list_id: str | None = None
    record_id: str | None = None
    position: int | None = None
    data: dict[str, Any] = {}
    created_at: str | None = None


class RecordRow(CrmBaseModel):
    """A row as it appears *inside a list*: the record's own ``data`` plus the
    list-scoped ``list_data`` (the entry's per-list column values)."""

    id: str | None = None
    name: str | None = None
    status: str | None = None
    data: dict[str, Any] = {}
    list_data: dict[str, Any] = {}


class RelatedRecord(CrmBaseModel):
    """An edge touching a record via a relationship/reference attribute."""

    record_id: str | None = None
    attribute_id: str | None = None
    direction: str | None = None


class DuplicateCandidate(CrmBaseModel):
    """A possible duplicate surfaced before an insert."""

    id: str | None = None
    name: str | None = None
    data: dict[str, Any] = {}
    created_at: str | None = None


class ReorderResult(CrmBaseModel):
    """Outcome of a reorder (lists or entries)."""

    updated_count: int | None = None
