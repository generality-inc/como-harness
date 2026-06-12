"""``como agents`` — author, upload, and run research agents on the platform.

An **agent** is a reusable research-agent definition: a `mission` (the prompt a
sandboxed coding agent runs), the record `input_fields` it reads, and an
`output_schema` (JSON Schema) whose top-level scalar fields map onto CRM columns.
Upload one once, then run it over a list **again and again** — each run is a
sandboxed coding agent (browser + `como`), not a single LLM call.

    como agents template > my-agent.json   # scaffold a definition to edit
    como agents create --from-file my-agent.json   # upload it to your workspace
    como agents ls                          # list your agents
    como agents run --attribute <col_id> --list <list_id>   # run it over a list

Authoring an agent needs the `workspace:manage` role; running needs
`records:update`.
"""

from __future__ import annotations

import json

import httpx
import typer

from .._config import DEFAULT_TIMEOUT, resolve_api_key, resolve_base_url

app = typer.Typer(
    no_args_is_help=True,
    help="Author, upload, and run research agents (run a list again and again).",
)

_BASE = "/v1/crm"

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


def _client() -> tuple[str, dict[str, str]]:
    return resolve_base_url(None), {"Authorization": f"Bearer {resolve_api_key(None)}"}


def _req(method: str, path: str, body: dict | None = None) -> object:
    base, headers = _client()
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as c:
            r = c.request(method, f"{base}{path}", headers=headers, json=body)
            r.raise_for_status()
            return r.json() if r.content else None
    except httpx.HTTPStatusError as exc:
        typer.secho(f"Request failed ({exc.response.status_code}): {exc.response.text}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    except httpx.HTTPError as exc:
        typer.secho(f"Request failed: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc


def _resolve_agent(ref: str) -> dict:
    agents = _req("GET", f"{_BASE}/agents")
    assert isinstance(agents, list)
    ref_l = ref.lower()
    for a in agents:
        if str(a.get("id")) == ref or a.get("slug") == ref or str(a.get("name", "")).lower() == ref_l:
            return a
    typer.secho(f"No agent matching {ref!r}. Run `como agents ls`.", fg="red", err=True)
    raise typer.Exit(code=1)


@app.command("template")
def template() -> None:
    """Print a starter agent definition (JSON) to stdout. Redirect to a file,
    edit the mission + output_schema, then `como agents create --from-file`."""
    typer.echo(json.dumps(_TEMPLATE, indent=2))


@app.command("ls")
def ls(json_out: bool = typer.Option(False, "--json", help="Raw JSON instead of a table.")) -> None:
    """List the agents in your workspace."""
    agents = _req("GET", f"{_BASE}/agents")
    assert isinstance(agents, list)
    if json_out:
        typer.echo(json.dumps(agents, indent=2))
        return
    if not agents:
        typer.secho("No agents yet. Scaffold one: `como agents template > a.json`.", fg="yellow")
        return
    name_w = max((len(str(a.get("name", ""))) for a in agents), default=4)
    typer.echo(f"{'NAME'.ljust(name_w)}  {'SLUG'.ljust(24)}  OUTPUT FIELDS")
    for a in agents:
        fields = ", ".join((a.get("output_fields") or {}).keys()) or "—"
        typer.echo(f"{str(a.get('name','')).ljust(name_w)}  {str(a.get('slug','')).ljust(24)}  {fields}")


@app.command("get")
def get(ref: str = typer.Argument(..., help="Agent name, slug, or id.")) -> None:
    """Show an agent definition as JSON."""
    typer.echo(json.dumps(_resolve_agent(ref), indent=2))


@app.command("create")
def create(
    from_file: str = typer.Option(..., "--from-file", "-f", help="Path to an agent definition JSON (see `template`)."),
) -> None:
    """Upload an agent definition to your workspace."""
    try:
        with open(from_file) as fh:
            body = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        typer.secho(f"Couldn't read {from_file!r}: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    agent = _req("POST", f"{_BASE}/agents", body)
    typer.echo(json.dumps(agent, indent=2))
    if isinstance(agent, dict):
        typer.secho(f"\nUploaded agent {agent.get('name')!r} (slug: {agent.get('slug')}).", fg="green")


@app.command("rm")
def rm(ref: str = typer.Argument(..., help="Agent name, slug, or id.")) -> None:
    """Delete an agent (needs workspace:manage)."""
    agent = _resolve_agent(ref)
    _req("DELETE", f"{_BASE}/agents/{agent['id']}")
    typer.secho(f"Deleted {agent['name']!r}.", fg="green")


@app.command("run")
def run(
    attribute: str = typer.Option(..., "--attribute", help="Agent-bound column (attribute) id to compute."),
    list_id: str = typer.Option(..., "--list", help="List id to run over."),
) -> None:
    """Run an agent-bound column over a list — creates a batch (one sandboxed run
    per record). Bind the agent to the column first (in the web app), then run
    this as often as you like."""
    batch = _req("POST", f"{_BASE}/agent-batches", {"attribute_id": attribute, "list_id": list_id})
    typer.echo(json.dumps(batch, indent=2))
    if isinstance(batch, dict):
        typer.secho(f"\nStarted batch {batch.get('id')} — {batch.get('total_runs')} runs queued.", fg="green")
