"""``como crm lists`` — read and build CRM lists on the como platform.

A **list** is a curated container of records (companies / people) — e.g. a
target account list. Thin wrappers over the SDK client (``Como().lists``),
authenticated by your ``como_live_`` key.

    como crm lists ls                      # all lists in your workspace (JSON; --table for a table)
    como crm lists records "US - Seed/A/B"  # the rows in a list (by name or id)
    como crm lists create "My targets" --object companies
    como crm lists add <list> <record_id>  # add a record to a list

A brand-new list has **no view** until you add one — same as the dashboard's
"Start with a view" step (see `como crm lists view create`). Resolve a list by
**name** (case-insensitive), **slug**, or **id**.

Output contract: every command prints JSON to stdout (``--pretty`` for readable);
``ls``/``records`` also accept ``--table`` for a human table.
"""

from __future__ import annotations

import json

import typer

from ..client import Como
from ._output import api_errors, emit

from ._resolve import resolve_list, resolve_object  # isort: skip

app = typer.Typer(
    no_args_is_help=True,
    help="Read + build CRM lists (target account lists, etc.).",
)


def _parse_data(raw: str) -> dict:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        typer.secho(f"--data is not valid JSON: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    if not isinstance(parsed, dict):
        typer.secho("--data must be a JSON object.", fg="red", err=True)
        raise typer.Exit(code=1)
    return parsed


def _ids(raw: str) -> list[str]:
    ids = [x.strip() for x in raw.split(",") if x.strip()]
    if not ids:
        typer.secho("No ids given.", fg="red", err=True)
        raise typer.Exit(code=1)
    return ids


@app.command("ls")
def ls(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
    table: bool = typer.Option(False, "--table", help="Render a human table instead of JSON."),
) -> None:
    """List the lists in your workspace."""
    with Como() as client, api_errors():
        lists = client.lists.list()
    if not table:
        emit(lists, pretty=pretty)
        return
    name_w = max((len(lst.name or "") for lst in lists), default=4)
    typer.echo(f"{'NAME'.ljust(name_w)}  {'SLUG'.ljust(24)}  ID")
    for lst in lists:
        typer.echo(f"{(lst.name or '').ljust(name_w)}  {(lst.slug or '').ljust(24)}  {lst.id}")


@app.command("get")
def get(
    ref: str = typer.Argument(..., help="List name, slug, or id."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Show a single list's metadata as JSON."""
    with Como() as client, api_errors():
        lst = resolve_list(client, ref)
    emit(lst, pretty=pretty)


@app.command("records")
def records(
    ref: str = typer.Argument(..., help="List name, slug, or id."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
    table: bool = typer.Option(False, "--table", help="Render a human table instead of JSON."),
) -> None:
    """Read the rows (records) in a list — id, name, status, data, list_data."""
    with Como() as client, api_errors():
        lst = resolve_list(client, ref)
        rows = client.lists.records(str(lst.id))
    if not table:
        emit(rows, pretty=pretty)
        return
    typer.secho(f"{lst.name}  ({len(rows)} records)", bold=True)
    name_w = max((len(r.name or "—") for r in rows), default=4)
    for r in rows:
        status = f"  [{r.status}]" if r.status else ""
        typer.echo(f"{(r.name or '—').ljust(name_w)}  {r.id}{status}")


@app.command("entries")
def entries(
    ref: str = typer.Argument(..., help="List name, slug, or id."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Raw list entries (record_id + list-scoped data) as JSON."""
    with Como() as client, api_errors():
        lst = resolve_list(client, ref)
        rows = client.lists.entries(str(lst.id))
    emit(rows, pretty=pretty)


@app.command("create")
def create(
    name: str = typer.Argument(..., help="The list's display name."),
    object_ref: str = typer.Option(..., "--object", help="Parent object slug or id (e.g. 'companies')."),
    emoji: str | None = typer.Option(None, "--emoji", help="Optional emoji icon."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Create a new list (add a view with `lists view create`). Prints it as JSON."""
    with Como() as client, api_errors():
        object_id = resolve_object(client, object_ref)
        lst = client.lists.create(parent_object_id=object_id, name=name, emoji=emoji)
    emit(lst, pretty=pretty)


@app.command("update")
def update(
    ref: str = typer.Argument(..., help="List name, slug, or id."),
    name: str | None = typer.Option(None, "--name", help="New display name."),
    emoji: str | None = typer.Option(None, "--emoji", help="New emoji icon."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Rename a list / change its emoji."""
    if name is None and emoji is None:
        typer.secho("Nothing to update — pass --name and/or --emoji.", fg="red", err=True)
        raise typer.Exit(code=1)
    with Como() as client, api_errors():
        lst = resolve_list(client, ref)
        updated = client.lists.update(str(lst.id), name=name, emoji=emoji)
    emit(updated, pretty=pretty)


@app.command("rm")
def rm(
    ref: str = typer.Argument(..., help="List name, slug, or id."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Delete a list (soft-delete; its entries/views/attributes go with it)."""
    with Como() as client, api_errors():
        lst = resolve_list(client, ref)
        client.lists.delete(str(lst.id))
    emit({"deleted": True, "list_id": str(lst.id)}, pretty=pretty)


@app.command("duplicate")
def duplicate(
    ref: str = typer.Argument(..., help="List name, slug, or id."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Clone a list's shell + attributes + views (no entries). Prints the new list."""
    with Como() as client, api_errors():
        lst = resolve_list(client, ref)
        clone = client.lists.duplicate(str(lst.id))
    emit(clone, pretty=pretty)


@app.command("set-parent")
def set_parent(
    ref: str = typer.Argument(..., help="List name, slug, or id."),
    object_ref: str = typer.Option(..., "--object", help="New parent object slug or id."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Move a list to a different parent object (entries are kept)."""
    with Como() as client, api_errors():
        lst = resolve_list(client, ref)
        object_id = resolve_object(client, object_ref)
        updated = client.lists.change_parent_object(str(lst.id), parent_object_id=object_id)
    emit(updated, pretty=pretty)


@app.command("reorder")
def reorder(
    list_ids: str = typer.Argument(..., help="List ids in the desired sidebar order, comma-separated."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Reorder the lists in the sidebar (full ordered id list)."""
    ids = _ids(list_ids)
    with Como() as client, api_errors():
        res = client.lists.reorder(ordered_list_ids=ids)
    emit(res, pretty=pretty)


@app.command("add")
def add(
    ref: str = typer.Argument(..., help="List name, slug, or id."),
    record_ids: str = typer.Argument(..., help="A record id, or comma-separated ids."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Add record(s) to a list."""
    ids = _ids(record_ids)
    with Como() as client, api_errors():
        lst = resolve_list(client, ref)
        if len(ids) == 1:
            client.lists.add_entry(str(lst.id), record_id=ids[0])
            added = 1
        else:
            res = client.lists.add_entries(str(lst.id), record_ids=ids)
            added = res.added_count if res.added_count is not None else len(ids)
    emit({"added_count": added, "list_id": str(lst.id), "record_ids": ids}, pretty=pretty)


@app.command("remove")
def remove(
    ref: str = typer.Argument(..., help="List name, slug, or id."),
    record_ids: str = typer.Argument(..., help="A record id, or comma-separated ids, to remove."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Remove record(s) from a list (the inverse of `add`)."""
    ids = _ids(record_ids)
    with Como() as client, api_errors():
        lst = resolve_list(client, ref)
        if len(ids) == 1:
            client.lists.remove_entry(str(lst.id), record_id=ids[0])
            removed = 1
        else:
            res = client.lists.remove_entries(str(lst.id), record_ids=ids)
            removed = res.removed_count if res.removed_count is not None else len(ids)
    emit({"removed_count": removed, "list_id": str(lst.id), "record_ids": ids}, pretty=pretty)


@app.command("reorder-entries")
def reorder_entries(
    ref: str = typer.Argument(..., help="List name, slug, or id."),
    record_ids: str = typer.Argument(..., help="Record ids in the desired order, comma-separated."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Reorder the records within a list (full ordered id list)."""
    ids = _ids(record_ids)
    with Como() as client, api_errors():
        lst = resolve_list(client, ref)
        res = client.lists.reorder_entries(str(lst.id), ordered_record_ids=ids)
    emit(res, pretty=pretty)


@app.command("entry-data")
def entry_data(
    ref: str = typer.Argument(..., help="List name, slug, or id."),
    record_id: str = typer.Argument(..., help="The record's id (must be in the list)."),
    data: str = typer.Option(..., "--data", help="List-scoped column values as a JSON object (merged)."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Set a record's list-scoped column values (the entry's `list_data`); merges."""
    parsed = _parse_data(data)
    with Como() as client, api_errors():
        lst = resolve_list(client, ref)
        entry = client.lists.update_entry_data(str(lst.id), record_id=record_id, data=parsed)
    emit(entry, pretty=pretty)


# --- list-scoped attributes (the entry_data columns) -------------------------
attrs_app = typer.Typer(no_args_is_help=True, help="List-scoped columns (the `list_data` fields on a list).")
app.add_typer(attrs_app, name="attrs")


@attrs_app.command("ls")
def attrs_ls(
    ref: str = typer.Argument(..., help="List name, slug, or id."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """List a list's own (list-scoped) attributes."""
    with Como() as client, api_errors():
        lst = resolve_list(client, ref)
        attributes = client.lists.attributes(str(lst.id))
    emit(attributes, pretty=pretty)


@attrs_app.command("create")
def attrs_create(
    ref: str = typer.Argument(..., help="List name, slug, or id."),
    slug: str = typer.Option(..., "--slug", help="Attribute slug (e.g. 'stage')."),
    name: str = typer.Option(..., "--name", help="Display name (e.g. 'Stage')."),
    type: str = typer.Option("text", "--type", help="Attribute type (text/number/select/status/date/…)."),
    description: str | None = typer.Option(None, "--description"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Create a list-scoped column. Its values are set per-record with `entry-data`."""
    with Como() as client, api_errors():
        lst = resolve_list(client, ref)
        attr = client.lists.create_attribute(str(lst.id), slug=slug, name=name, type=type, description=description)
    emit(attr, pretty=pretty)
