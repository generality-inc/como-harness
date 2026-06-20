"""``como crm lists view`` — create and customise CRM views (table/kanban).

A **view** is how a list (or object) renders: which columns, in what order, how
it's sorted/filtered, and — for kanban — how cards are grouped. New lists get a
default table view automatically; these commands add or customise views.

    como crm lists view ls "My targets"                       # views on a list
    como crm lists view create "My targets" --name "Hot" --type table
    como crm lists view columns <view_id> domain,name,amount  # set columns (by slug/id)
    como crm lists view sorts   <view_id> amount:desc,name:asc
    como crm lists view filter  <view_id> --json '<tree>'     # or --clear
    como crm lists view kanban  <view_id> --json '<config>'
    como crm lists view operators                             # filter operator catalog
    como crm lists view rm <view_id> [--promote <view_id>]

Resolve a list by name/slug/id (same as `como crm lists`); resolve column/sort
attributes by **slug or id**, scoped to the view's object.
"""

from __future__ import annotations

import json

import typer

from ..client import Como
from ._output import api_errors, emit
from ._resolve import resolve_attribute, resolve_list

app = typer.Typer(
    no_args_is_help=True,
    help="Create + customise list views (table/kanban, columns, sorts, filters).",
)


def _parse_json_object(raw: str, *, flag: str) -> dict:
    """Parse a JSON-object CLI argument. Exits on bad JSON / non-object."""
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        typer.secho(f"{flag} is not valid JSON: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    if not isinstance(parsed, dict):
        typer.secho(f"{flag} must be a JSON object.", fg="red", err=True)
        raise typer.Exit(code=1)
    return parsed


@app.command("ls")
def ls(
    list_ref: str = typer.Argument(..., help="List name, slug, or id."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """List the views on a list."""
    with Como() as client, api_errors():
        lst = resolve_list(client, list_ref)
        views = client.views.list_for_list(str(lst.id))
    emit(views, pretty=pretty)


@app.command("get")
def get(
    view_id: str = typer.Argument(..., help="The view's id."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Show a single view (columns + sorts + filter)."""
    with Como() as client, api_errors():
        view = client.views.get(view_id)
    emit(view, pretty=pretty)


@app.command("create")
def create(
    list_ref: str = typer.Argument(..., help="List name, slug, or id to create the view on."),
    name: str = typer.Option(..., "--name", help="The view's display name."),
    view_type: str = typer.Option("table", "--type", help="View type: table or kanban."),
    kanban_config: str | None = typer.Option(
        None, "--kanban-config", help="Kanban layout as a JSON object (required when --type kanban)."
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Create a view on a list."""
    if view_type not in ("table", "kanban"):
        typer.secho("--type must be 'table' or 'kanban'.", fg="red", err=True)
        raise typer.Exit(code=1)
    config = None
    if view_type == "kanban":
        if kanban_config is None:
            typer.secho("--kanban-config (JSON) is required for a kanban view.", fg="red", err=True)
            raise typer.Exit(code=1)
        config = _parse_json_object(kanban_config, flag="--kanban-config")
    with Como() as client, api_errors():
        lst = resolve_list(client, list_ref)
        view = client.views.create(list_id=str(lst.id), name=name, view_type=view_type, kanban_config=config)
    emit(view, pretty=pretty)


@app.command("update")
def update(
    view_id: str = typer.Argument(..., help="The view's id."),
    name: str | None = typer.Option(None, "--name", help="New display name."),
    default: bool = typer.Option(False, "--default", help="Make this the list's default view."),
    view_type: str | None = typer.Option(None, "--type", help="Convert to 'table' or 'kanban'."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Rename a view, set it as default, or convert its type."""
    if view_type is not None and view_type not in ("table", "kanban"):
        typer.secho("--type must be 'table' or 'kanban'.", fg="red", err=True)
        raise typer.Exit(code=1)
    if name is None and not default and view_type is None:
        typer.secho("Nothing to update — pass --name, --default, and/or --type.", fg="red", err=True)
        raise typer.Exit(code=1)
    with Como() as client, api_errors():
        view = client.views.update(view_id, name=name, is_default=True if default else None, view_type=view_type)
    emit(view, pretty=pretty)


@app.command("columns")
def columns(
    view_id: str = typer.Argument(..., help="The view's id."),
    attributes: str = typer.Argument(..., help="Ordered attribute slugs or ids, comma-separated."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Set the view's columns (full ordered list — slugs or ids)."""
    refs = [x.strip() for x in attributes.split(",") if x.strip()]
    if not refs:
        typer.secho("No attributes given.", fg="red", err=True)
        raise typer.Exit(code=1)
    with Como() as client, api_errors():
        view = client.views.get(view_id)
        object_id = str(view.object_id)
        cols = [{"attribute_id": resolve_attribute(client, object_id, r)} for r in refs]
        updated = client.views.set_columns(view_id, columns=cols)
    emit(updated, pretty=pretty)


@app.command("sorts")
def sorts(
    view_id: str = typer.Argument(..., help="The view's id."),
    spec: str = typer.Argument(..., help="Sort rules 'attr:asc,attr:desc' (direction defaults to asc)."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Set the view's sort order (slugs or ids; 'attr:asc' / 'attr:desc')."""
    pairs: list[tuple[str, str]] = []
    for tok in spec.split(","):
        tok = tok.strip()
        if not tok:
            continue
        ref, _, direction = tok.partition(":")
        direction = direction or "asc"
        if direction not in ("asc", "desc"):
            typer.secho(f"Direction in {tok!r} must be 'asc' or 'desc'.", fg="red", err=True)
            raise typer.Exit(code=1)
        pairs.append((ref.strip(), direction))
    if not pairs:
        typer.secho("No sort rules given.", fg="red", err=True)
        raise typer.Exit(code=1)
    with Como() as client, api_errors():
        view = client.views.get(view_id)
        object_id = str(view.object_id)
        rules = [{"attribute_id": resolve_attribute(client, object_id, ref), "direction": d} for ref, d in pairs]
        updated = client.views.set_sorts(view_id, sorts=rules)
    emit(updated, pretty=pretty)


@app.command("filter")
def filter_(
    view_id: str = typer.Argument(..., help="The view's id."),
    filter_json: str | None = typer.Option(None, "--json", help="Filter tree as a JSON object."),
    clear: bool = typer.Option(False, "--clear", help="Clear the view's filter."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Set (or clear) the view's filter tree."""
    if clear == (filter_json is not None):
        typer.secho("Pass exactly one of --json or --clear.", fg="red", err=True)
        raise typer.Exit(code=1)
    tree = None if clear else _parse_json_object(filter_json or "", flag="--json")
    with Como() as client, api_errors():
        updated = client.views.set_filter(view_id, filter=tree)
    emit(updated, pretty=pretty)


@app.command("kanban")
def kanban(
    view_id: str = typer.Argument(..., help="The view's id."),
    config_json: str = typer.Option(..., "--json", help="Kanban config as a JSON object."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Set a kanban view's layout config."""
    config = _parse_json_object(config_json, flag="--json")
    with Como() as client, api_errors():
        updated = client.views.set_kanban_config(view_id, kanban_config=config)
    emit(updated, pretty=pretty)


@app.command("rm")
def rm(
    view_id: str = typer.Argument(..., help="The view's id."),
    promote: str | None = typer.Option(
        None, "--promote", help="If deleting the default view, the view id to promote to default."
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Delete a view."""
    with Como() as client, api_errors():
        client.views.delete(view_id, promote_to=promote)
    emit({"deleted": True, "view_id": view_id}, pretty=pretty)


@app.command("operators")
def operators(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Print the filter operator catalog (operators available per attribute type)."""
    with Como() as client, api_errors():
        ops = client.views.operators()
    emit(ops, pretty=pretty)
