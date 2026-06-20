"""``como crm records`` — full CRUD + references + merge over CRM records.

A **record** is a single row of a CRM object (a Company, a Person, …). These
commands are thin wrappers over the SDK client (``Como().records``),
authenticated by your ``como_live_`` key.

    como crm records create --object companies --name "Acme" --data '{"domain":"acme.com"}'
    como crm records upsert --object companies --match domain=acme.com --name "Acme"
    como crm records get <id>
    como crm records list --object companies --limit 50
    como crm records search "acme" --object companies
    como crm records update <id> --name "Acme Inc" --status active
    como crm records rm <id> [<id> ...]
    como crm records restore <id>
    como crm records link <id> --attribute employees --to <id> --to <id>
    como crm records merge <id> --victim <victim_id>
    como crm records lists <id>

`create` always inserts a new row. `upsert` is idempotent: it matches an
existing record by an identity attribute (``--match slug=value``) and updates
it, or creates one if none matches — reporting `created` + `changed_fields`.

Resolve ``--object`` by **slug** or **id**; resolve ``--list`` (optional) by a
list's name, slug, or id (same as `como crm lists`); resolve ``--attribute`` by
slug or id, scoped to the source record's object.
"""

from __future__ import annotations

import json

import typer

from ..client import Como
from ._output import api_errors, emit
from ._resolve import resolve_attribute, resolve_list, resolve_object

app = typer.Typer(
    no_args_is_help=True,
    help="Create + idempotently upsert CRM records.",
)


def _parse_data(data: str) -> dict:
    """Parse the ``--data`` JSON string into a dict. Exits on bad JSON / non-object."""
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as exc:
        typer.secho(f"--data is not valid JSON: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    if not isinstance(parsed, dict):
        typer.secho('--data must be a JSON object (e.g. \'{"domain":"acme.com"}\').', fg="red", err=True)
        raise typer.Exit(code=1)
    return parsed


@app.command("create")
def create(
    object_ref: str = typer.Option(..., "--object", help="Object slug or id (e.g. 'companies')."),
    name: str | None = typer.Option(None, "--name", help="The record's display name."),
    data: str = typer.Option("{}", "--data", help="Field values as a JSON object string."),
    list_ref: str | None = typer.Option(None, "--list", help="Add the record to this list (name, slug, or id)."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Create a new CRM record. Always inserts — use `upsert` to dedupe."""
    parsed = _parse_data(data)
    with Como() as client, api_errors():
        object_id = resolve_object(client, object_ref)
        list_id = str(resolve_list(client, list_ref).id) if list_ref is not None else None
        record = client.records.create(object_id=object_id, name=name, data=parsed, list_id=list_id)
    emit(record, pretty=pretty)


@app.command("upsert")
def upsert(
    object_ref: str = typer.Option(..., "--object", help="Object slug or id (e.g. 'companies')."),
    match: str = typer.Option(
        ..., "--match", help="Identity attribute + value as 'slug=value' (e.g. 'domain=acme.com')."
    ),
    name: str | None = typer.Option(None, "--name", help="The record's display name."),
    data: str = typer.Option("{}", "--data", help="Field values as a JSON object string."),
    list_ref: str | None = typer.Option(None, "--list", help="Add the record to this list (name, slug, or id)."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Idempotently create-or-update a record, matched by an identity attribute.

    Prints the record plus `created` (bool) and `changed_fields` (list)."""
    slug, sep, value = match.partition("=")
    if not sep or not slug:
        typer.secho("--match must be 'slug=value' (e.g. 'domain=acme.com').", fg="red", err=True)
        raise typer.Exit(code=1)
    parsed = _parse_data(data)
    with Como() as client, api_errors():
        object_id = resolve_object(client, object_ref)
        list_id = str(resolve_list(client, list_ref).id) if list_ref is not None else None
        result = client.records.upsert(
            object_id=object_id,
            identity_slug=slug,
            identity_value=value,
            name=name,
            data=parsed,
            list_id=list_id,
        )
    emit(result, pretty=pretty)


@app.command("get")
def get(
    record_id: str = typer.Argument(..., help="The record's id."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Fetch a single record by id."""
    with Como() as client, api_errors():
        record = client.records.get(record_id)
    emit(record, pretty=pretty)


@app.command("list")
def list_records(
    object_ref: str = typer.Option(..., "--object", help="Object slug or id (e.g. 'companies')."),
    limit: int = typer.Option(50, "--limit", help="Max records to return (up to 500)."),
    offset: int = typer.Option(0, "--offset", help="Number of records to skip."),
    view: str | None = typer.Option(None, "--view", help="Apply a saved view's filter + sort (view id)."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """List records for an object (newest first; or in a view's filter/sort order)."""
    with Como() as client, api_errors():
        object_id = resolve_object(client, object_ref)
        records = client.records.list(object_id=object_id, limit=limit, offset=offset, view_id=view)
    emit(records, pretty=pretty)


@app.command("search")
def search(
    query: str = typer.Argument(..., help="Substring to match against record names."),
    object_ref: str | None = typer.Option(None, "--object", help="Scope to this object (slug or id)."),
    limit: int = typer.Option(20, "--limit", help="Max hits to return."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Search records by name (ILIKE on name)."""
    with Como() as client, api_errors():
        object_id = resolve_object(client, object_ref) if object_ref is not None else None
        records = client.records.search(q=query, limit=limit, object_id=object_id)
    emit(records, pretty=pretty)


@app.command("update")
def update(
    record_id: str = typer.Argument(..., help="The record's id."),
    name: str | None = typer.Option(None, "--name", help="New display name."),
    data: str | None = typer.Option(None, "--data", help="Field values to merge, as a JSON object string."),
    status: str | None = typer.Option(None, "--status", help="New status."),
    owner: str | None = typer.Option(None, "--owner", help="Set the owner (a workspace member id)."),
    unset_owner: bool = typer.Option(False, "--unset-owner", help="Clear the record's owner."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Update a record. Only the fields you pass are sent (``--data`` merges)."""
    if owner is not None and unset_owner:
        typer.secho("Pass either --owner or --unset-owner, not both.", fg="red", err=True)
        raise typer.Exit(code=1)
    parsed = _parse_data(data) if data is not None else None
    if name is None and parsed is None and status is None and owner is None and not unset_owner:
        typer.secho(
            "Nothing to update — pass at least one of --name/--data/--status/--owner/--unset-owner.",
            fg="red",
            err=True,
        )
        raise typer.Exit(code=1)
    with Como() as client, api_errors():
        record = client.records.update(
            record_id, name=name, data=parsed, status=status, owner_member_id=owner, unset_owner=unset_owner
        )
    emit(record, pretty=pretty)


@app.command("rm")
def rm(
    record_ids: str = typer.Argument(..., help="A record id, or comma-separated ids."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Soft-delete record(s). One id uses DELETE; multiple use bulk-delete."""
    ids = [x.strip() for x in record_ids.split(",") if x.strip()]
    if not ids:
        typer.secho("No record ids given.", fg="red", err=True)
        raise typer.Exit(code=1)
    with Como() as client, api_errors():
        if len(ids) == 1:
            client.records.delete(ids[0])
            emit({"deleted_count": 1}, pretty=pretty)
            return
        result = client.records.bulk_delete(ids)
    emit(result, pretty=pretty)


@app.command("restore")
def restore(
    record_id: str = typer.Argument(..., help="The record's id."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Restore a soft-deleted record."""
    with Como() as client, api_errors():
        record = client.records.restore(record_id)
    emit(record, pretty=pretty)


@app.command("link")
def link(
    record_id: str = typer.Argument(..., help="The source record's id."),
    attribute_ref: str = typer.Option(..., "--attribute", help="Relationship attribute slug or id."),
    to: str = typer.Option(..., "--to", help="Target record id, or comma-separated ids, to set as references."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Set a record's references for a relationship attribute.

    Resolves the attribute on the source record's object, then replaces the
    reference set with the given target id(s)."""
    target_ids = [x.strip() for x in to.split(",") if x.strip()]
    if not target_ids:
        typer.secho("No target record ids given to --to.", fg="red", err=True)
        raise typer.Exit(code=1)
    with Como() as client, api_errors():
        record = client.records.get(record_id)
        attribute_id = resolve_attribute(client, str(record.object_id), attribute_ref)
        client.records.set_references(record_id, attribute_id=attribute_id, target_record_ids=target_ids)
    emit({"record_id": record_id, "attribute_id": attribute_id, "target_record_ids": target_ids}, pretty=pretty)


@app.command("unlink")
def unlink(
    record_id: str = typer.Argument(..., help="The source record's id."),
    attribute_ref: str = typer.Option(..., "--attribute", help="Relationship attribute slug or id to clear."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Clear all references for a relationship attribute (the inverse of `link`)."""
    with Como() as client, api_errors():
        record = client.records.get(record_id)
        attribute_id = resolve_attribute(client, str(record.object_id), attribute_ref)
        client.records.set_references(record_id, attribute_id=attribute_id, target_record_ids=[])
    emit({"record_id": record_id, "attribute_id": attribute_id, "target_record_ids": []}, pretty=pretty)


@app.command("related")
def related(
    record_id: str = typer.Argument(..., help="The record's id."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Show every relationship edge touching this record (forward + reverse)."""
    with Como() as client, api_errors():
        edges = client.records.related(record_id)
    emit(edges, pretty=pretty)


@app.command("duplicates")
def duplicates(
    object_ref: str = typer.Option(..., "--object", help="Object slug or id (e.g. 'companies')."),
    name: str | None = typer.Option(None, "--name", help="Candidate name to match."),
    data: str = typer.Option("{}", "--data", help="Candidate field values as a JSON object string."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Find likely-duplicate records (by email/domain/name) before inserting."""
    parsed = _parse_data(data)
    with Como() as client, api_errors():
        object_id = resolve_object(client, object_ref)
        hits = client.records.duplicates(object_id=object_id, name=name, data=parsed)
    emit(hits, pretty=pretty)


@app.command("merge")
def merge(
    record_id: str = typer.Argument(..., help="The survivor record's id."),
    victim_id: str = typer.Option(..., "--victim", help="The record to merge into the survivor (soft-deleted)."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Merge a victim record into a survivor; prints the surviving record."""
    with Como() as client, api_errors():
        record = client.records.merge(record_id, victim_id=victim_id)
    emit(record, pretty=pretty)


@app.command("lists")
def lists(
    record_id: str = typer.Argument(..., help="The record's id."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Show the lists this record belongs to + each membership's data."""
    with Como() as client, api_errors():
        memberships = client.records.lists(record_id)
    emit(memberships, pretty=pretty)
