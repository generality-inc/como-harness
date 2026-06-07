from __future__ import annotations

from ._common import BaseModel, MediaImage, Pagination


class _GroupCreatedAt(BaseModel):
    date: str | None = None
    timestamp: int | None = None


class _GroupAdminProfile(BaseModel):
    id: str | None = None
    linkedin_url: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    headline: str | None = None
    picture: str | None = None


class _GroupAdmins(BaseModel):
    total_count: int | None = None
    text: str | None = None
    profiles: list[_GroupAdminProfile] | None = None


class Group(BaseModel):
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
    picture: str | None = None
    primary_actions: list[_GroupPrimaryAction] | None = None


class GroupSearchResult(BaseModel):
    elements: list[GroupSearchHit] = []
    pagination: Pagination | None = None
