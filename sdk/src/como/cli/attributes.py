"""``como crm attributes`` — the columns on a CRM object, their options, and
paired relationships. Authenticated by your ``como_live_`` key (writes need
``crm:write``).

    como crm attributes ls --object companies
    como crm attributes create --object companies --slug tier --name Tier --type select
    como crm attributes option add <attr_id> --slug lead --label Lead --color blue
    como crm attributes update <attr_id> --name "ICP Tier"
    como crm attributes rm <attr_id>
    como crm attributes reorder --object companies <attr_id,attr_id,...>
    como crm attributes bind <attr> --agent <agent_id> --output-field summary
    como crm attributes unbind <attr>
    como crm attributes duplicate <attr>
    como crm attributes enrichment set <attr> --source company --field employee_count
    como crm attributes enrichment clear <attr>
    como crm attributes relationship --left-object companies --left-slug investors --left-name Investors \\
        --left-cardinality many --right-object investors --right-slug portfolio \\
        --right-name Portfolio --right-cardinality many
"""

from __future__ import annotations

import typer

from ..client import Como
from ._output import api_errors, emit
from ._resolve import UUID_RE, resolve_object

app = typer.Typer(no_args_is_help=True, help="CRM attributes (object columns), options + relationships.")


def _resolve_attribute_ref(client: Como, ref: str) -> str:
    """Resolve an attribute ref (id or slug) to its id, scanning every object for a slug."""
    if UUID_RE.match(ref):
        return ref
    for obj in client.objects.list():
        for attr in client.attributes.list(object_id=str(obj.id)):
            if attr.slug == ref:
                return str(attr.id)
    typer.secho(f"No attribute matching {ref!r}. Pass the attribute id, or scope it with its object.", fg="red", err=True)
    raise typer.Exit(code=1)


@app.command("ls")
def ls(
    object_ref: str = typer.Option(..., "--object", help="Object slug or id."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """List an object's attributes (incl. their options)."""
    with Como() as client, api_errors():
        object_id = resolve_object(client, object_ref)
        attrs = client.attributes.list(object_id=object_id)
    emit(attrs, pretty=pretty)


@app.command("create")
def create(
    object_ref: str = typer.Option(..., "--object", help="Object slug or id."),
    slug: str = typer.Option(..., "--slug"),
    name: str = typer.Option(..., "--name"),
    type: str = typer.Option("text", "--type", help="text/number/currency/date/select/status/checkbox/domain/email/…"),
    description: str | None = typer.Option(None, "--description"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Create a scalar attribute (column) on an object."""
    with Como() as client, api_errors():
        object_id = resolve_object(client, object_ref)
        attr = client.attributes.create(object_id=object_id, slug=slug, name=name, type=type, description=description)
    emit(attr, pretty=pretty)


@app.command("update")
def update(
    attribute_id: str = typer.Argument(..., help="The attribute id."),
    name: str | None = typer.Option(None, "--name"),
    description: str | None = typer.Option(None, "--description"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Update an attribute's name / description."""
    if name is None and description is None:
        typer.secho("Nothing to update — pass --name and/or --description.", fg="red", err=True)
        raise typer.Exit(code=1)
    with Como() as client, api_errors():
        attr = client.attributes.update(attribute_id, name=name, description=description)
    emit(attr, pretty=pretty)


@app.command("rm")
def rm(
    attribute_id: str = typer.Argument(..., help="The attribute id."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Archive (soft-delete) an attribute."""
    with Como() as client, api_errors():
        client.attributes.archive(attribute_id)
    emit({"archived": True, "attribute_id": attribute_id}, pretty=pretty)


@app.command("reorder")
def reorder(
    object_ref: str = typer.Option(..., "--object", help="Object slug or id."),
    attribute_ids: str = typer.Argument(..., help="Attribute ids in the desired order, comma-separated."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Reorder an object's attributes (full ordered id list)."""
    ids = [x.strip() for x in attribute_ids.split(",") if x.strip()]
    if not ids:
        typer.secho("No attribute ids given.", fg="red", err=True)
        raise typer.Exit(code=1)
    with Como() as client, api_errors():
        object_id = resolve_object(client, object_ref)
        attrs = client.attributes.reorder(object_id=object_id, ordered_attribute_ids=ids)
    emit(attrs, pretty=pretty)


@app.command("relationship")
def relationship(
    left_object: str = typer.Option(..., "--left-object", help="Left object slug or id."),
    left_slug: str = typer.Option(..., "--left-slug"),
    left_name: str = typer.Option(..., "--left-name"),
    left_cardinality: str = typer.Option(..., "--left-cardinality", help="one or many."),
    right_object: str = typer.Option(..., "--right-object", help="Right object slug or id."),
    right_slug: str = typer.Option(..., "--right-slug"),
    right_name: str = typer.Option(..., "--right-name"),
    right_cardinality: str = typer.Option(..., "--right-cardinality", help="one or many."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Create a bidirectional relationship attribute pair between two objects."""
    with Como() as client, api_errors():
        left_id = resolve_object(client, left_object)
        right_id = resolve_object(client, right_object)
        pair = client.attributes.create_relationship(
            left_object_id=left_id,
            left_slug=left_slug,
            left_name=left_name,
            left_cardinality=left_cardinality,
            right_object_id=right_id,
            right_slug=right_slug,
            right_name=right_name,
            right_cardinality=right_cardinality,
        )
    emit(pair, pretty=pretty)


@app.command("bind")
def bind(
    attribute_ref: str = typer.Argument(..., help="The attribute id or slug to bind."),
    agent_id: str = typer.Option(..., "--agent", help="The agent id to run for this column."),
    output_field: str = typer.Option(..., "--output-field", help="The agent output field to write into the column."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Bind an agent to a column: its `--output-field` fills this attribute."""
    with Como() as client, api_errors():
        attribute_id = _resolve_attribute_ref(client, attribute_ref)
        result = client.attributes.set_agent(attribute_id, agent_id=agent_id, output_field=output_field)
    emit(result, pretty=pretty)


@app.command("unbind")
def unbind(
    attribute_ref: str = typer.Argument(..., help="The attribute id or slug to unbind."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Unbind any agent from a column (the inverse of `bind`)."""
    with Como() as client, api_errors():
        attribute_id = _resolve_attribute_ref(client, attribute_ref)
        result = client.attributes.unbind_agent(attribute_id)
    emit(result, pretty=pretty)


@app.command("duplicate")
def duplicate(
    attribute_ref: str = typer.Argument(..., help="The attribute id or slug to clone."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Clone a (non-system) attribute, options and all."""
    with Como() as client, api_errors():
        attribute_id = _resolve_attribute_ref(client, attribute_ref)
        attr = client.attributes.duplicate(attribute_id)
    emit(attr, pretty=pretty)


# --- enrichment (which provider fills a column, from which provider field) ----
enrichment_app = typer.Typer(no_args_is_help=True, help="Bind a column to the enrichment provider (or clear it).")
app.add_typer(enrichment_app, name="enrichment")


@enrichment_app.command("set")
def enrichment_set(
    attribute_ref: str = typer.Argument(..., help="The attribute id or slug."),
    source: str = typer.Option(..., "--source", help="The enrichment provider key/source."),
    field: str = typer.Option(..., "--field", help="The provider-native field that fills this column."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Set which enrichment provider + provider field populates this column."""
    with Como() as client, api_errors():
        attribute_id = _resolve_attribute_ref(client, attribute_ref)
        attr = client.attributes.set_enrichment(attribute_id, source=source, field=field)
    emit(attr, pretty=pretty)


@enrichment_app.command("clear")
def enrichment_clear(
    attribute_ref: str = typer.Argument(..., help="The attribute id or slug."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Clear a column's enrichment mapping (it stops being enrichable)."""
    with Como() as client, api_errors():
        attribute_id = _resolve_attribute_ref(client, attribute_ref)
        attr = client.attributes.clear_enrichment(attribute_id)
    emit(attr, pretty=pretty)


# --- options (for select / status / multi_select attributes) -----------------
option_app = typer.Typer(no_args_is_help=True, help="Options on a select/status/multi_select attribute.")
app.add_typer(option_app, name="option")


@option_app.command("add")
def option_add(
    attribute_id: str = typer.Argument(..., help="The attribute id."),
    slug: str = typer.Option(..., "--slug"),
    label: str = typer.Option(..., "--label"),
    color: str | None = typer.Option(None, "--color"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Add an option (choice) to a select/status attribute."""
    with Como() as client, api_errors():
        opt = client.attributes.add_option(attribute_id, slug=slug, label=label, color=color)
    emit(opt, pretty=pretty)


@option_app.command("update")
def option_update(
    attribute_id: str = typer.Argument(..., help="The attribute id."),
    option_id: str = typer.Argument(..., help="The option id."),
    label: str | None = typer.Option(None, "--label"),
    color: str | None = typer.Option(None, "--color"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Update an option's label / color."""
    with Como() as client, api_errors():
        opt = client.attributes.update_option(attribute_id, option_id, label=label, color=color)
    emit(opt, pretty=pretty)


@option_app.command("rm")
def option_rm(
    attribute_id: str = typer.Argument(..., help="The attribute id."),
    option_id: str = typer.Argument(..., help="The option id."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Archive an option."""
    with Como() as client, api_errors():
        client.attributes.archive_option(attribute_id, option_id)
    emit({"archived": True, "attribute_id": attribute_id, "option_id": option_id}, pretty=pretty)
