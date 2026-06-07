from __future__ import annotations

from como_core.profile import (
    Profile,
    ProfileCommentsResult,
    ProfilePostsResult,
    ProfileReactionsResult,
    ProfileSearchResult,
)

from .._params import clean_params, require_one_of
from ._base import AsyncResource, SyncResource

_PATH_GET = "/v1/ghost/profile"
_PATH_SEARCH = "/v1/ghost/profile-search"
_PATH_POSTS = "/v1/ghost/profile-posts"
_PATH_COMMENTS = "/v1/ghost/profile-comments"
_PATH_REACTIONS = "/v1/ghost/profile-reactions"


def _get_params(
    *,
    url: str | None,
    public_identifier: str | None,
    profile_id: str | None,
    main: bool | None,
    find_email: bool | None,
    skip_smtp: bool | None,
    include_about_profile: bool | None,
) -> dict[str, str]:
    require_one_of(url=url, public_identifier=public_identifier, profile_id=profile_id)
    return clean_params(
        {
            "url": url,
            "publicIdentifier": public_identifier,
            "profileId": profile_id,
            "main": main,
            "findEmail": find_email,
            "skipSmtp": skip_smtp,
            "includeAboutProfile": include_about_profile,
        }
    )


def _search_params(**kwargs) -> dict[str, str]:
    return clean_params(
        {
            "search": kwargs.get("search"),
            "currentCompany": kwargs.get("current_company"),
            "pastCompany": kwargs.get("past_company"),
            "school": kwargs.get("school"),
            "firstName": kwargs.get("first_name"),
            "lastName": kwargs.get("last_name"),
            "title": kwargs.get("title"),
            "location": kwargs.get("location"),
            "geoId": kwargs.get("geo_id"),
            "industryId": kwargs.get("industry_id"),
            "keywordsCompany": kwargs.get("keywords_company"),
            "keywordsSchool": kwargs.get("keywords_school"),
            "followerOf": kwargs.get("follower_of"),
            "page": kwargs.get("page"),
        }
    )


def _posts_params(*, profile, profile_id, profile_public_identifier, page, pagination_token) -> dict[str, str]:
    require_one_of(profile=profile, profile_id=profile_id, profile_public_identifier=profile_public_identifier)
    return clean_params(
        {
            "profile": profile,
            "profileId": profile_id,
            "profilePublicIdentifier": profile_public_identifier,
            "page": page,
            "paginationToken": pagination_token,
        }
    )


def _comments_params(*, profile, profile_id, page, pagination_token) -> dict[str, str]:
    require_one_of(profile=profile, profile_id=profile_id)
    return clean_params(
        {
            "profile": profile,
            "profileId": profile_id,
            "page": page,
            "paginationToken": pagination_token,
        }
    )


def _reactions_params(*, profile, profile_id, page, pagination_token) -> dict[str, str]:
    require_one_of(profile=profile, profile_id=profile_id)
    return clean_params(
        {
            "profile": profile,
            "profileId": profile_id,
            "page": page,
            "paginationToken": pagination_token,
        }
    )


class ProfileResource(SyncResource):
    def get(
        self,
        *,
        url: str | None = None,
        public_identifier: str | None = None,
        profile_id: str | None = None,
        main: bool | None = None,
        find_email: bool | None = None,
        skip_smtp: bool | None = None,
        include_about_profile: bool | None = None,
    ) -> Profile:
        params = _get_params(
            url=url,
            public_identifier=public_identifier,
            profile_id=profile_id,
            main=main,
            find_email=find_email,
            skip_smtp=skip_smtp,
            include_about_profile=include_about_profile,
        )
        body = self._t.get(_PATH_GET, params=params)
        return Profile.model_validate(body.get("element") or {})

    def search(
        self,
        *,
        search: str | None = None,
        current_company: str | None = None,
        past_company: str | None = None,
        school: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        title: str | None = None,
        location: str | None = None,
        geo_id: str | None = None,
        industry_id: str | None = None,
        keywords_company: str | None = None,
        keywords_school: str | None = None,
        follower_of: str | None = None,
        page: int | None = None,
    ) -> ProfileSearchResult:
        params = _search_params(
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
        body = self._t.get(_PATH_SEARCH, params=params)
        return ProfileSearchResult.model_validate(body)

    def posts(
        self,
        *,
        profile: str | None = None,
        profile_id: str | None = None,
        profile_public_identifier: str | None = None,
        page: int | None = None,
        pagination_token: str | None = None,
    ) -> ProfilePostsResult:
        params = _posts_params(
            profile=profile,
            profile_id=profile_id,
            profile_public_identifier=profile_public_identifier,
            page=page,
            pagination_token=pagination_token,
        )
        body = self._t.get(_PATH_POSTS, params=params)
        return ProfilePostsResult.model_validate(body)

    def comments(
        self,
        *,
        profile: str | None = None,
        profile_id: str | None = None,
        page: int | None = None,
        pagination_token: str | None = None,
    ) -> ProfileCommentsResult:
        params = _comments_params(
            profile=profile,
            profile_id=profile_id,
            page=page,
            pagination_token=pagination_token,
        )
        body = self._t.get(_PATH_COMMENTS, params=params)
        return ProfileCommentsResult.model_validate(body)

    def reactions(
        self,
        *,
        profile: str | None = None,
        profile_id: str | None = None,
        page: int | None = None,
        pagination_token: str | None = None,
    ) -> ProfileReactionsResult:
        params = _reactions_params(
            profile=profile,
            profile_id=profile_id,
            page=page,
            pagination_token=pagination_token,
        )
        body = self._t.get(_PATH_REACTIONS, params=params)
        return ProfileReactionsResult.model_validate(body)


class AsyncProfileResource(AsyncResource):
    async def get(
        self,
        *,
        url: str | None = None,
        public_identifier: str | None = None,
        profile_id: str | None = None,
        main: bool | None = None,
        find_email: bool | None = None,
        skip_smtp: bool | None = None,
        include_about_profile: bool | None = None,
    ) -> Profile:
        params = _get_params(
            url=url,
            public_identifier=public_identifier,
            profile_id=profile_id,
            main=main,
            find_email=find_email,
            skip_smtp=skip_smtp,
            include_about_profile=include_about_profile,
        )
        body = await self._t.get(_PATH_GET, params=params)
        return Profile.model_validate(body.get("element") or {})

    async def search(
        self,
        *,
        search: str | None = None,
        current_company: str | None = None,
        past_company: str | None = None,
        school: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        title: str | None = None,
        location: str | None = None,
        geo_id: str | None = None,
        industry_id: str | None = None,
        keywords_company: str | None = None,
        keywords_school: str | None = None,
        follower_of: str | None = None,
        page: int | None = None,
    ) -> ProfileSearchResult:
        params = _search_params(
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
        body = await self._t.get(_PATH_SEARCH, params=params)
        return ProfileSearchResult.model_validate(body)

    async def posts(
        self,
        *,
        profile: str | None = None,
        profile_id: str | None = None,
        profile_public_identifier: str | None = None,
        page: int | None = None,
        pagination_token: str | None = None,
    ) -> ProfilePostsResult:
        params = _posts_params(
            profile=profile,
            profile_id=profile_id,
            profile_public_identifier=profile_public_identifier,
            page=page,
            pagination_token=pagination_token,
        )
        body = await self._t.get(_PATH_POSTS, params=params)
        return ProfilePostsResult.model_validate(body)

    async def comments(
        self,
        *,
        profile: str | None = None,
        profile_id: str | None = None,
        page: int | None = None,
        pagination_token: str | None = None,
    ) -> ProfileCommentsResult:
        params = _comments_params(
            profile=profile,
            profile_id=profile_id,
            page=page,
            pagination_token=pagination_token,
        )
        body = await self._t.get(_PATH_COMMENTS, params=params)
        return ProfileCommentsResult.model_validate(body)

    async def reactions(
        self,
        *,
        profile: str | None = None,
        profile_id: str | None = None,
        page: int | None = None,
        pagination_token: str | None = None,
    ) -> ProfileReactionsResult:
        params = _reactions_params(
            profile=profile,
            profile_id=profile_id,
            page=page,
            pagination_token=pagination_token,
        )
        body = await self._t.get(_PATH_REACTIONS, params=params)
        return ProfileReactionsResult.model_validate(body)
