from __future__ import annotations

import typer

from .._version import __version__
from . import (
    ads as _ads_cli,
)
from . import (
    agents as _agents_cli,
)
from . import (
    attributes as _attributes_cli,
)
from . import (
    auth as _auth_cli,
)
from . import (
    browser as _browser_cli,
)
from . import (
    company as _company_cli,
)
from . import (
    geo as _geo_cli,
)
from . import (
    group as _group_cli,
)
from . import (
    job as _job_cli,
)
from . import (
    leads as _leads_cli,
)
from . import (
    lists as _lists_cli,
)
from . import (
    objects as _objects_cli,
)
from . import (
    post as _post_cli,
)
from . import (
    profile as _profile_cli,
)
from . import (
    records as _records_cli,
)
from . import (
    run as _run_cli,
)
from . import (
    service as _service_cli,
)
from . import (
    views as _views_cli,
)

app = typer.Typer(
    name="como",
    no_args_is_help=True,
    add_completion=False,
    help=(
        "como — typed CLI & SDK for the como platform.\n\n"
        "Groups: `como linkedin` (ghost LinkedIn research data — companies, jobs, people, "
        "posts, groups, ads, services, locations), `como auth` (sign in), "
        "`como run -- <cmd>` (run code with the LLM gateway injected). "
        "Auth via COMO_API_KEY. Add --pretty for readable JSON."
    ),
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-V", help="Show version and exit."),
) -> None:
    if version:
        typer.echo(f"como {__version__}")
        raise typer.Exit()
    # Throttled best-effort auto-update (notify + fast-forward pull). Never runs
    # for `como update` itself, and is a no-op under COMO_NO_UPDATE (the runner).
    if ctx.invoked_subcommand != "update":
        from .._autoupdate import maybe_autoupdate

        maybe_autoupdate()


# ---- `como linkedin` — the ghost LinkedIn research API -----------------------
# All read-only public LinkedIn data lives under one group. It is sourced from
# the como "ghost" research API and does NOT touch the user's own LinkedIn login.
linkedin = typer.Typer(
    name="linkedin",
    no_args_is_help=True,
    help=(
        "Ghost LinkedIn research — read-only LinkedIn data (companies, jobs, people, "
        "posts, groups, ads, services, locations) via the como ghost research API; "
        "needs no LinkedIn account of your own.\n\n"
        "Key idea: a `search` returns SHALLOW hits (no descriptions/full fields) — call "
        "the matching `get` for the full record. Resolve an entity to an ID first "
        "(`company get` -> id) and pass --company-id / --geo-id rather than fuzzy keyword "
        "search. Run `como linkedin <resource> <command> --help` for full options."
    ),
    context_settings={"help_option_names": ["-h", "--help"]},
)
linkedin.add_typer(_company_cli.app, name="company")
linkedin.add_typer(_job_cli.app, name="job")
linkedin.add_typer(_profile_cli.app, name="profile")
linkedin.add_typer(_leads_cli.app, name="leads")
linkedin.add_typer(_post_cli.app, name="post")
linkedin.add_typer(_group_cli.app, name="group")
linkedin.add_typer(_ads_cli.app, name="ads")
linkedin.add_typer(_service_cli.app, name="service")
linkedin.add_typer(_geo_cli.app, name="geo")

app.add_typer(linkedin, name="linkedin")
app.add_typer(_auth_cli.app, name="auth")
app.add_typer(_browser_cli.app, name="browser")

# ---- `como crm` — the first-party CRM (records, lists, objects, attributes) ---
# The symmetric counterpart to `como linkedin`: `linkedin` is what you can *learn*
# (read-only ghost research); `crm` is what you *own* (your workspace's records,
# lists, and the object/attribute catalog). One namespace keeps the top level flat.
crm = typer.Typer(
    name="crm",
    no_args_is_help=True,
    help=(
        "Your workspace CRM — records, lists, and the object/attribute catalog.\n\n"
        "`crm records` (rows) and `crm lists` (curated containers, + `lists view` / "
        "`lists attrs`) are the daily surface; `crm objects` / `crm attributes` shape "
        "the schema. Authenticated by your `como_live_` key; every command prints JSON "
        "(`--pretty` to format). Run `como crm <resource> --help` for commands."
    ),
    context_settings={"help_option_names": ["-h", "--help"]},
)
_lists_cli.app.add_typer(_views_cli.app, name="view")
crm.add_typer(_records_cli.app, name="records")
crm.add_typer(_lists_cli.app, name="lists")
crm.add_typer(_objects_cli.app, name="objects")
crm.add_typer(_attributes_cli.app, name="attributes")
app.add_typer(crm, name="crm")

app.add_typer(_agents_cli.app, name="agents")

# Passthrough launchers: run a command (or Claude Code) with the LLM gateway env
# injected for that child process only — `--` separates como's flags from the
# command. `ignore_unknown_options` lets the wrapped command keep its own flags.
_RUN_CTX = {"allow_extra_args": True, "ignore_unknown_options": True}
app.command(
    "run", context_settings=_RUN_CTX, help="Run a command with the como LLM gateway injected: como run -- <cmd>"
)(_run_cli.run)
app.command("claude", context_settings=_RUN_CTX, help="Run Claude Code routed through the como LLM gateway.")(
    _run_cli.claude
)


@app.command("update", help="Update the como CLI to the latest (fast-forward pull on the editable clone).")
def _update() -> None:
    from .._autoupdate import force_update

    raise typer.Exit(force_update())
