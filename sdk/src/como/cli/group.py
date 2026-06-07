from __future__ import annotations

import typer

from ..client import Como
from ._output import emit

app = typer.Typer(no_args_is_help=True, help="LinkedIn groups: full group records and group search.")


@app.command("get")
def get_group(
    url: str | None = typer.Option(None, "--url", help="LinkedIn group URL (https://www.linkedin.com/groups/<id>/)."),
    group_id: str | None = typer.Option(None, "--group-id", help="Numeric LinkedIn group ID."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """Get the full group record by URL or group ID. Requires one of --url / --group-id."""
    with Como() as client:
        result = client.group.get(url=url, group_id=group_id)
    emit(result, pretty=pretty)


@app.command("search")
def search_groups(
    search: str | None = typer.Option(None, "--search", help="Keyword query."),
    page: int | None = typer.Option(None, "--page", help="1-based page number."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """Search groups by keyword. Returns shallow hits; `como group get` for the full record."""
    with Como() as client:
        result = client.group.search(search=search, page=page)
    emit(result, pretty=pretty)
