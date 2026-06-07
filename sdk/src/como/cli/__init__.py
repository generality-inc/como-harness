from __future__ import annotations

from ._app import app


def main() -> None:
    app()


__all__ = ["app", "main"]
