from __future__ import annotations

import typer

from ..client import Como
from ._output import emit

app = typer.Typer(
    no_args_is_help=True, help="LinkedIn people search (high quality): employees, recent hires, lead lists."
)


@app.command("search")
def search_leads(
    search: str | None = typer.Option(None, "--search", help="Free-text keyword (e.g. a job title)."),
    current_companies: str | None = typer.Option(
        None, "--current-companies", help="Company URL(s)/ID(s) the person currently works at. Comma-joined."
    ),
    past_companies: str | None = typer.Option(
        None, "--past-companies", help="Company URL(s)/ID(s) previously worked at. Comma-joined."
    ),
    locations: str | None = typer.Option(
        None, "--locations", help="Location text(s). Comma-joined. --geo-ids is more precise."
    ),
    geo_ids: str | None = typer.Option(
        None, "--geo-ids", help="LinkedIn geo ID(s) (from `como geo search`). Comma-joined."
    ),
    schools: str | None = typer.Option(None, "--schools", help="School URL(s)/ID(s). Comma-joined."),
    current_job_titles: str | None = typer.Option(
        None, "--current-job-titles", help='Current title keyword(s), e.g. "Software Engineer". Comma-joined.'
    ),
    past_job_titles: str | None = typer.Option(None, "--past-job-titles", help="Past title keyword(s). Comma-joined."),
    first_names: str | None = typer.Option(None, "--first-names", help="First name(s). Comma-joined."),
    last_names: str | None = typer.Option(None, "--last-names", help="Last name(s). Comma-joined."),
    industry_ids: str | None = typer.Option(None, "--industry-ids", help="LinkedIn industry ID(s). Comma-joined."),
    years_at_current_company_ids: str | None = typer.Option(
        None, "--years-at-current-company-ids", help="Tenure-bucket ID(s) at current company. Comma-joined."
    ),
    years_of_experience_ids: str | None = typer.Option(
        None, "--years-of-experience-ids", help="Total-experience bucket ID(s). Comma-joined."
    ),
    seniority_level_ids: str | None = typer.Option(
        None, "--seniority-level-ids", help="Seniority-level ID(s). Comma-joined."
    ),
    function_ids: str | None = typer.Option(None, "--function-ids", help="Job-function ID(s). Comma-joined."),
    recently_changed_jobs: bool = typer.Option(
        False,
        "--recently-changed-jobs",
        help="Only people who recently changed jobs (i.e. recent hires).",
    ),
    posted_on_linkedin: bool = typer.Option(
        False, "--posted-on-linkedin", help="Only people who recently posted on LinkedIn."
    ),
    profile_languages: str | None = typer.Option(
        None, "--profile-languages", help="Profile language code(s), e.g. en. Comma-joined."
    ),
    company_headcount: str | None = typer.Option(
        None, "--company-headcount", help="Headcount range(s) of the person's company. Comma-joined."
    ),
    company_headquarter_locations: str | None = typer.Option(
        None, "--company-headquarter-locations", help="HQ location(s) of the person's company. Comma-joined."
    ),
    exclude_locations: str | None = typer.Option(
        None, "--exclude-locations", help="Exclude these location(s). Comma-joined."
    ),
    exclude_geo_ids: str | None = typer.Option(
        None, "--exclude-geo-ids", help="Exclude these geo ID(s). Comma-joined."
    ),
    exclude_current_companies: str | None = typer.Option(
        None, "--exclude-current-companies", help="Exclude these current companies. Comma-joined."
    ),
    exclude_past_companies: str | None = typer.Option(
        None, "--exclude-past-companies", help="Exclude these past companies. Comma-joined."
    ),
    exclude_schools: str | None = typer.Option(None, "--exclude-schools", help="Exclude these schools. Comma-joined."),
    exclude_current_job_titles: str | None = typer.Option(
        None, "--exclude-current-job-titles", help="Exclude these current titles. Comma-joined."
    ),
    exclude_past_job_titles: str | None = typer.Option(
        None, "--exclude-past-job-titles", help="Exclude these past titles. Comma-joined."
    ),
    exclude_industry_ids: str | None = typer.Option(
        None, "--exclude-industry-ids", help="Exclude these industry ID(s). Comma-joined."
    ),
    exclude_seniority_level_ids: str | None = typer.Option(
        None, "--exclude-seniority-level-ids", help="Exclude these seniority-level ID(s). Comma-joined."
    ),
    exclude_function_ids: str | None = typer.Option(
        None, "--exclude-function-ids", help="Exclude these function ID(s). Comma-joined."
    ),
    exclude_company_headquarter_locations: str | None = typer.Option(
        None, "--exclude-company-headquarter-locations", help="Exclude these company HQ location(s). Comma-joined."
    ),
    sales_nav_url: str | None = typer.Option(
        None, "--sales-nav-url", help="Reproduce a Sales Navigator search by pasting its URL (filters parsed from it)."
    ),
    page: int | None = typer.Option(
        None, "--page", help="1-based page number. Use --session-id for consistent multi-page results."
    ),
    session_id: str | None = typer.Option(
        None,
        "--session-id",
        help="Arbitrary string pinning all pages to one backend resource (consistent pagination; slower).",
    ),
    use_private_pool: str | None = typer.Option(
        None, "--use-private-pool", help="Route via your private account pool (advanced)."
    ),
    required_account_id: str | None = typer.Option(
        None, "--required-account-id", help="Pin to a specific account in your pool (advanced)."
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """High-quality people search with advanced inclusion/exclusion filters — the reliable way to
    find employees of a company, recent hires, and lead lists (no anonymized "LinkedIn Member"
    gaps like `profile search` has). All multi-value filters are COMMA-JOINED strings.

    Recent hires at a company:
      como leads search --current-companies <companyUrlOrId> --recently-changed-jobs --current-job-titles "Engineer,Software,ML"
    """
    with Como() as client:
        result = client.leads.search(
            search=search,
            current_companies=current_companies,
            past_companies=past_companies,
            locations=locations,
            geo_ids=geo_ids,
            schools=schools,
            current_job_titles=current_job_titles,
            past_job_titles=past_job_titles,
            first_names=first_names,
            last_names=last_names,
            industry_ids=industry_ids,
            years_at_current_company_ids=years_at_current_company_ids,
            years_of_experience_ids=years_of_experience_ids,
            seniority_level_ids=seniority_level_ids,
            function_ids=function_ids,
            recently_changed_jobs=recently_changed_jobs or None,
            posted_on_linkedin=posted_on_linkedin or None,
            profile_languages=profile_languages,
            company_headcount=company_headcount,
            company_headquarter_locations=company_headquarter_locations,
            exclude_locations=exclude_locations,
            exclude_geo_ids=exclude_geo_ids,
            exclude_current_companies=exclude_current_companies,
            exclude_past_companies=exclude_past_companies,
            exclude_schools=exclude_schools,
            exclude_current_job_titles=exclude_current_job_titles,
            exclude_past_job_titles=exclude_past_job_titles,
            exclude_industry_ids=exclude_industry_ids,
            exclude_seniority_level_ids=exclude_seniority_level_ids,
            exclude_function_ids=exclude_function_ids,
            exclude_company_headquarter_locations=exclude_company_headquarter_locations,
            sales_nav_url=sales_nav_url,
            page=page,
            session_id=session_id,
            use_private_pool=use_private_pool,
            required_account_id=required_account_id,
        )
    emit(result, pretty=pretty)
