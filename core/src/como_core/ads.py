from __future__ import annotations

from typing import Any

from ._common import BaseModel, Pagination


class _AdAdvertiser(BaseModel):
    name: str | None = None
    linkedin_url: str | None = None
    image_url: str | None = None
    headline: str | None = None


class _AdSlide(BaseModel):
    image_url: str | None = None
    target_url: str | None = None
    title: str | None = None


class _AdContent(BaseModel):
    description: str | None = None
    image_url: str | None = None
    video_thumbnail_url: str | None = None
    video_source: Any | None = None
    target_url: str | None = None
    headline: str | None = None
    cta_label: str | None = None
    slides: list[_AdSlide] | None = None


class _AdVariant(BaseModel):
    advertiser: _AdAdvertiser | None = None
    content: _AdContent | None = None
    creative_type: str | None = None


class _AdAbout(BaseModel):
    format: str | None = None
    advertiser_name: str | None = None
    advertiser_url: str | None = None
    paid_by: str | None = None
    ran_from: str | None = None
    ran_to: str | None = None


class _AdImpressionsByCountry(BaseModel):
    name: str | None = None
    percentage: str | None = None


class _AdImpressions(BaseModel):
    total: str | None = None
    by_country: list[_AdImpressionsByCountry] | None = None


class _AdTargetingSegment(BaseModel):
    name: str | None = None
    includes: list[str] | None = None
    excludes: list[str] | None = None


class _AdTargetingParameter(BaseModel):
    name: str | None = None
    targeted: bool | None = None
    excluded: bool | None = None


class _AdTargeting(BaseModel):
    segments: list[_AdTargetingSegment] | None = None
    parameters: list[_AdTargetingParameter] | None = None


class Ad(BaseModel):
    id: str | None = None
    variants: list[_AdVariant] | None = None
    about: _AdAbout | None = None
    impressions: _AdImpressions | None = None
    targeting: _AdTargeting | None = None


class AdSearchResult(BaseModel):
    elements: list[dict] = []
    pagination: Pagination | None = None
