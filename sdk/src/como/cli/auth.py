"""``como auth login`` / ``como auth logout`` / ``como auth whoami`` — WorkOS.

``login`` runs WorkOS AuthKit's Authorization-Code + PKCE flow (see ``_pkce`` +
``_workos_auth``): open the browser, capture the ``code`` on a ``127.0.0.1``
loopback, exchange it for a WorkOS access + refresh token, and store the session
in ``~/.config/como/credentials.json``. The transport then sends the access
token and refreshes it on 401 (see ``_config``/``_transport``). The WorkOS
client id for the target deployment is discovered from the public
``/v1/cli/auth-config`` endpoint.
"""

from __future__ import annotations

import contextlib

import httpx
import typer

from .._config import (
    DEFAULT_TIMEOUT,
    credentials_path,
    load_credentials,
    resolve_base_url,
    resolve_bearer,
    save_credentials,
)
from .._workos_auth import login_via_pkce

app = typer.Typer(no_args_is_help=True, help="Authenticate the CLI/SDK against a Como workspace.")


def _fetch_workos_client_id(api_base: str) -> str:
    """Discover the WorkOS client id for this deployment from the public API."""
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            resp = client.get(f"{api_base}/v1/cli/auth-config")
            resp.raise_for_status()
            cid = resp.json().get("workos_client_id")
    except httpx.HTTPError as exc:
        typer.secho(f"Couldn't reach {api_base} to start sign-in: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    if not cid:
        typer.secho("Server did not return a WorkOS client id.", fg="red", err=True)
        raise typer.Exit(code=1)
    return str(cid)


@app.command("login")
def login(
    base_url: str | None = typer.Option(None, "--base-url", help="Como API base URL."),
    client_id: str | None = typer.Option(
        None, "--client-id", help="WorkOS client id (default: discovered from the API)."
    ),
    no_browser: bool = typer.Option(False, "--no-browser", help="Don't auto-open the browser."),
) -> None:
    """Sign in via WorkOS (Authorization Code + PKCE) and store the session."""
    api_base = resolve_base_url(base_url)
    cid = client_id or _fetch_workos_client_id(api_base)
    typer.echo(f"Signing in to {api_base} via WorkOS …")
    try:
        tokens = login_via_pkce(client_id=cid, open_browser=not no_browser)
    except RuntimeError as exc:
        typer.secho(f"Login failed: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    path = save_credentials(
        {
            "auth": "workos",
            "workos_access_token": tokens.access_token,
            "workos_refresh_token": tokens.refresh_token,
            "workos_client_id": cid,
            "organization_id": tokens.organization_id,
            "user_id": tokens.user_id,
            "base_url": api_base,
        }
    )
    typer.secho("Signed in.", fg="green", bold=True)
    typer.echo(f"Credentials written to {path}")


@app.command("logout")
def logout() -> None:
    """Forget the saved session (and revoke a legacy API key if present)."""
    creds = load_credentials()
    path = credentials_path()
    if creds is None and not path.exists():
        typer.echo("Not logged in.")
        return
    # Legacy api-key sessions get a best-effort server-side revoke. WorkOS
    # sessions are short-lived tokens that simply expire — nothing to revoke.
    if creds and creds.get("api_key"):
        base_url = creds.get("base_url") or resolve_base_url(None)
        api_key = str(creds["api_key"])
        with contextlib.suppress(httpx.HTTPError):
            with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                keys = client.get(
                    f"{base_url}/v1/cli/keys", headers={"Authorization": f"Bearer {api_key}"}
                )
            if keys.status_code == 200:
                own_prefix = api_key[:14]
                for row in keys.json():
                    if row.get("prefix") == own_prefix:
                        with httpx.Client(timeout=DEFAULT_TIMEOUT) as deleter:
                            deleter.delete(
                                f"{base_url}/v1/cli/keys/{row['id']}",
                                headers={"Authorization": f"Bearer {api_key}"},
                            )
                        break
    with contextlib.suppress(FileNotFoundError):
        path.unlink()
    typer.secho("Logged out.", fg="green")


@app.command("whoami")
def whoami() -> None:
    """Show the workspace and user this CLI is authenticated as."""
    creds = load_credentials()
    if not creds:
        typer.secho("Not logged in. Run `como auth login`.", fg="yellow")
        raise typer.Exit(code=1)
    base_url = creds.get("base_url") or resolve_base_url(None)
    bearer = resolve_bearer(None)
    with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
        resp = client.get(f"{base_url}/v1/me", headers={"Authorization": f"Bearer {bearer}"})
    if resp.status_code == 200:
        body = resp.json()
        user = body.get("user", {})
        ws = body.get("workspace", {})
        typer.echo(f"{user.get('email')}  →  workspace {ws.get('slug')} ({ws.get('name')})")
    else:
        typer.secho(f"Server returned {resp.status_code}: {resp.text}", fg="red", err=True)
        raise typer.Exit(code=1)
