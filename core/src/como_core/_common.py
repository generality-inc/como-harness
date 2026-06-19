from __future__ import annotations

from typing import Any

from pydantic import BaseModel as _PydanticBase
from pydantic import ConfigDict
from pydantic.alias_generators import to_camel


class BaseModel(_PydanticBase):
    """Project-wide base. snake_case fields ↔ camelCase wire format, extras allowed."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )


class Pagination(BaseModel):
    total_pages: int | None = None
    total_elements: int | None = None
    page_number: int | None = None
    previous_elements: int | None = None
    page_size: int | None = None
    pagination_token: str | None = None


class Cost(BaseModel):
    """What the caller is charged for one request — OUR price, margin included.

    This is the marked-up amount billed to the customer's wallet, never the
    upstream/vendor cost: the API computes it from the per-org price book and
    stamps it onto the response after the upstream envelope is stripped. ``amount``
    is a fixed-point USD string (6 dp, e.g. ``"0.060000"``) so it round-trips the
    ledger's ``Decimal`` exactly without float drift.
    """

    amount: str
    currency: str = "USD"


class CostMixin(BaseModel):
    """Mixin for top-level ghost responses that carry a request ``cost``.

    Optional by design: ``cost`` is absent when the request wasn't metered (no
    upstream cost, or the billing layer couldn't resolve the org). It is the only
    pricing field a customer ever sees — see ``GhostService._shape``, which strips
    every upstream pricing/identity field before this is added.
    """

    cost: Cost | None = None


class DatePart(BaseModel):
    month: Any | None = None
    year: int | None = None
    day: Any | None = None
    text: str | None = None
    timestamp: int | None = None
    date: str | None = None


class MediaImage(BaseModel):
    url: str | None = None
    width: int | None = None
    height: int | None = None
    expires_at: int | None = None


class ParsedLocation(BaseModel):
    text: str | None = None
    country_code: str | None = None
    region_code: str | None = None
    country: str | None = None
    country_full: str | None = None
    state: str | None = None
    city: str | None = None


class LocationField(BaseModel):
    linkedin_text: str | None = None
    country_code: str | None = None
    postal_address: str | None = None
    parsed: ParsedLocation | None = None
