from __future__ import annotations

import json
import sys
from typing import Any

from pydantic import BaseModel
from rich.console import Console
from rich.json import JSON


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
