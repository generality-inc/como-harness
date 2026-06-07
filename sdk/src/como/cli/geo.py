from __future__ import annotations

import typer

from ..client import Como
from ._output import emit

app = typer.Typer(
    no_args_is_help=True, help="Geo IDs: resolve a location to a LinkedIn geo ID for precise search filtering."
)


@app.command("search")
def search_geo(
    search: str = typer.Option(..., "--search", help="Location text to look up, e.g. 'New York' (required)."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """Resolve a location to a LinkedIn geo ID. The response `.id` is the closest match (and
    `.elements` lists all matches). Pass that id as --geo-id to company/profile/job/leads/service
    search for precise, unambiguous location filtering (avoids NY->New Zealand mishaps)."""
    with Como() as client:
        result = client.geo.search(search=search)
    emit(result, pretty=pretty)
