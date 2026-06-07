from __future__ import annotations

import typer

from ..client import Como
from ._output import emit

app = typer.Typer(no_args_is_help=True, help="LinkedIn posts: search, get, and posts by company / user / group.")


@app.command("search")
def search_posts(
    search: str | None = typer.Option(None, "--search", help="Keyword query."),
    profile: str | None = typer.Option(None, "--profile", help="Limit to posts by this profile (URL or ID)."),
    profile_id: str | None = typer.Option(None, "--profile-id", help="Limit to posts by this profile ID (faster)."),
    company: str | None = typer.Option(None, "--company", help="Limit to posts by this company (URL or ID)."),
    company_id: str | None = typer.Option(None, "--company-id", help="Limit to posts by this company ID (faster)."),
    authors_company: str | None = typer.Option(
        None, "--authors-company", help="All posts authored by employees of this company (URL or ID)."
    ),
    authors_industry_id: str | None = typer.Option(
        None, "--authors-industry-id", help="Limit to authors in this industry ID."
    ),
    mentioning_member: str | None = typer.Option(None, "--mentioning-member", help="Posts mentioning this member."),
    mentioning_company: str | None = typer.Option(None, "--mentioning-company", help="Posts mentioning this company."),
    content_type: str | None = typer.Option(
        None, "--content-type", help="Filter by content type (e.g. video, image, document)."
    ),
    author_keywords: str | None = typer.Option(None, "--author-keywords", help="Keyword match against the author."),
    group: str | None = typer.Option(None, "--group", help="Limit to posts in this group (URL or ID)."),
    posted_limit: str | None = typer.Option(
        None, "--posted-limit", help="Only posts within this window: 24h | week | month."
    ),
    scrape_posted_limit: str | None = typer.Option(
        None, "--scrape-posted-limit", help="Stop fetching once posts are older than this window."
    ),
    sort_by: str | None = typer.Option(None, "--sort-by", help="date | relevance."),
    page: int | None = typer.Option(None, "--page", help="1-based page number."),
    pagination_token: str | None = typer.Option(
        None, "--pagination-token", help="Token from a prior page (required for pages >= 2)."
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """Search posts by keyword, author, company, group, mention, content type, and recency."""
    with Como() as client:
        result = client.post.search(
            search=search,
            profile=profile,
            profile_id=profile_id,
            company=company,
            company_id=company_id,
            authors_company=authors_company,
            authors_industry_id=authors_industry_id,
            mentioning_member=mentioning_member,
            mentioning_company=mentioning_company,
            content_type=content_type,
            author_keywords=author_keywords,
            group=group,
            posted_limit=posted_limit,
            scrape_posted_limit=scrape_posted_limit,
            sort_by=sort_by,
            page=page,
            pagination_token=pagination_token,
        )
    emit(result, pretty=pretty)


@app.command("get")
def get_post(
    url: str = typer.Option(..., "--url", help="LinkedIn post or activity URL (required)."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """Get the FULL post (text, author, media, engagement counts) by URL."""
    with Como() as client:
        result = client.post.get(url=url)
    emit(result, pretty=pretty)


@app.command("company-posts")
def company_posts(
    company: str | None = typer.Option(None, "--company", help="Company URL or ID."),
    company_id: str | None = typer.Option(None, "--company-id", help="Numeric LinkedIn company ID (faster)."),
    company_universal_name: str | None = typer.Option(
        None, "--company-universal-name", help="Company universal name (URL slug)."
    ),
    posted_limit: str | None = typer.Option(
        None, "--posted-limit", help="Only posts within this window: 24h | week | month."
    ),
    scrape_posted_limit: str | None = typer.Option(
        None, "--scrape-posted-limit", help="Stop fetching once posts are older than this window."
    ),
    page: int | None = typer.Option(None, "--page", help="1-based page number."),
    pagination_token: str | None = typer.Option(
        None, "--pagination-token", help="Token from a prior page (required for pages >= 2)."
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """List posts authored by a company. Requires one of --company / --company-id /
    --company-universal-name."""
    with Como() as client:
        result = client.post.company_posts(
            company=company,
            company_id=company_id,
            company_universal_name=company_universal_name,
            posted_limit=posted_limit,
            scrape_posted_limit=scrape_posted_limit,
            page=page,
            pagination_token=pagination_token,
        )
    emit(result, pretty=pretty)


@app.command("user-posts")
def user_posts(
    profile: str | None = typer.Option(None, "--profile", help="Profile URL or ID."),
    profile_id: str | None = typer.Option(None, "--profile-id", help="Opaque profile ID (faster)."),
    profile_public_identifier: str | None = typer.Option(
        None, "--profile-public-identifier", help="Public identifier / vanity slug."
    ),
    posted_limit: str | None = typer.Option(
        None, "--posted-limit", help="Only posts within this window: 24h | week | month."
    ),
    scrape_posted_limit: str | None = typer.Option(
        None, "--scrape-posted-limit", help="Stop fetching once posts are older than this window."
    ),
    page: int | None = typer.Option(None, "--page", help="1-based page number."),
    pagination_token: str | None = typer.Option(
        None, "--pagination-token", help="Token from a prior page (required for pages >= 2)."
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """List posts authored by a person. Requires one of --profile / --profile-id /
    --profile-public-identifier."""
    with Como() as client:
        result = client.post.user_posts(
            profile=profile,
            profile_id=profile_id,
            profile_public_identifier=profile_public_identifier,
            posted_limit=posted_limit,
            scrape_posted_limit=scrape_posted_limit,
            page=page,
            pagination_token=pagination_token,
        )
    emit(result, pretty=pretty)


@app.command("comments")
def post_comments(
    post: str = typer.Option(..., "--post", help="Post or activity URL (required)."),
    sort_by: str | None = typer.Option(None, "--sort-by", help="relevance | recent."),
    page: int | None = typer.Option(None, "--page", help="1-based page number."),
    pagination_token: str | None = typer.Option(
        None, "--pagination-token", help="Token from a prior page (required for pages >= 2)."
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """List comments on a post."""
    with Como() as client:
        result = client.post.comments(
            post=post,
            sort_by=sort_by,
            page=page,
            pagination_token=pagination_token,
        )
    emit(result, pretty=pretty)


@app.command("reactions")
def post_reactions(
    post: str = typer.Option(..., "--post", help="Post or activity URL (required)."),
    page: int | None = typer.Option(None, "--page", help="1-based page number."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """List reactions on a post. Reactor profiles come back in opaque-ID URL form; `profile get`
    each (with --main) to resolve normal URLs."""
    with Como() as client:
        result = client.post.reactions(post=post, page=page)
    emit(result, pretty=pretty)


@app.command("group-posts")
def group_posts(
    group: str | None = typer.Option(None, "--group", help="Group URL or ID."),
    search: str | None = typer.Option(None, "--search", help="Keyword filter within the group."),
    sort_by: str | None = typer.Option(None, "--sort-by", help="date | relevance."),
    page: int | None = typer.Option(None, "--page", help="1-based page number."),
    pagination_token: str | None = typer.Option(
        None, "--pagination-token", help="Token from a prior page (required for pages >= 2)."
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """List posts in a group."""
    with Como() as client:
        result = client.post.group_posts(
            group=group,
            search=search,
            sort_by=sort_by,
            page=page,
            pagination_token=pagination_token,
        )
    emit(result, pretty=pretty)


@app.command("comment-replies")
def comment_replies(
    comment: str = typer.Option(..., "--comment", help="Comment URL (required)."),
    page: int | None = typer.Option(None, "--page", help="1-based page number."),
    pagination_token: str | None = typer.Option(
        None, "--pagination-token", help="Token from a prior page (required for pages >= 2)."
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """List replies to a comment."""
    with Como() as client:
        result = client.post.comment_replies(
            comment=comment,
            page=page,
            pagination_token=pagination_token,
        )
    emit(result, pretty=pretty)


@app.command("comment-reactions")
def comment_reactions(
    comment: str = typer.Option(..., "--comment", help="Comment URL (required)."),
    page: int | None = typer.Option(None, "--page", help="1-based page number."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty, syntax-highlighted JSON."),
) -> None:
    """List reactions on a comment."""
    with Como() as client:
        result = client.post.comment_reactions(comment=comment, page=page)
    emit(result, pretty=pretty)
