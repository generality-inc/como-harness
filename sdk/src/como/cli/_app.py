from __future__ import annotations

import typer

from .._version import __version__
from . import (
    ads as _ads_cli,
)
from . import (
    auth as _auth_cli,
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
    post as _post_cli,
)
from . import (
    profile as _profile_cli,
)
from . import (
    service as _service_cli,
)

app = typer.Typer(
    name="como",
    no_args_is_help=True,
    add_completion=False,
    help=(
        "como — typed CLI & SDK for LinkedIn data.\n\n"
        "Resources: company, job, profile, leads (people search), post, group, ads, service, geo. "
        "Auth via COMO_API_KEY. Add --pretty for readable JSON.\n\n"
        "Key idea: a `search` returns SHALLOW hits (no descriptions/full fields) — call the matching "
        "`get` for the full record. Resolve an entity to an ID first (`company get` -> id) and pass "
        "--company-id / --geo-id rather than fuzzy keyword search. Run `como <resource> <command> --help` "
        "for full options."
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


app.add_typer(_ads_cli.app, name="ads")
app.add_typer(_auth_cli.app, name="auth")
app.add_typer(_company_cli.app, name="company")
app.add_typer(_geo_cli.app, name="geo")
app.add_typer(_group_cli.app, name="group")
app.add_typer(_job_cli.app, name="job")
app.add_typer(_leads_cli.app, name="leads")
app.add_typer(_post_cli.app, name="post")
app.add_typer(_profile_cli.app, name="profile")
app.add_typer(_service_cli.app, name="service")
