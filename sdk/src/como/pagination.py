from __future__ import annotations

import inspect
from collections.abc import AsyncIterator, Callable, Coroutine, Iterator
from typing import Any, Protocol


class _Paginated(Protocol):
    pagination: Any
    elements: Any


def _build_kwargs(call: Callable, *, page: int, token: Any, base: dict) -> dict:
    try:
        params = inspect.signature(call).parameters
    except (TypeError, ValueError):
        params = {}
    kwargs = dict(base)
    if not params or "page" in params:
        kwargs["page"] = page
    if token is not None and (not params or "pagination_token" in params):
        kwargs["pagination_token"] = token
    return kwargs


def iter_pages(
    call: Callable[..., _Paginated],
    *,
    max_pages: int | None = None,
    **kwargs: Any,
) -> Iterator[_Paginated]:
    """Iterate a paginated endpoint until exhausted or `max_pages` reached.

    `call` must be a bound method that accepts a `page` kwarg (and optionally
    `pagination_token`) and returns a model exposing `.pagination` and `.elements`.
    """
    page = kwargs.pop("page", None) or 1
    token = kwargs.pop("pagination_token", None)
    fetched = 0
    while True:
        result = call(**_build_kwargs(call, page=page, token=token, base=kwargs))
        yield result
        fetched += 1
        if max_pages is not None and fetched >= max_pages:
            return
        pg = getattr(result, "pagination", None)
        total = getattr(pg, "total_pages", None) if pg is not None else None
        if not total or page >= total:
            return
        page += 1
        token = getattr(pg, "pagination_token", None) if pg is not None else None


async def aiter_pages(
    call: Callable[..., Coroutine[Any, Any, _Paginated]],
    *,
    max_pages: int | None = None,
    **kwargs: Any,
) -> AsyncIterator[_Paginated]:
    page = kwargs.pop("page", None) or 1
    token = kwargs.pop("pagination_token", None)
    fetched = 0
    while True:
        result = await call(**_build_kwargs(call, page=page, token=token, base=kwargs))
        yield result
        fetched += 1
        if max_pages is not None and fetched >= max_pages:
            return
        pg = getattr(result, "pagination", None)
        total = getattr(pg, "total_pages", None) if pg is not None else None
        if not total or page >= total:
            return
        page += 1
        token = getattr(pg, "pagination_token", None) if pg is not None else None
