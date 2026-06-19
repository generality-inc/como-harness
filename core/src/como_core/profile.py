from __future__ import annotations

from ._common import BaseModel, CostMixin, DatePart, LocationField, Pagination
from .post import Comment, Post, Reaction


class _CurrentPosition(BaseModel):
    company_name: str | None = None


class Experience(BaseModel):
    company_name: str | None = None
    duration: str | None = None
    position: str | None = None
    location: str | None = None
    company_link: str | None = None
    description: str | None = None
    start_date: DatePart | None = None
    end_date: DatePart | None = None
    employment_type: str | None = None


class Education(BaseModel):
    title: str | None = None
    link: str | None = None
    degree: str | None = None
    start_date: DatePart | None = None
    end_date: DatePart | None = None


class Certification(BaseModel):
    title: str | None = None
    issued_at: str | None = None
    issued_by: str | None = None
    issued_by_link: str | None = None


class Skill(BaseModel):
    name: str | None = None


class Language(BaseModel):
    language: str | None = None
    proficiency: str | None = None


class _Recommendation(BaseModel):
    given_by: str | None = None
    given_at: str | None = None
    given_by_link: str | None = None
    description: str | None = None


class _Project(BaseModel):
    title: str | None = None
    description: str | None = None
    start_date: DatePart | None = None
    end_date: DatePart | None = None


class _Publication(BaseModel):
    title: str | None = None
    published_at: str | None = None
    description: str | None = None
    link: str | None = None


class _Featured(BaseModel):
    images: list[str] | None = None
    link: str | None = None
    title: str | None = None
    subtitle: str | None = None


class Profile(CostMixin):
    id: str | None = None
    public_identifier: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    headline: str | None = None
    about: str | None = None
    linkedin_url: str | None = None
    photo: str | None = None
    registered_at: str | None = None
    top_skills: str | None = None
    connections_count: int | None = None
    follower_count: int | None = None
    open_to_work: bool | None = None
    hiring: bool | None = None
    verified: bool | None = None
    location: LocationField | None = None
    current_position: list[_CurrentPosition] | None = None
    experience: list[Experience] | None = None
    education: list[Education] | None = None
    certifications: list[Certification] | None = None
    received_recommendations: list[_Recommendation] | None = None
    skills: list[Skill] | None = None
    languages: list[Language] | None = None
    projects: list[_Project] | None = None
    publications: list[_Publication] | None = None
    featured: _Featured | None = None
    email: str | None = None


class ProfileSearchHit(BaseModel):
    id: str | None = None
    public_identifier: str | None = None
    name: str | None = None
    position: str | None = None
    location: LocationField | None = None
    linkedin_url: str | None = None
    photo: str | None = None
    hidden: bool | None = None


class ProfileSearchResult(CostMixin):
    elements: list[ProfileSearchHit] = []
    pagination: Pagination | None = None


class ProfilePostsResult(CostMixin):
    elements: list[Post] = []
    pagination: Pagination | None = None


class ProfileCommentsResult(CostMixin):
    elements: list[Comment] = []
    pagination: Pagination | None = None


class ProfileReactionsResult(CostMixin):
    elements: list[Reaction] = []
    pagination: Pagination | None = None
