from __future__ import annotations

import typer

from ..client import Como
from ._output import emit

app = typer.Typer(no_args_is_help=True, help="LinkedIn jobs: full job records and job search.")


@app.command("get")
def get_job(
    job_id: str | None = typer.Option(None, "--job-id", help="LinkedIn job ID (e.g. 4153069088)."),
    url: str | None = typer.Option(None, "--url", help="LinkedIn job URL (https://www.linkedin.com/jobs/view/...)."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """Get the FULL job record (descriptionText, descriptionHtml, salary, workplaceType,
    employmentType, applicantsCount, expireAt) by job ID or URL. Requires one of --job-id / --url.
    An empty element usually means the posting expired on LinkedIn."""
    with Como() as client:
        result = client.job.get(job_id=job_id, url=url)
    emit(result, pretty=pretty)


@app.command("search")
def search_jobs(
    search: str | None = typer.Option(
        None, "--search", help="Keyword query (fuzzy; may include other companies). Prefer --company-id."
    ),
    company_id: str | None = typer.Option(
        None,
        "--company-id",
        help="Scope to a company's jobs by numeric LinkedIn ID (from `como company get`). PREFERRED over --search.",
    ),
    location: str | None = typer.Option(
        None, "--location", help='Location text, e.g. "US". Can mis-resolve; --geo-id is more precise.'
    ),
    geo_id: str | None = typer.Option(
        None, "--geo-id", help="LinkedIn geo ID (from `como geo search`) for precise location filtering."
    ),
    sort_by: str | None = typer.Option(None, "--sort-by", help="date | relevance."),
    workplace_type: str | None = typer.Option(
        None, "--workplace-type", help="on-site | hybrid | remote (comma-join for multiple)."
    ),
    employment_type: str | None = typer.Option(
        None, "--employment-type", help="full-time | part-time | contract | internship | temporary (comma-join)."
    ),
    salary: str | None = typer.Option(None, "--salary", help="Minimum salary band, e.g. 40k+ … 200k+."),
    posted_limit: str | None = typer.Option(None, "--posted-limit", help="24h | week | month."),
    experience_level: str | None = typer.Option(
        None, "--experience-level", help="LinkedIn experience-level ID(s), comma-joined."
    ),
    industry_id: str | None = typer.Option(None, "--industry-id", help="LinkedIn industry ID(s), comma-joined."),
    function_id: str | None = typer.Option(None, "--function-id", help="LinkedIn job-function ID(s), comma-joined."),
    under10_applicants: str | None = typer.Option(
        None, "--under10-applicants", help="'true' to only return postings with fewer than 10 applicants."
    ),
    easy_apply: str | None = typer.Option(None, "--easy-apply", help="'true' to only return Easy Apply postings."),
    page: int | None = typer.Option(None, "--page", help="1-based page number. See .pagination.totalPages."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """Search jobs. Returns SHALLOW hits (id, url, title, company, location, postedDate) with
    NO description — call `como job get --job-id <id>` on each hit to read the JD. To enumerate a
    company's roles, resolve its ID with `como company get` then pass --company-id (cleaner than
    keyword --search, which leaks other companies' postings)."""
    with Como() as client:
        result = client.job.search(
            search=search,
            company_id=company_id,
            location=location,
            geo_id=geo_id,
            sort_by=sort_by,
            workplace_type=workplace_type,
            employment_type=employment_type,
            salary=salary,
            posted_limit=posted_limit,
            experience_level=experience_level,
            industry_id=industry_id,
            function_id=function_id,
            under10_applicants=under10_applicants,
            easy_apply=easy_apply,
            page=page,
        )
    emit(result, pretty=pretty)
