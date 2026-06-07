from __future__ import annotations

from ._common import BaseModel, DatePart, LocationField, Pagination


class _LeadTenure(BaseModel):
    num_years: int | None = None
    num_months: int | None = None


class _LeadCurrentPosition(BaseModel):
    company_name: str | None = None
    title: str | None = None
    description: str | None = None
    started_on: DatePart | None = None
    company_id: str | None = None
    company_linkedin_url: str | None = None
    tenure_at_position: _LeadTenure | None = None
    tenure_at_company: _LeadTenure | None = None


class Lead(BaseModel):
    id: str | None = None
    linkedin_url: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    open_profile: bool | None = None
    premium: bool | None = None
    location: LocationField | None = None
    picture_url: str | None = None
    current_positions: list[_LeadCurrentPosition] | None = None


class LeadSearchResult(BaseModel):
    elements: list[Lead] = []
    pagination: Pagination | None = None
