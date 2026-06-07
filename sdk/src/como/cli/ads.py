from __future__ import annotations

import typer

from ..client import Como
from ._output import emit

app = typer.Typer(no_args_is_help=True, help="LinkedIn Ad Library: full ad records and ad search.")


@app.command("get")
def get_ad(
    ad_id: str | None = typer.Option(None, "--ad-id", help="LinkedIn ad ID (e.g. 1104386363)."),
    url: str | None = typer.Option(None, "--url", help="LinkedIn Ad Library detail URL."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """Get the full ad record by ad ID or URL. Requires one of --ad-id / --url."""
    with Como() as client:
        result = client.ads.get(ad_id=ad_id, url=url)
    emit(result, pretty=pretty)


@app.command("search")
def search_ads(
    search_url: str | None = typer.Option(
        None, "--search-url", help="Reproduce an Ad Library search by pasting its URL (filters parsed from it)."
    ),
    keyword: str | None = typer.Option(None, "--keyword", help="Keyword query."),
    account_owner: str | None = typer.Option(None, "--account-owner", help="Advertiser / account owner name."),
    countries: str | None = typer.Option(None, "--countries", help="Country codes, comma-joined (e.g. US,CA,FR)."),
    date_option: str | None = typer.Option(
        None, "--date-option", help="Date filter mode, e.g. custom-date-range (use with --startdate/--enddate)."
    ),
    startdate: str | None = typer.Option(
        None, "--startdate", help="Start date YYYY-MM-DD (with --date-option custom-date-range)."
    ),
    enddate: str | None = typer.Option(
        None, "--enddate", help="End date YYYY-MM-DD (with --date-option custom-date-range)."
    ),
    pagination_token: str | None = typer.Option(
        None, "--pagination-token", help="Token from a prior page (required for pages >= 2)."
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """Search the LinkedIn Ad Library by keyword, advertiser, countries, and date range."""
    with Como() as client:
        result = client.ads.search(
            search_url=search_url,
            keyword=keyword,
            account_owner=account_owner,
            countries=countries,
            date_option=date_option,
            startdate=startdate,
            enddate=enddate,
            pagination_token=pagination_token,
        )
    emit(result, pretty=pretty)
