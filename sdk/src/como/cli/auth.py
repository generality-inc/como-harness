"""``como auth login`` / ``como auth logout`` / ``como auth whoami``.

Auth flow mirrors OAuth 2.0 Device Authorization Grant:

  1. POST /v1/cli/device-code → server returns ``device_code`` (kept secret)
     and ``user_code`` (printed to the user).
  2. CLI opens the browser to ``<web>/cli/<user_code>``; the user, already
     signed in, picks a workspace and clicks **Approve**.
  3. CLI polls /v1/cli/poll with the device_code; once approved the
     response carries the full API key — returned exactly once. Written to
     ``~/.config/como/credentials.json`` with ``0600`` perms.

After ``como auth login`` succeeds, every other SDK / CLI call picks the key up
automatically (see ``_config.resolve_api_key``).
"""

from __future__ import annotations

import contextlib
import json
import platform
import socket
import time
import webbrowser
from pathlib import Path
from typing import Any

import httpx
import typer

from .._config import DEFAULT_TIMEOUT, credentials_path, load_credentials, resolve_base_url

app = typer.Typer(no_args_is_help=True, help="Authenticate the CLI/SDK against a Como workspace.")


def _device_label() -> str:
    """Default human-readable device name: ``<user>@<hostname>`` (best effort)."""
    try:
        import getpass

        user = getpass.getuser()
    except Exception:
        user = "user"
    return f"{user}@{socket.gethostname()} ({platform.system()})"


def _save_credentials(payload: dict[str, Any]) -> Path:
    path = credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    path.chmod(0o600)
    return path


@app.command("login")
def login(
    base_url: str | None = typer.Option(
        None, "--base-url", help="Como API base URL. Defaults to COMO_API_BASE_URL or the production URL."
    ),
    label: str | None = typer.Option(None, "--label", help="Display name for this device."),
    no_browser: bool = typer.Option(False, "--no-browser", help="Don't auto-open the browser."),
) -> None:
    """Pair this machine with a Como workspace via the device-code flow."""
    api_base = resolve_base_url(base_url)
    device_label = label or _device_label()

    typer.echo(f"Starting login at {api_base} …")
    with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
        start_resp = client.post(f"{api_base}/v1/cli/device-code", json={"device_label": device_label})
        start_resp.raise_for_status()
        start = start_resp.json()

    user_code = start["user_code"]
    device_code = start["device_code"]
    verify_url = start["verification_url_complete"]
    expires_in = int(start.get("expires_in", 600))
    interval = max(int(start.get("interval", 5)), 2)

    typer.echo("")
    typer.echo(f"  Your one-time code:  {typer.style(user_code, bold=True, fg='cyan')}")
    typer.echo(f"  Visit:               {verify_url}")
    typer.echo("")
    if not no_browser:
        typer.echo("Opening browser …")
        with contextlib.suppress(Exception):
            webbrowser.open(verify_url)
    typer.echo("Waiting for approval (Ctrl-C to cancel) …")

    deadline = time.time() + expires_in
    while time.time() < deadline:
        time.sleep(interval)
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            poll_resp = client.post(f"{api_base}/v1/cli/poll", json={"device_code": device_code})
            poll_resp.raise_for_status()
            poll = poll_resp.json()
        status = poll.get("status")
        if status == "pending":
            continue
        if status == "approved":
            key = poll.get("key")
            if not key:
                typer.secho("Server approved the device but didn't return a key.", fg="red", err=True)
                raise typer.Exit(code=1)
            path = _save_credentials(
                {
                    "api_key": key,
                    "workspace_id": poll.get("workspace_id"),
                    "user_id": poll.get("user_id"),
                    "base_url": api_base,
                    "device_label": device_label,
                }
            )
            typer.secho("Logged in.", fg="green", bold=True)
            typer.echo(f"Credentials written to {path}")
            return
        if status == "denied":
            typer.secho("Login denied.", fg="red", err=True)
            raise typer.Exit(code=1)
        if status == "expired":
            typer.secho("Login expired before approval.", fg="red", err=True)
            raise typer.Exit(code=1)
        # Unknown status — keep polling.

    typer.secho("Login timed out waiting for approval.", fg="red", err=True)
    raise typer.Exit(code=1)


@app.command("logout")
def logout() -> None:
    """Forget the saved API key and revoke it server-side."""
    creds = load_credentials()
    path = credentials_path()
    if creds is None and not path.exists():
        typer.echo("Not logged in.")
        return

    if creds is not None:
        base_url = creds.get("base_url") or resolve_base_url(None)
        api_key = creds.get("api_key")
        if api_key:
            try:
                with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                    keys = client.get(
                        f"{base_url}/v1/cli/keys",
                        headers={"Authorization": f"Bearer {api_key}"},
                    )
                if keys.status_code == 200:
                    # Find our own key by comparing prefix.
                    own_prefix = api_key[:14]
                    for row in keys.json():
                        if row.get("prefix") == own_prefix:
                            client_del = httpx.Client(timeout=DEFAULT_TIMEOUT)
                            try:
                                client_del.delete(
                                    f"{base_url}/v1/cli/keys/{row['id']}",
                                    headers={"Authorization": f"Bearer {api_key}"},
                                )
                            finally:
                                client_del.close()
                            break
            except httpx.HTTPError:
                # Server unreachable — still wipe local creds.
                pass

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
    api_key = creds["api_key"]
    with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
        resp = client.get(
            f"{base_url}/v1/me",
            headers={"Authorization": f"Bearer {api_key}"},
        )
    if resp.status_code == 200:
        body = resp.json()
        user = body.get("user", {})
        ws = body.get("workspace", {})
        typer.echo(f"{user.get('email')}  →  workspace {ws.get('slug')} ({ws.get('name')})")
    else:
        typer.secho(f"Server returned {resp.status_code}: {resp.text}", fg="red", err=True)
        raise typer.Exit(code=1)
