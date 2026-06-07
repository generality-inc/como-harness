from __future__ import annotations

from typing import Any

from ._common import BaseModel, DatePart, LocationField, MediaImage, Pagination, ParsedLocation


class _Industry(BaseModel):
    id: str | None = None
    name: str | None = None
    urn: str | None = None
    title: str | None = None
    hierarchy: str | None = None


class _EmployeeCountRange(BaseModel):
    start: int | None = None
    end: int | None = None


class _Headquarter(BaseModel):
    geographic_area: str | None = None
    city: str | None = None
    country: str | None = None
    postal_code: str | None = None
    line1: str | None = None
    line2: str | None = None
    description: str | None = None
    parsed: ParsedLocation | None = None


class _CompanyLocation(BaseModel):
    localized_name: str | None = None
    headquarter: bool | None = None
    description: str | None = None
    country: str | None = None
    geographic_area: str | None = None
    city: str | None = None
    postal_code: str | None = None
    line1: str | None = None
    line2: str | None = None


class _FundingMoney(BaseModel):
    amount: str | None = None
    currency_code: str | None = None


class _LastFundingRound(BaseModel):
    localized_funding_type: str | None = None
    lead_investors: list[Any] | None = None
    money_raised: _FundingMoney | None = None
    funding_round_url: str | None = None
    announced_on: DatePart | None = None
    number_of_other_investors: int | None = None
    investors_url: str | None = None


class _CrunchbaseFundingData(BaseModel):
    number_of_funding_rounds: int | None = None
    last_funding_round: _LastFundingRound | None = None
    organization_url: str | None = None
    updated_at: int | None = None
    funding_rounds_url: str | None = None


class Company(BaseModel):
    id: str | None = None
    universal_name: str | None = None
    name: str | None = None
    tagline: str | None = None
    website: str | None = None
    linkedin_url: str | None = None
    logo: str | None = None
    founded_on: DatePart | None = None
    employee_count: int | None = None
    employee_count_range: _EmployeeCountRange | None = None
    follower_count: int | None = None
    description: str | None = None
    headquarter: _Headquarter | None = None
    locations: list[_CompanyLocation] | None = None
    specialities: list[str] | None = None
    industries: list[_Industry] | None = None
    logos: list[MediaImage] | None = None
    background_covers: list[MediaImage] | None = None
    active: bool | None = None
    job_search_url: str | None = None
    phone: str | None = None
    crunchbase_funding_data: _CrunchbaseFundingData | None = None
    page_verified: bool | None = None


class CompanySearchHit(BaseModel):
    id: str | None = None
    name: str | None = None
    industries: str | None = None
    location: LocationField | None = None
    followers: str | None = None
    summary: str | None = None
    logo: str | None = None
    linkedin_url: str | None = None
    universal_name: str | None = None


class CompanySearchResult(BaseModel):
    elements: list[CompanySearchHit] = []
    pagination: Pagination | None = None
