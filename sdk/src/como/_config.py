from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Final

DEFAULT_BASE_URL: Final[str] = "https://api.como.sh"
DEFAULT_TIMEOUT: Final[float] = 30.0

ENV_API_KEY: Final[str] = "COMO_API_KEY"
ENV_BASE_URL: Final[str] = "COMO_API_BASE_URL"


def credentials_path() -> Path:
    """``$XDG_CONFIG_HOME/como/credentials.json`` (or ``~/.config/como/...``)."""
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "como" / "credentials.json"


def load_credentials() -> dict[str, Any] | None:
    """Return the credentials dict written by ``como auth login``, or None."""
    path = credentials_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def resolve_api_key(explicit: str | None) -> str:
    """Resolve the API key in priority order: explicit → env → credentials file."""
    if explicit:
        return explicit
    env_value = os.environ.get(ENV_API_KEY)
    if env_value:
        return env_value
    creds = load_credentials()
    if creds and creds.get("api_key"):
        return str(creds["api_key"])
    raise RuntimeError(
        f"Missing API key. Run `como auth login`, set {ENV_API_KEY} in the environment, "
        "or pass api_key=... to the client."
    )


def resolve_base_url(explicit: str | None) -> str:
    """Resolve base URL in priority order: explicit → env → credentials file → default."""
    if explicit:
        return explicit.rstrip("/")
    env_value = os.environ.get(ENV_BASE_URL)
    if env_value:
        return env_value.rstrip("/")
    creds = load_credentials()
    if creds and creds.get("base_url"):
        return str(creds["base_url"]).rstrip("/")
    return DEFAULT_BASE_URL.rstrip("/")
