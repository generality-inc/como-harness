from __future__ import annotations

import typer

from ..client import Como
from ._output import emit

app = typer.Typer(no_args_is_help=True, help="LinkedIn companies: full company records, search, and company posts.")


@app.command("get")
def get_company(
    url: str | None = typer.Option(
        None, "--url", help="LinkedIn company URL (https://www.linkedin.com/company/<name>)."
    ),
    universal_name: str | None = typer.Option(
        None, "--universal-name", help='Company universal name (the URL slug, e.g. "openai").'
    ),
    search: str | None = typer.Option(None, "--search", help="Resolve by name; returns the best-match company."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """Get the FULL company record (id, universalName, name, website, description, employeeCount,
    employeeCountRange, followerCount, foundedOn, headquarter, industry). Requires one of
    --url / --universal-name / --search. Use the returned `.element.id` to scope job/leads/post
    searches by --company-id."""
    with Como() as client:
        result = client.company.get(url=url, universal_name=universal_name, search=search)
    emit(result, pretty=pretty)


@app.command("search")
def search_companies(
    search: str | None = typer.Option(None, "--search", help="Keyword query (name / industry)."),
    location: str | None = typer.Option(
        None, "--location", help='Location text, e.g. "Australia". --geo-id is more precise.'
    ),
    geo_id: str | None = typer.Option(None, "--geo-id", help="LinkedIn geo ID (from `como geo search`)."),
    company_size: str | None = typer.Option(
        None,
        "--company-size",
        help="Headcount ranges, comma-joined: 1-10,11-50,51-200,201-500,501-1000,1001-5000,5001-10000,10001+.",
    ),
    industry_id: str | None = typer.Option(None, "--industry-id", help="LinkedIn industry ID(s), comma-joined."),
    page: int | None = typer.Option(None, "--page", help="1-based page number."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """Search companies. Returns SHALLOW hits (id, name, universalName, url) — call `como company
    get` for the full record. Each hit's `id` is the numeric LinkedIn company ID."""
    with Como() as client:
        result = client.company.search(
            search=search,
            location=location,
            geo_id=geo_id,
            company_size=company_size,
            industry_id=industry_id,
            page=page,
        )
    emit(result, pretty=pretty)


@app.command("posts")
def company_posts(
    company: str | None = typer.Option(None, "--company", help="Company URL or ID."),
    company_id: str | None = typer.Option(None, "--company-id", help="Numeric LinkedIn company ID (faster than URL)."),
    company_universal_name: str | None = typer.Option(
        None, "--company-universal-name", help="Company universal name (URL slug)."
    ),
    posted_limit: str | None = typer.Option(
        None, "--posted-limit", help="Only return posts within this window: 24h | week | month."
    ),
    scrape_posted_limit: str | None = typer.Option(
        None,
        "--scrape-posted-limit",
        help="Stop fetching once posts are older than this window (caps how far back to read): 24h | week | month.",
    ),
    page: int | None = typer.Option(None, "--page", help="1-based page number."),
    pagination_token: str | None = typer.Option(
        None,
        "--pagination-token",
        help="Token from a prior page's .pagination.paginationToken (required for pages >= 2).",
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """List posts authored by a company. Requires one of --company / --company-id /
    --company-universal-name."""
    with Como() as client:
        result = client.company.posts(
            company=company,
            company_id=company_id,
            company_universal_name=company_universal_name,
            posted_limit=posted_limit,
            scrape_posted_limit=scrape_posted_limit,
            page=page,
            pagination_token=pagination_token,
        )
    emit(result, pretty=pretty)
