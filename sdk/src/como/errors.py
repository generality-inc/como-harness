from __future__ import annotations

from typing import Any


class ComoError(Exception):
    """Base class for all como SDK errors."""


class ComoNetworkError(ComoError):
    """Raised when the request fails at the transport layer (DNS, timeout, connection reset)."""


class ComoAPIError(ComoError):
    """Raised when the API returns a non-success response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        body: Any = None,
        response: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body
        self.response = response


class ComoBadRequestError(ComoAPIError):
    """HTTP 400 — invalid parameters or malformed request."""


class ComoAuthError(ComoAPIError):
    """HTTP 401 / 403 — missing, invalid, or unauthorized credentials."""


class ComoNotFoundError(ComoAPIError):
    """HTTP 404 — resource not found."""


class ComoRateLimitError(ComoAPIError):
    """HTTP 429 — rate-limited."""


class ComoServerError(ComoAPIError):
    """HTTP 5xx — upstream server error."""


_STATUS_MAP: dict[int, type[ComoAPIError]] = {
    400: ComoBadRequestError,
    401: ComoAuthError,
    403: ComoAuthError,
    404: ComoNotFoundError,
    429: ComoRateLimitError,
}


def error_for_status(status: int, body: Any, response: Any) -> ComoAPIError:
    message = ""
    if isinstance(body, dict):
        message = body.get("message") or body.get("error") or ""
    if not message:
        message = f"HTTP {status}"
    cls = _STATUS_MAP.get(status)
    if cls is None:
        cls = ComoServerError if status >= 500 else ComoAPIError
    return cls(message, status_code=status, body=body, response=response)
