from __future__ import annotations

import typer

from ..client import Como
from ._output import emit

app = typer.Typer(no_args_is_help=True, help="LinkedIn service providers: search people offering services.")


@app.command("search")
def search_services(
    search: str = typer.Option(..., "--search", help="Service / skill keyword, e.g. 'web development' (required)."),
    location: str | None = typer.Option(None, "--location", help="Location text. --geo-id is more precise."),
    geo_id: str | None = typer.Option(None, "--geo-id", help="LinkedIn geo ID (from `como geo search`)."),
    page: int | None = typer.Option(None, "--page", help="1-based page number (up to ~100 pages, 10/page)."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """Search the LinkedIn services directory (people offering services). Unlike `profile search`,
    results are not anonymized, so it's a good alternative for finding people by skill/title."""
    with Como() as client:
        result = client.service.search(
            search=search,
            location=location,
            geo_id=geo_id,
            page=page,
        )
    emit(result, pretty=pretty)
