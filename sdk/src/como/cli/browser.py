"""``como browser`` — provision a cloud browser through como (the broker).

``como browser create`` returns a Browser Use cloud browser created with the
**platform's** key — so no Browser Use key is needed on this machine. It prints a
``cdp_url`` to attach a driver to (e.g. the ``browser-harness`` skill via
``BU_CDP_URL``) plus a ``live_url`` to watch, and an ``id`` to tear it down with
``como browser stop <id>``. The Browser Use key never leaves the platform — same
broker pattern as the LLM gateway.
"""

from __future__ import annotations

import json

import httpx
import typer

from .._config import DEFAULT_TIMEOUT, resolve_api_key, resolve_base_url

app = typer.Typer(
    no_args_is_help=True,
    help="Provision a cloud browser through como (for the browser-harness skill).",
)


@app.command("create")
def create() -> None:
    """Create a cloud browser. Prints {id, cdp_url, live_url} as JSON.

    Attach a CDP driver to `cdp_url` (e.g. `BU_CDP_URL=<cdp_url>` for the
    browser-harness skill); stop it with `como browser stop <id>` when done.
    """
    base, key = resolve_base_url(None), resolve_api_key(None)
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as c:
            resp = c.post(f"{base}/v1/browser", headers={"Authorization": f"Bearer {key}"})
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        typer.secho(f"Couldn't create a cloud browser: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(resp.json()))


@app.command("stop")
def stop(
    browser_id: str = typer.Argument(..., help="The browser session id from `create`."),
) -> None:
    """Stop (tear down) a cloud browser by id."""
    base, key = resolve_base_url(None), resolve_api_key(None)
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as c:
            resp = c.delete(f"{base}/v1/browser/{browser_id}", headers={"Authorization": f"Bearer {key}"})
    except httpx.HTTPError as exc:
        typer.secho(f"Stop failed: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    if resp.status_code not in (200, 204):
        typer.secho(f"Stop failed ({resp.status_code}): {resp.text}", fg="red", err=True)
        raise typer.Exit(code=1)
    typer.secho("Stopped.", fg="green")
