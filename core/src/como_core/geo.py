from __future__ import annotations

from ._common import BaseModel, CostMixin


class GeoMatch(BaseModel):
    geo_id: str | None = None
    title: str | None = None


class GeoSearchResult(CostMixin):
    id: str | None = None
    elements: list[GeoMatch] = []
