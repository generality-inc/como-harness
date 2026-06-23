from __future__ import annotations

from typing import Any

from ._common import BaseModel, CostMixin, MediaImage, Pagination


class PostAuthor(BaseModel):
    id: str | None = None
    urn: str | None = None
    public_identifier: str | None = None
    universal_name: str | None = None
    name: str | None = None
    linkedin_url: str | None = None
    type: str | None = None
    info: str | None = None
    website: Any | None = None
    website_label: Any | None = None
    avatar: MediaImage | None = None


class _PostedAt(BaseModel):
    timestamp: int | None = None
    date: str | None = None
    posted_ago_short: str | None = None
    posted_ago_text: str | None = None


class _Article(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    link: str | None = None
    link_label: str | None = None
    description: str | None = None
    image: MediaImage | None = None


class _PostVideo(BaseModel):
    thumbnail_url: str | None = None
    video_url: str | None = None


class _SocialContent(BaseModel):
    share_url: str | None = None


class _ReactionCount(BaseModel):
    type: str | None = None
    count: int | None = None


class _Engagement(BaseModel):
    likes: int | None = None
    comments: int | None = None
    shares: int | None = None
    reactions: list[_ReactionCount] | None = None


class Post(CostMixin):
    id: str | None = None
    content: str | None = None
    linkedin_url: str | None = None
    author: PostAuthor | None = None
    posted_at: _PostedAt | None = None
    post_images: list[MediaImage] | None = None
    post_video: _PostVideo | None = None
    article: _Article | None = None
    repost_id: str | None = None
    repost: Any | None = None
    reposted_by: dict | None = None
    newsletter_url: str | None = None
    newsletter_title: str | None = None
    social_content: _SocialContent | None = None
    engagement: _Engagement | None = None


class PostActor(BaseModel):
    id: str | None = None
    name: str | None = None
    linkedin_url: str | None = None
    position: str | None = None
    picture_url: str | None = None
    picture: MediaImage | None = None
    author: bool | None = None


class Comment(BaseModel):
    id: str | None = None
    linkedin_url: str | None = None
    commentary: str | None = None
    created_at: str | None = None
    created_at_timestamp: int | None = None
    num_comments: int | None = None
    num_shares: int | None = None
    num_impressions: int | None = None
    reaction_type_counts: list[_ReactionCount] | None = None
    post_id: str | None = None
    actor: PostActor | None = None
    pinned: bool | None = None
    contributed: bool | None = None
    edited: bool | None = None


class Reaction(BaseModel):
    id: str | None = None
    reaction_type: str | None = None
    post_id: str | None = None
    actor: PostActor | None = None


class CommentReaction(BaseModel):
    id: str | None = None
    reaction_type: str | None = None
    comment_id: str | None = None
    actor: PostActor | None = None


class PostsResult(CostMixin):
    elements: list[Post] = []
    pagination: Pagination | None = None


class PostSearchResult(CostMixin):
    elements: list[Post] = []
    pagination: Pagination | None = None


class CommentsResult(CostMixin):
    elements: list[Comment] = []
    pagination: Pagination | None = None


class ReactionsResult(CostMixin):
    elements: list[Reaction] = []
    pagination: Pagination | None = None


class CommentRepliesResult(CostMixin):
    elements: list[Comment] = []
    pagination: Pagination | None = None


class CommentReactionsResult(CostMixin):
    elements: list[CommentReaction] = []
    pagination: Pagination | None = None
