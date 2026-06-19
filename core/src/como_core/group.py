from __future__ import annotations

from ._common import BaseModel, CostMixin, MediaImage, Pagination


class _GroupCreatedAt(BaseModel):
    date: str | None = None
    timestamp: int | None = None


class _GroupAdminProfile(BaseModel):
    id: str | None = None
    linkedin_url: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    headline: str | None = None
    # Upstream returns either a media object ({url,width,height}) or a bare URL
    # string — union both so a media object never raises (it crashed group search).
    picture: MediaImage | str | None = None


class _GroupAdmins(BaseModel):
    total_count: int | None = None
    text: str | None = None
    profiles: list[_GroupAdminProfile] | None = None


class Group(CostMixin):
    id: str | None = None
    linkedin_url: str | None = None
    name: str | None = None
    member_count: int | None = None
    logo: MediaImage | None = None
    hero_image: MediaImage | None = None
    description: str | None = None
    rules: str | None = None
    created_at: _GroupCreatedAt | None = None
    group_plus_status_active: bool | None = None
    post_approval_enabled: bool | None = None
    invitation_level: str | None = None
    welcome_note: str | None = None
    automated_welcome_note_enabled: bool | None = None
    public_visibility: bool | None = None
    admins: _GroupAdmins | None = None


class _GroupPrimaryAction(BaseModel):
    label: str | None = None
    value: str | None = None


class GroupSearchHit(BaseModel):
    id: str | None = None
    linkedin_url: str | None = None
    name: str | None = None
    members: str | None = None
    summary: str | None = None
    # media object ({url,width,height}) or bare URL — union both (was str-only,
    # which raised on the media object and crashed group search).
    picture: MediaImage | str | None = None
    primary_actions: list[_GroupPrimaryAction] | None = None


class GroupSearchResult(CostMixin):
    elements: list[GroupSearchHit] = []
    pagination: Pagination | None = None
