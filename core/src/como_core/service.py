from __future__ import annotations

from ._common import BaseModel, CostMixin, LocationField, Pagination


class ServiceSearchHit(BaseModel):
    id: str | None = None
    public_identifier: str | None = None
    name: str | None = None
    position: str | None = None
    location: LocationField | None = None
    linkedin_url: str | None = None
    photo: str | None = None
    hidden: bool | None = None


class ServiceSearchResult(CostMixin):
    elements: list[ServiceSearchHit] = []
    pagination: Pagination | None = None
