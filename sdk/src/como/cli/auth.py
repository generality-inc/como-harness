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
from ..client import Como
from ..errors import ComoAPIError, ComoError

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
    label: str | None = typer.Option(None, "--label", help="Display name for this device."),
    no_browser: bool = typer.Option(False, "--no-browser", help="Don't auto-open the browser."),
) -> None:
    """Pair this machine with a Como workspace via the device-code flow."""
    # The backend is production by default; internal use sets COMO_BASE_URL.
    api_base = resolve_base_url(None)
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
        api_key = creds.get("api_key")
        if api_key:
            # Revoke the stored key server-side by matching its prefix. Any
            # failure (server unreachable, non-200) is swallowed — we still wipe
            # local creds below.
            own_prefix = api_key[:14]
            try:
                with Como(api_key=api_key) as client:
                    for row in client.account.list_keys():
                        if row.prefix == own_prefix:
                            client.account.delete_key(str(row.id))
                            break
            except ComoError:
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
    try:
        with Como(api_key=creds["api_key"]) as client:
            me = client.account.me()
    except ComoAPIError as exc:
        typer.secho(
            f"Server returned {exc.status_code}: {exc.body if exc.body is not None else exc}", fg="red", err=True
        )
        raise typer.Exit(code=1) from exc
    except ComoError as exc:
        typer.secho(f"Couldn't reach the server: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"{me.user.get('email')}  →  workspace {me.workspace.get('slug')} ({me.workspace.get('name')})")
