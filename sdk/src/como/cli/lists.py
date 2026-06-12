"""``como lists`` — read and build CRM lists on the como platform.

A **list** is a curated container of records (companies / people) — e.g. a
target account list. These commands read a list's contents and add records to
it, authenticated by your ``como_live_`` key (which acts as your own workspace
member, with your real permissions).

    como lists ls                      # all lists in your workspace (name + id)
    como lists records "US - Seed/A/B"  # the rows in a list (by name or id)
    como lists create "My targets" --object <object_id>
    como lists add <list> <record_id>  # add a record to a list

Resolve a list by **name** (case-insensitive), **slug**, or **id** — most
commands accept any of the three.
"""

from __future__ import annotations

import json
import re

import httpx
import typer

from .._config import DEFAULT_TIMEOUT, resolve_api_key, resolve_base_url

# Same canonicalization the backend uses to derive a list's slug — lets a caller
# match a list by a loosely-typed name (e.g. a plain hyphen for a stored en dash).
_SLUG_RE = re.compile(r"[^a-z0-9_-]+")
_MULTI_DASH_RE = re.compile(r"-+")


def _canonical_slug(value: str) -> str:
    return _MULTI_DASH_RE.sub("-", _SLUG_RE.sub("-", value.lower()).strip("-"))


app = typer.Typer(
    no_args_is_help=True,
    help="Read + build CRM lists (target account lists, etc.).",
)

_BASE_PATH = "/v1/crm/lists"


def _client() -> tuple[str, dict[str, str]]:
    base, key = resolve_base_url(None), resolve_api_key(None)
    return base, {"Authorization": f"Bearer {key}"}


def _get(path: str) -> object:
    base, headers = _client()
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as c:
            r = c.get(f"{base}{path}", headers=headers)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as exc:
        typer.secho(f"Request failed ({exc.response.status_code}): {exc.response.text}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    except httpx.HTTPError as exc:
        typer.secho(f"Request failed: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc


def _post(path: str, body: dict) -> object:
    base, headers = _client()
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as c:
            r = c.post(f"{base}{path}", headers=headers, json=body)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as exc:
        typer.secho(f"Request failed ({exc.response.status_code}): {exc.response.text}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    except httpx.HTTPError as exc:
        typer.secho(f"Request failed: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc


def _resolve_list(ref: str) -> dict:
    """Find a list by id, slug, or (case-insensitive) name. Exits if not found."""
    lists = _get(_BASE_PATH)
    assert isinstance(lists, list)
    ref_l = ref.lower()
    ref_canon = _canonical_slug(ref)
    for lst in lists:
        if (
            str(lst.get("id")) == ref
            or lst.get("slug") == ref
            or str(lst.get("name", "")).lower() == ref_l
            # Loose name match: canonicalize the input the same way slugs are
            # derived, so "US - Seed/A/B > 20M" finds slug "us-seed-a-b-20m"
            # even when the typed dash/punctuation differs from the stored name.
            or _canonical_slug(str(lst.get("name", ""))) == ref_canon
        ):
            return lst
    typer.secho(f"No list matching {ref!r}. Run `como lists ls` to see them.", fg="red", err=True)
    raise typer.Exit(code=1)


@app.command("ls")
def ls(
    json_out: bool = typer.Option(False, "--json", help="Raw JSON instead of a table."),
) -> None:
    """List the lists in your workspace."""
    lists = _get(_BASE_PATH)
    assert isinstance(lists, list)
    if json_out:
        typer.echo(json.dumps(lists, indent=2))
        return
    if not lists:
        typer.secho("No lists in this workspace yet.", fg="yellow")
        return
    name_w = max((len(str(lst.get("name", ""))) for lst in lists), default=4)
    typer.echo(f"{'NAME'.ljust(name_w)}  {'SLUG'.ljust(24)}  ID")
    for lst in lists:
        name = str(lst.get("name", "")).ljust(name_w)
        slug = str(lst.get("slug", "")).ljust(24)
        typer.echo(f"{name}  {slug}  {lst.get('id')}")


@app.command("get")
def get(ref: str = typer.Argument(..., help="List name, slug, or id.")) -> None:
    """Show a single list's metadata as JSON."""
    typer.echo(json.dumps(_resolve_list(ref), indent=2))


@app.command("records")
def records(
    ref: str = typer.Argument(..., help="List name, slug, or id."),
    json_out: bool = typer.Option(False, "--json", help="Raw JSON instead of a table."),
) -> None:
    """Read the rows (records) in a list — name + status + data."""
    lst = _resolve_list(ref)
    rows = _get(f"{_BASE_PATH}/{lst['id']}/records")
    assert isinstance(rows, list)
    if json_out:
        typer.echo(json.dumps(rows, indent=2))
        return
    if not rows:
        typer.secho(f"List {lst['name']!r} is empty.", fg="yellow")
        return
    typer.secho(f"{lst['name']}  ({len(rows)} records)", bold=True)
    name_w = max((len(str(r.get("name") or "—")) for r in rows), default=4)
    for r in rows:
        name = str(r.get("name") or "—").ljust(name_w)
        status = f"  [{r['status']}]" if r.get("status") else ""
        typer.echo(f"{name}  {r.get('id')}{status}")


@app.command("entries")
def entries(
    ref: str = typer.Argument(..., help="List name, slug, or id."),
) -> None:
    """Raw list entries (record_id + list-scoped data) as JSON."""
    lst = _resolve_list(ref)
    typer.echo(json.dumps(_get(f"{_BASE_PATH}/{lst['id']}/entries"), indent=2))


@app.command("create")
def create(
    name: str = typer.Argument(..., help="The list's display name."),
    object_id: str = typer.Option(..., "--object", help="Parent object id (e.g. the Companies object)."),
    emoji: str | None = typer.Option(None, "--emoji", help="Optional emoji icon."),
) -> None:
    """Create a new list. Prints it as JSON."""
    body: dict = {"parent_object_id": object_id, "name": name}
    if emoji:
        body["emoji"] = emoji
    typer.echo(json.dumps(_post(_BASE_PATH, body), indent=2))


@app.command("add")
def add(
    ref: str = typer.Argument(..., help="List name, slug, or id."),
    record_ids: str = typer.Argument(..., help="A record id, or comma-separated ids."),
) -> None:
    """Add record(s) to a list."""
    lst = _resolve_list(ref)
    ids = [x.strip() for x in record_ids.split(",") if x.strip()]
    if not ids:
        typer.secho("No record ids given.", fg="red", err=True)
        raise typer.Exit(code=1)
    if len(ids) == 1:
        _post(f"{_BASE_PATH}/{lst['id']}/entries", {"record_id": ids[0]})
        typer.secho(f"Added 1 record to {lst['name']!r}.", fg="green")
    else:
        res = _post(f"{_BASE_PATH}/{lst['id']}/entries/bulk", {"record_ids": ids})
        added = res.get("added_count") if isinstance(res, dict) else len(ids)
        typer.secho(f"Added {added} records to {lst['name']!r}.", fg="green")
