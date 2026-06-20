from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import typer
from pydantic import BaseModel
from rich.console import Console
from rich.json import JSON

from ..errors import ComoAPIError, ComoError


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", by_alias=True, exclude_none=True)
    if isinstance(value, list):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    return value


def emit(value: Any, *, pretty: bool = False) -> None:
    payload = _to_jsonable(value)
    if pretty:
        Console().print(JSON.from_data(payload))
    else:
        json.dump(payload, sys.stdout, ensure_ascii=False, default=str)
        sys.stdout.write("\n")


@contextmanager
def api_errors() -> Iterator[None]:
    """Turn SDK exceptions into a clean red message + exit(1), instead of a
    traceback. Wrap the client calls a CLI command makes."""
    try:
        yield
    except ComoAPIError as exc:
        detail = exc.body if exc.body is not None else str(exc)
        typer.secho(f"Request failed ({exc.status_code}): {detail}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    except ComoError as exc:
        typer.secho(f"Request failed: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
