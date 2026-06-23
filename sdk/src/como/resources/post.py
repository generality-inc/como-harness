from __future__ import annotations

from como_core.post import (
    CommentReactionsResult,
    CommentRepliesResult,
    CommentsResult,
    Post,
    PostSearchResult,
    PostsResult,
    ReactionsResult,
)

from .._params import clean_params, require_one_of
from ._base import AsyncResource, SyncResource, lift_cost

_PATH_SEARCH = "/v1/ghost/post-search"
_PATH_GET = "/v1/ghost/post"
_PATH_COMPANY_POSTS = "/v1/ghost/company-posts"
_PATH_USER_POSTS = "/v1/ghost/profile-posts"
_PATH_COMMENTS = "/v1/ghost/post-comments"
_PATH_REACTIONS = "/v1/ghost/post-reactions"
_PATH_COMMENT_REPLIES = "/v1/ghost/post-comment-replies"
_PATH_COMMENT_REACTIONS = "/v1/ghost/comment-reactions"


def _search_params(**kwargs) -> dict[str, str]:
    return clean_params(
        {
            "search": kwargs.get("search"),
            "profile": kwargs.get("profile"),
            "profileId": kwargs.get("profile_id"),
            "company": kwargs.get("company"),
            "companyId": kwargs.get("company_id"),
            "authorsCompany": kwargs.get("authors_company"),
            "authorsIndustryId": kwargs.get("authors_industry_id"),
            "mentioningMember": kwargs.get("mentioning_member"),
            "mentioningCompany": kwargs.get("mentioning_company"),
            "contentType": kwargs.get("content_type"),
            "authorKeywords": kwargs.get("author_keywords"),
            "group": kwargs.get("group"),
            "postedLimit": kwargs.get("posted_limit"),
            "historyLimit": kwargs.get("history_limit"),
            "sortBy": kwargs.get("sort_by"),
            "page": kwargs.get("page"),
            "paginationToken": kwargs.get("pagination_token"),
        }
    )


def _get_params(*, url) -> dict[str, str]:
    if url is None:
        raise ValueError("url is required.")
    return clean_params({"url": url})


def _company_posts_params(
    *, company, company_id, company_universal_name, posted_limit, history_limit, page, pagination_token
) -> dict[str, str]:
    require_one_of(company=company, company_id=company_id, company_universal_name=company_universal_name)
    return clean_params(
        {
            "company": company,
            "companyId": company_id,
            "companyUniversalName": company_universal_name,
            "postedLimit": posted_limit,
            "historyLimit": history_limit,
            "page": page,
            "paginationToken": pagination_token,
        }
    )


def _user_posts_params(
    *, profile, profile_id, profile_public_identifier, posted_limit, history_limit, page, pagination_token
) -> dict[str, str]:
    require_one_of(profile=profile, profile_id=profile_id, profile_public_identifier=profile_public_identifier)
    return clean_params(
        {
            "profile": profile,
            "profileId": profile_id,
            "profilePublicIdentifier": profile_public_identifier,
            "postedLimit": posted_limit,
            "historyLimit": history_limit,
            "page": page,
            "paginationToken": pagination_token,
        }
    )


def _comments_params(*, post, sort_by, page, pagination_token) -> dict[str, str]:
    if post is None:
        raise ValueError("post is required.")
    return clean_params(
        {
            "post": post,
            "sortBy": sort_by,
            "page": page,
            "paginationToken": pagination_token,
        }
    )


def _reactions_params(*, post, page) -> dict[str, str]:
    if post is None:
        raise ValueError("post is required.")
    return clean_params({"post": post, "page": page})


def _comment_replies_params(*, comment, page, pagination_token) -> dict[str, str]:
    if comment is None:
        raise ValueError("comment is required.")
    return clean_params(
        {
            "url": comment,
            "page": page,
            "paginationToken": pagination_token,
        }
    )


def _comment_reactions_params(*, comment, page) -> dict[str, str]:
    if comment is None:
        raise ValueError("comment is required.")
    return clean_params({"url": comment, "page": page})


class PostResource(SyncResource):
    def search(
        self,
        *,
        search: str | None = None,
        profile: str | None = None,
        profile_id: str | None = None,
        company: str | None = None,
        company_id: str | None = None,
        authors_company: str | None = None,
        authors_industry_id: str | None = None,
        mentioning_member: str | None = None,
        mentioning_company: str | None = None,
        content_type: str | None = None,
        author_keywords: str | None = None,
        group: str | None = None,
        posted_limit: str | None = None,
        history_limit: str | None = None,
        sort_by: str | None = None,
        page: int | None = None,
        pagination_token: str | None = None,
    ) -> PostSearchResult:
        params = _search_params(
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
            history_limit=history_limit,
            sort_by=sort_by,
            page=page,
            pagination_token=pagination_token,
        )
        body = self._t.get(_PATH_SEARCH, params=params)
        return PostSearchResult.model_validate(body)

    def get(self, *, url: str) -> Post:
        params = _get_params(url=url)
        body = self._t.get(_PATH_GET, params=params)
        return lift_cost(Post.model_validate(body.get("element") or {}), body)

    def company_posts(
        self,
        *,
        company: str | None = None,
        company_id: str | None = None,
        company_universal_name: str | None = None,
        posted_limit: str | None = None,
        history_limit: str | None = None,
        page: int | None = None,
        pagination_token: str | None = None,
    ) -> PostsResult:
        params = _company_posts_params(
            company=company,
            company_id=company_id,
            company_universal_name=company_universal_name,
            posted_limit=posted_limit,
            history_limit=history_limit,
            page=page,
            pagination_token=pagination_token,
        )
        body = self._t.get(_PATH_COMPANY_POSTS, params=params)
        return PostsResult.model_validate(body)

    def user_posts(
        self,
        *,
        profile: str | None = None,
        profile_id: str | None = None,
        profile_public_identifier: str | None = None,
        posted_limit: str | None = None,
        history_limit: str | None = None,
        page: int | None = None,
        pagination_token: str | None = None,
    ) -> PostsResult:
        params = _user_posts_params(
            profile=profile,
            profile_id=profile_id,
            profile_public_identifier=profile_public_identifier,
            posted_limit=posted_limit,
            history_limit=history_limit,
            page=page,
            pagination_token=pagination_token,
        )
        body = self._t.get(_PATH_USER_POSTS, params=params)
        return PostsResult.model_validate(body)

    def comments(
        self,
        *,
        post: str,
        sort_by: str | None = None,
        page: int | None = None,
        pagination_token: str | None = None,
    ) -> CommentsResult:
        params = _comments_params(post=post, sort_by=sort_by, page=page, pagination_token=pagination_token)
        body = self._t.get(_PATH_COMMENTS, params=params)
        return CommentsResult.model_validate(body)

    def reactions(self, *, post: str, page: int | None = None) -> ReactionsResult:
        params = _reactions_params(post=post, page=page)
        body = self._t.get(_PATH_REACTIONS, params=params)
        return ReactionsResult.model_validate(body)

    def group_posts(
        self,
        *,
        group: str | None = None,
        search: str | None = None,
        sort_by: str | None = None,
        page: int | None = None,
        pagination_token: str | None = None,
    ) -> PostSearchResult:
        params = _search_params(
            group=group,
            search=search,
            sort_by=sort_by,
            page=page,
            pagination_token=pagination_token,
        )
        body = self._t.get(_PATH_SEARCH, params=params)
        return PostSearchResult.model_validate(body)

    def comment_replies(
        self,
        *,
        comment: str,
        page: int | None = None,
        pagination_token: str | None = None,
    ) -> CommentRepliesResult:
        params = _comment_replies_params(comment=comment, page=page, pagination_token=pagination_token)
        body = self._t.get(_PATH_COMMENT_REPLIES, params=params)
        return CommentRepliesResult.model_validate(body)

    def comment_reactions(self, *, comment: str, page: int | None = None) -> CommentReactionsResult:
        params = _comment_reactions_params(comment=comment, page=page)
        body = self._t.get(_PATH_COMMENT_REACTIONS, params=params)
        return CommentReactionsResult.model_validate(body)


class AsyncPostResource(AsyncResource):
    async def search(
        self,
        *,
        search: str | None = None,
        profile: str | None = None,
        profile_id: str | None = None,
        company: str | None = None,
        company_id: str | None = None,
        authors_company: str | None = None,
        authors_industry_id: str | None = None,
        mentioning_member: str | None = None,
        mentioning_company: str | None = None,
        content_type: str | None = None,
        author_keywords: str | None = None,
        group: str | None = None,
        posted_limit: str | None = None,
        history_limit: str | None = None,
        sort_by: str | None = None,
        page: int | None = None,
        pagination_token: str | None = None,
    ) -> PostSearchResult:
        params = _search_params(
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
            history_limit=history_limit,
            sort_by=sort_by,
            page=page,
            pagination_token=pagination_token,
        )
        body = await self._t.get(_PATH_SEARCH, params=params)
        return PostSearchResult.model_validate(body)

    async def get(self, *, url: str) -> Post:
        params = _get_params(url=url)
        body = await self._t.get(_PATH_GET, params=params)
        return lift_cost(Post.model_validate(body.get("element") or {}), body)

    async def company_posts(
        self,
        *,
        company: str | None = None,
        company_id: str | None = None,
        company_universal_name: str | None = None,
        posted_limit: str | None = None,
        history_limit: str | None = None,
        page: int | None = None,
        pagination_token: str | None = None,
    ) -> PostsResult:
        params = _company_posts_params(
            company=company,
            company_id=company_id,
            company_universal_name=company_universal_name,
            posted_limit=posted_limit,
            history_limit=history_limit,
            page=page,
            pagination_token=pagination_token,
        )
        body = await self._t.get(_PATH_COMPANY_POSTS, params=params)
        return PostsResult.model_validate(body)

    async def user_posts(
        self,
        *,
        profile: str | None = None,
        profile_id: str | None = None,
        profile_public_identifier: str | None = None,
        posted_limit: str | None = None,
        history_limit: str | None = None,
        page: int | None = None,
        pagination_token: str | None = None,
    ) -> PostsResult:
        params = _user_posts_params(
            profile=profile,
            profile_id=profile_id,
            profile_public_identifier=profile_public_identifier,
            posted_limit=posted_limit,
            history_limit=history_limit,
            page=page,
            pagination_token=pagination_token,
        )
        body = await self._t.get(_PATH_USER_POSTS, params=params)
        return PostsResult.model_validate(body)

    async def comments(
        self,
        *,
        post: str,
        sort_by: str | None = None,
        page: int | None = None,
        pagination_token: str | None = None,
    ) -> CommentsResult:
        params = _comments_params(post=post, sort_by=sort_by, page=page, pagination_token=pagination_token)
        body = await self._t.get(_PATH_COMMENTS, params=params)
        return CommentsResult.model_validate(body)

    async def reactions(self, *, post: str, page: int | None = None) -> ReactionsResult:
        params = _reactions_params(post=post, page=page)
        body = await self._t.get(_PATH_REACTIONS, params=params)
        return ReactionsResult.model_validate(body)

    async def group_posts(
        self,
        *,
        group: str | None = None,
        search: str | None = None,
        sort_by: str | None = None,
        page: int | None = None,
        pagination_token: str | None = None,
    ) -> PostSearchResult:
        params = _search_params(
            group=group,
            search=search,
            sort_by=sort_by,
            page=page,
            pagination_token=pagination_token,
        )
        body = await self._t.get(_PATH_SEARCH, params=params)
        return PostSearchResult.model_validate(body)

    async def comment_replies(
        self,
        *,
        comment: str,
        page: int | None = None,
        pagination_token: str | None = None,
    ) -> CommentRepliesResult:
        params = _comment_replies_params(comment=comment, page=page, pagination_token=pagination_token)
        body = await self._t.get(_PATH_COMMENT_REPLIES, params=params)
        return CommentRepliesResult.model_validate(body)

    async def comment_reactions(self, *, comment: str, page: int | None = None) -> CommentReactionsResult:
        params = _comment_reactions_params(comment=comment, page=page)
        body = await self._t.get(_PATH_COMMENT_REACTIONS, params=params)
        return CommentReactionsResult.model_validate(body)
