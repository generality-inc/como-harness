from __future__ import annotations

from ._common import BaseModel, LocationField, Pagination


class _JobCompany(BaseModel):
    name: str | None = None
    universal_name: str | None = None
    linkedin_url: str | None = None


class _JobSalary(BaseModel):
    min: str | None = None
    max: str | None = None
    currency: str | None = None
    text: str | None = None


class Job(BaseModel):
    id: str | None = None
    title: str | None = None
    linkedin_url: str | None = None
    job_state: str | None = None
    posted_date: str | None = None
    description_text: str | None = None
    description_html: str | None = None
    location: LocationField | None = None
    employment_type: str | None = None
    workplace_type: str | None = None
    work_remote_allowed: bool | None = None
    easy_apply_url: str | None = None
    applicants: int | None = None
    company_name: str | None = None
    company_logo: str | None = None
    company_link: str | None = None
    company_universal_name: str | None = None
    salary: _JobSalary | None = None
    views: int | None = None
    expire_at: str | None = None
    new: bool | None = None
    job_application_limit_reached: bool | None = None
    applicant_tracking_system: str | None = None


class JobSearchHit(BaseModel):
    id: str | None = None
    url: str | None = None
    title: str | None = None
    posted_date: str | None = None
    company: _JobCompany | None = None
    location: LocationField | None = None
    easy_apply: bool | None = None


class JobSearchResult(BaseModel):
    elements: list[JobSearchHit] = []
    pagination: Pagination | None = None
