from __future__ import annotations

from ._common import BaseModel


class GeoMatch(BaseModel):
    geo_id: str | None = None
    title: str | None = None


class GeoSearchResult(BaseModel):
    id: str | None = None
    elements: list[GeoMatch] = []
