from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Final

DEFAULT_BASE_URL: Final[str] = "https://api.como.sh"
DEFAULT_TIMEOUT: Final[float] = 30.0

ENV_API_KEY: Final[str] = "COMO_API_KEY"
# The backend is injected via the environment (the cloud runner and internal dev
# set it); everyone else — i.e. every customer — gets production by default.
# There is deliberately no CLI flag for it. ``COMO_API_BASE_URL`` stays honored
# as a legacy alias so already-deployed sandboxes / scripts keep working.
ENV_BASE_URL: Final[str] = "COMO_BASE_URL"
ENV_BASE_URL_LEGACY: Final[str] = "COMO_API_BASE_URL"


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
    """Resolve the API base URL: explicit (the SDK ``base_url=`` kwarg) →
    ``COMO_BASE_URL`` → ``COMO_API_BASE_URL`` (legacy) → the production default.

    Injected via the environment, not a CLI flag — customers always get
    production; the cloud runner and internal dev set the env var to point
    elsewhere."""
    if explicit:
        return explicit.rstrip("/")
    for var in (ENV_BASE_URL, ENV_BASE_URL_LEGACY):
        env_value = os.environ.get(var)
        if env_value:
            return env_value.rstrip("/")
    return DEFAULT_BASE_URL.rstrip("/")
