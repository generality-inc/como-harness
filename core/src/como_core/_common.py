from __future__ import annotations

from typing import Any

from pydantic import BaseModel as _PydanticBase
from pydantic import ConfigDict
from pydantic.alias_generators import to_camel


class BaseModel(_PydanticBase):
    """Base for the LinkedIn data models — snake_case fields ↔ camelCase wire format.

    ``extra="ignore"`` drops any undeclared key at every depth during validation, so a
    response only ever contains the fields declared here. (The CRM models use a
    separate base, ``crm.CrmBaseModel``; they are not affected by this and keep
    failing loudly on unexpected shapes.)"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )


class Pagination(BaseModel):
    total_pages: int | None = None
    total_elements: int | None = None
    page_number: int | None = None
    previous_elements: int | None = None
    page_size: int | None = None
    pagination_token: str | None = None


class Cost(BaseModel):
    """The price for one request, in USD.

    ``amount`` is a fixed-point string (6 dp, e.g. ``"0.060000"``) so it round-trips
    exactly without floating-point error.
    """

    amount: str
    currency: str = "USD"


class CostMixin(BaseModel):
    """Mixin for responses that carry a request ``cost`` (the price for the call).

    Optional: ``cost`` is absent when a request wasn't priced.
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
