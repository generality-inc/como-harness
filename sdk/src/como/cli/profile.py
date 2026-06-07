from __future__ import annotations

import typer

from ..client import Como
from ._output import emit

app = typer.Typer(
    no_args_is_help=True, help="LinkedIn profiles: full profiles, people search, posts, comments, reactions."
)


@app.command("get")
def get_profile(
    url: str | None = typer.Option(None, "--url", help="LinkedIn profile URL (https://www.linkedin.com/in/<id>)."),
    public_identifier: str | None = typer.Option(
        None, "--public-identifier", help="Public identifier / vanity slug (the /in/<this> part)."
    ),
    profile_id: str | None = typer.Option(
        None, "--profile-id", help="Opaque LinkedIn profile ID (ACoAA...). Fastest when known."
    ),
    main: bool = typer.Option(False, "--main", help="Return the lighter, cheaper main profile (skips heavy sections)."),
    find_email: bool = typer.Option(
        False, "--find-email", help="Also run a best-effort work-email lookup for this person."
    ),
    skip_smtp: bool = typer.Option(
        False, "--skip-smtp", help="With --find-email, skip SMTP deliverability checks (faster, less strict)."
    ),
    include_about_profile: bool = typer.Option(
        False, "--include-about-profile", help="Include the extended 'about' section in the response."
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """Get the FULL profile (name, headline, experience, education, skills, location) by URL,
    public identifier, or profile ID. Requires one of --url / --public-identifier / --profile-id.
    The returned `.id` is the profile ID for other commands."""
    with Como() as client:
        result = client.profile.get(
            url=url,
            public_identifier=public_identifier,
            profile_id=profile_id,
            main=main or None,
            find_email=find_email or None,
            skip_smtp=skip_smtp or None,
            include_about_profile=include_about_profile or None,
        )
    emit(result, pretty=pretty)


@app.command("search")
def search_profiles(
    search: str | None = typer.Option(None, "--search", help="Free-text name/keyword (fuzzy)."),
    current_company: str | None = typer.Option(
        None, "--current-company", help="Company URL or ID the person currently works at."
    ),
    past_company: str | None = typer.Option(
        None, "--past-company", help="Company URL or ID the person previously worked at."
    ),
    school: str | None = typer.Option(None, "--school", help="School URL or ID."),
    first_name: str | None = typer.Option(None, "--first-name", help="Exact first name."),
    last_name: str | None = typer.Option(None, "--last-name", help="Exact last name."),
    title: str | None = typer.Option(None, "--title", help='Job title keyword, e.g. "engineer".'),
    location: str | None = typer.Option(None, "--location", help="Location text. --geo-id is more precise."),
    geo_id: str | None = typer.Option(None, "--geo-id", help="LinkedIn geo ID (from `como geo search`)."),
    industry_id: str | None = typer.Option(None, "--industry-id", help="LinkedIn industry ID(s), comma-joined."),
    keywords_company: str | None = typer.Option(None, "--keywords-company", help="Free-text company keyword filter."),
    keywords_school: str | None = typer.Option(None, "--keywords-school", help="Free-text school keyword filter."),
    follower_of: str | None = typer.Option(None, "--follower-of", help="Limit to followers of this profile/company."),
    page: int | None = typer.Option(None, "--page", help="1-based page number (--page only; no token)."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """Basic people search. LIMITED: many results are anonymized "LinkedIn Member" with no link.
    For reliable people-finding (employees of a company, recent hires) use `como leads search`
    instead. Returns shallow hits; `como profile get` for the full record."""
    with Como() as client:
        result = client.profile.search(
            search=search,
            current_company=current_company,
            past_company=past_company,
            school=school,
            first_name=first_name,
            last_name=last_name,
            title=title,
            location=location,
            geo_id=geo_id,
            industry_id=industry_id,
            keywords_company=keywords_company,
            keywords_school=keywords_school,
            follower_of=follower_of,
            page=page,
        )
    emit(result, pretty=pretty)


@app.command("posts")
def profile_posts(
    profile: str | None = typer.Option(None, "--profile", help="Profile URL or ID."),
    profile_id: str | None = typer.Option(None, "--profile-id", help="Opaque profile ID (faster)."),
    profile_public_identifier: str | None = typer.Option(
        None, "--profile-public-identifier", help="Public identifier / vanity slug."
    ),
    page: int | None = typer.Option(None, "--page", help="1-based page number."),
    pagination_token: str | None = typer.Option(
        None, "--pagination-token", help="Token from a prior page (required for pages >= 2)."
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """List posts authored by a profile. Requires one of --profile / --profile-id /
    --profile-public-identifier."""
    with Como() as client:
        result = client.profile.posts(
            profile=profile,
            profile_id=profile_id,
            profile_public_identifier=profile_public_identifier,
            page=page,
            pagination_token=pagination_token,
        )
    emit(result, pretty=pretty)


@app.command("comments")
def profile_comments(
    profile: str | None = typer.Option(None, "--profile", help="Profile URL or ID."),
    profile_id: str | None = typer.Option(None, "--profile-id", help="Opaque profile ID (faster)."),
    page: int | None = typer.Option(None, "--page", help="1-based page number."),
    pagination_token: str | None = typer.Option(
        None, "--pagination-token", help="Token from a prior page (required for pages >= 2)."
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """List comments authored by a profile."""
    with Como() as client:
        result = client.profile.comments(
            profile=profile,
            profile_id=profile_id,
            page=page,
            pagination_token=pagination_token,
        )
    emit(result, pretty=pretty)


@app.command("reactions")
def profile_reactions(
    profile: str | None = typer.Option(None, "--profile", help="Profile URL or ID."),
    profile_id: str | None = typer.Option(None, "--profile-id", help="Opaque profile ID (faster)."),
    page: int | None = typer.Option(None, "--page", help="1-based page number."),
    pagination_token: str | None = typer.Option(
        None, "--pagination-token", help="Token from a prior page (required for pages >= 2)."
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """List reactions made by a profile."""
    with Como() as client:
        result = client.profile.reactions(
            profile=profile,
            profile_id=profile_id,
            page=page,
            pagination_token=pagination_token,
        )
    emit(result, pretty=pretty)
