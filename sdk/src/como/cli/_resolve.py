"""Shared slug→id resolution for the CRM CLI.

The SDK is id-first; the CLI lets a human/agent pass a friendly **slug** or
**name** and resolves it to an id by listing + scanning (the API has no
by-slug lookup). Kept in one leaf module so records/lists/objects/attributes/
views commands share it without import cycles.
"""

from __future__ import annotations

import re

import typer

from ..client import Como

# A loose UUID check — if a ref already looks like an id, skip the lookup.
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)

# Same canonicalization the backend uses to derive a list's slug, so a loosely
# typed name (plain hyphen for a stored en dash) still matches.
_SLUG_RE = re.compile(r"[^a-z0-9_-]+")
_MULTI_DASH_RE = re.compile(r"-+")


def canonical_slug(value: str) -> str:
    return _MULTI_DASH_RE.sub("-", _SLUG_RE.sub("-", value.lower()).strip("-"))


def resolve_object(client: Como, ref: str) -> str:
    """Resolve an object reference (slug or id) to its id. Exits if not found."""
    if UUID_RE.match(ref):
        return ref
    for obj in client.objects.list():
        if str(obj.id) == ref or obj.slug == ref:
            return str(obj.id)
    typer.secho(f"No object matching {ref!r}. Check the object's slug or id.", fg="red", err=True)
    raise typer.Exit(code=1)


def resolve_attribute(client: Como, object_id: str, ref: str) -> str:
    """Resolve an attribute reference (slug or id) to its id, scoped to an object."""
    if UUID_RE.match(ref):
        return ref
    for attr in client.attributes.list(object_id=object_id):
        if str(attr.id) == ref or attr.slug == ref:
            return str(attr.id)
    typer.secho(f"No attribute matching {ref!r} on that object. Check the attribute's slug or id.", fg="red", err=True)
    raise typer.Exit(code=1)


def resolve_list(client: Como, ref: str):
    """Find a list by id, slug, or (case-insensitive) name. Exits if not found."""
    ref_l = ref.lower()
    ref_canon = canonical_slug(ref)
    for lst in client.lists.list():
        name = lst.name or ""
        if str(lst.id) == ref or lst.slug == ref or name.lower() == ref_l or canonical_slug(name) == ref_canon:
            return lst
    typer.secho(f"No list matching {ref!r}. Run `como lists ls` to see them.", fg="red", err=True)
    raise typer.Exit(code=1)
