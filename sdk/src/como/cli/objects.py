"""``como crm objects`` — the CRM object *types* (Companies, People, custom types).

Read the catalog, or create/rename/delete object types. Authenticated by your
``como_live_`` key (writes need the ``crm:write`` scope).

    como crm objects ls
    como crm objects create --slug investors --singular Investor --plural Investors
    como crm objects update investors --plural "Investors & Funds"
    como crm objects rm investors
"""

from __future__ import annotations

import typer

from ..client import Como
from ._output import api_errors, emit
from ._resolve import resolve_object

app = typer.Typer(no_args_is_help=True, help="CRM object types (Companies, People, custom objects).")


@app.command("ls")
def ls(pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output.")) -> None:
    """List the object types in your workspace."""
    with Como() as client, api_errors():
        objects = client.objects.list()
    emit(objects, pretty=pretty)


@app.command("create")
def create(
    slug: str = typer.Option(..., "--slug", help="Object slug (e.g. 'investors')."),
    singular: str = typer.Option(..., "--singular", help="Singular name (e.g. 'Investor')."),
    plural: str = typer.Option(..., "--plural", help="Plural name (e.g. 'Investors')."),
    icon: str | None = typer.Option(None, "--icon"),
    color: str | None = typer.Option(None, "--color"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Create a custom object type."""
    with Como() as client, api_errors():
        obj = client.objects.create(slug=slug, singular_name=singular, plural_name=plural, icon=icon, color=color)
    emit(obj, pretty=pretty)


@app.command("update")
def update(
    ref: str = typer.Argument(..., help="Object slug or id."),
    singular: str | None = typer.Option(None, "--singular"),
    plural: str | None = typer.Option(None, "--plural"),
    icon: str | None = typer.Option(None, "--icon"),
    color: str | None = typer.Option(None, "--color"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Update an object type's names / icon / color."""
    if singular is None and plural is None and icon is None and color is None:
        typer.secho("Nothing to update — pass --singular/--plural/--icon/--color.", fg="red", err=True)
        raise typer.Exit(code=1)
    with Como() as client, api_errors():
        object_id = resolve_object(client, ref)
        obj = client.objects.update(object_id, singular_name=singular, plural_name=plural, icon=icon, color=color)
    emit(obj, pretty=pretty)


@app.command("rm")
def rm(
    ref: str = typer.Argument(..., help="Object slug or id."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Delete a custom object type."""
    with Como() as client, api_errors():
        object_id = resolve_object(client, ref)
        client.objects.delete(object_id)
    emit({"deleted": True, "object_id": object_id}, pretty=pretty)
