"""``como agents`` — author, upload, and run research agents on the platform.

An **agent** is a reusable research-agent definition: a `mission` (the prompt a
sandboxed coding agent runs), the record `input_fields` it reads, and an
`output_schema` (JSON Schema) whose top-level scalar fields map onto CRM columns.
Upload one once, then run it over a list **again and again** — each run is a
sandboxed coding agent (browser + `como`), not a single LLM call.

    como agents template > my-agent.json   # scaffold a definition to edit
    como agents create --from-file my-agent.json   # upload it to your workspace
    como agents ls                          # list your agents
    como agents link <agent> --profile <profile>   # run it from a logged-in profile
    como agents run --attribute <col_id> --list <list_id>   # run it over a list

An agent can be **linked to a browser profile** (`como browser profile ls`): every
run then starts from that profile's logged-in snapshot, ephemerally — the run
never writes its changes back to the profile. Link with `como agents link`, or set
`browser_profile_id` in the definition JSON.

Authoring an agent needs `agents:create` (update/delete need `agents:update` /
`agents:delete`); running a batch needs `agents:run`. The admin and member roles
both carry all four, so any non-guest member can author and run agents.
"""

from __future__ import annotations

import json

import typer
from como_core.platform import Agent, BrowserProfile

from ..client import Como
from ._output import api_errors, emit

app = typer.Typer(
    no_args_is_help=True,
    help="Author, upload, and run research agents (run a list again and again).",
)

_TEMPLATE = {
    "name": "Offshore ops hiring",
    "description": "Counts open offshore back-office roles a company is hiring for.",
    "input_fields": ["name", "domain", "linkedin"],
    "budget_usd": 2.0,
    "mission": (
        "You are a research agent. Find how many open roles the company under research is "
        "hiring for that match the TARGET PROFILE, from its careers site (via browser-harness) "
        "and LinkedIn (via the `como linkedin` CLI). Read full job descriptions; judge by the "
        "description, not the title. TARGET PROFILE: <describe the roles you care about>. "
        "Emit the counts and back them with evidence (role -> location -> source URL)."
    ),
    "output_schema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "offshore-ops-hiring",
        "type": "object",
        "required": ["matching_role_count", "total_open_roles"],
        "properties": {
            "total_open_roles": {"type": "integer", "description": "All currently-open roles, de-duplicated."},
            "matching_role_count": {"type": "integer", "description": "Open roles matching the TARGET PROFILE."},
        },
    },
}


def _resolve_agent(client: Como, ref: str) -> Agent:
    ref_l = ref.lower()
    for a in client.agents.list():
        if str(a.id) == ref or a.slug == ref or (a.name or "").lower() == ref_l:
            return a
    typer.secho(f"No agent matching {ref!r}. Run `como agents ls`.", fg="red", err=True)
    raise typer.Exit(code=1)


def _resolve_profile(client: Como, ref: str) -> BrowserProfile:
    """Find a browser profile by id or name (case-insensitive)."""
    ref_l = ref.lower()
    for p in client.browser.profiles():
        if str(p.id) == ref or (p.name or "").lower() == ref_l:
            return p
    typer.secho(f"No browser profile matching {ref!r}. Run `como browser profile ls`.", fg="red", err=True)
    raise typer.Exit(code=1)


@app.command("template")
def template() -> None:
    """Print a starter agent definition (JSON) to stdout. Redirect to a file,
    edit the mission + output_schema, then `como agents create --from-file`."""
    emit(_TEMPLATE, pretty=True)


@app.command("ls")
def ls(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
    table: bool = typer.Option(False, "--table", help="Render a human table instead of JSON."),
) -> None:
    """List the agents in your workspace."""
    with Como() as client, api_errors():
        agents = client.agents.list()
        # Resolve linked profile ids to names only for the table view.
        names = (
            {str(p.id): p.name for p in client.browser.profiles()}
            if table and any(a.browser_profile_id for a in agents)
            else {}
        )
    if not table:
        emit(agents, pretty=pretty)
        return
    name_w = max((len(a.name or "") for a in agents), default=4)
    typer.echo(f"{'NAME'.ljust(name_w)}  {'SLUG'.ljust(24)}  {'PROFILE'.ljust(16)}  OUTPUT FIELDS")
    for a in agents:
        fields = ", ".join((a.output_fields or {}).keys()) or "—"
        pid = a.browser_profile_id
        profile = (names.get(str(pid)) or str(pid)) if pid else "—"
        typer.echo(f"{(a.name or '').ljust(name_w)}  {(a.slug or '').ljust(24)}  {profile.ljust(16)}  {fields}")


@app.command("get")
def get(
    ref: str = typer.Argument(..., help="Agent name, slug, or id."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Show an agent definition as JSON."""
    with Como() as client, api_errors():
        agent = _resolve_agent(client, ref)
    emit(agent, pretty=pretty)


@app.command("create")
def create(
    from_file: str = typer.Option(..., "--from-file", "-f", help="Path to an agent definition JSON (see `template`)."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Upload an agent definition to your workspace."""
    try:
        with open(from_file) as fh:
            definition = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        typer.secho(f"Couldn't read {from_file!r}: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    with Como() as client, api_errors():
        agent = client.agents.create(definition)
    typer.secho(f"Uploaded agent {agent.name!r} (slug: {agent.slug}).", fg="green", err=True)
    emit(agent, pretty=pretty)


@app.command("link")
def link(
    ref: str = typer.Argument(..., help="Agent name, slug, or id."),
    profile: str = typer.Option(..., "--profile", "-p", help="Browser profile name or id to run from."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Link an agent to a browser profile — its runs start from that profile's
    logged-in snapshot, ephemerally (the run never writes back to the profile).
    Needs `agents:update`."""
    with Como() as client, api_errors():
        agent = _resolve_agent(client, ref)
        prof = _resolve_profile(client, profile)
        updated = client.agents.set_browser_profile(str(agent.id), profile_id=str(prof.id))
    typer.secho(f"Linked agent {agent.name!r} to profile {prof.name!r}.", fg="green", err=True)
    emit(updated, pretty=pretty)


@app.command("unlink")
def unlink(
    ref: str = typer.Argument(..., help="Agent name, slug, or id."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Unlink an agent's browser profile — its runs go back to an anonymous
    browser. Needs `agents:update`."""
    with Como() as client, api_errors():
        agent = _resolve_agent(client, ref)
        updated = client.agents.set_browser_profile(str(agent.id), profile_id=None)
    typer.secho(f"Unlinked agent {agent.name!r} — runs use an anonymous browser.", fg="green", err=True)
    emit(updated, pretty=pretty)


@app.command("rm")
def rm(
    ref: str = typer.Argument(..., help="Agent name, slug, or id."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Delete an agent (needs agents:delete)."""
    with Como() as client, api_errors():
        agent = _resolve_agent(client, ref)
        client.agents.delete(str(agent.id))
    emit({"deleted": True, "agent_id": str(agent.id)}, pretty=pretty)


@app.command("run")
def run(
    attribute: str = typer.Option(..., "--attribute", help="Agent-bound column (attribute) id to compute."),
    list_id: str = typer.Option(..., "--list", help="List id to run over."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Run an agent-bound column over a list — creates a batch (one sandboxed run
    per record). Bind the agent to the column first (in the web app), then run
    this as often as you like."""
    with Como() as client, api_errors():
        batch = client.agents.run_batch(attribute_id=attribute, list_id=list_id)
    typer.secho(f"Started batch {batch.id} — {batch.total_runs} runs queued.", fg="green", err=True)
    emit(batch, pretty=pretty)


@app.command("batches")
def batches(
    agent_id: str = typer.Argument(..., help="Agent id (UUID)."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """List an agent's batches — its run history, newest first."""
    with Como() as client, api_errors():
        result = client.agents.list_batches(agent_id)
    emit(result, pretty=pretty)


@app.command("batch")
def batch(
    batch_id: str = typer.Argument(..., help="Batch id (UUID)."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Show one batch's progress — status, counters, and spend."""
    with Como() as client, api_errors():
        result = client.agents.get_batch(batch_id)
    emit(result, pretty=pretty)


@app.command("runs")
def runs(
    batch_id: str = typer.Argument(..., help="Batch id (UUID)."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """List a batch's per-record runs — status, value, cost, error, timestamps."""
    with Como() as client, api_errors():
        result = client.agents.list_runs(batch_id)
    emit(result, pretty=pretty)


@app.command("active")
def active(
    attribute: str = typer.Option(..., "--attribute", help="Agent-bound column (attribute) id."),
    list_id: str = typer.Option(..., "--list", help="List id."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print the JSON output."),
) -> None:
    """Show the active (pending/running) batch for a column+list, or null."""
    with Como() as client, api_errors():
        result = client.agents.active_batch(attribute_id=attribute, list_id=list_id)
    if result is None:
        typer.secho("No active batch for this column + list.", fg="yellow", err=True)
    emit(result, pretty=pretty)
