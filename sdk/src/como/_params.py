from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def clean_params(params: Mapping[str, Any]) -> dict[str, str]:
    """Drop None values, stringify bools, and CSV-join list/tuple values."""
    out: dict[str, str] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, bool):
            out[key] = "true" if value else "false"
        elif isinstance(value, (list, tuple)):
            if not value:
                continue
            out[key] = ",".join(str(v) for v in value)
        else:
            out[key] = str(value)
    return out


def require_one_of(**kwargs: Any) -> None:
    """Raise ValueError if all keyword arguments are None."""
    if not any(v is not None for v in kwargs.values()):
        names = ", ".join(kwargs)
        raise ValueError(f"At least one of ({names}) is required.")
