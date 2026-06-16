"""``como browser`` — provision a cloud browser through como (the broker), and
manage persistent **browser profiles**.

Two noun groups:

  Sessions (ephemeral browsers):
    como browser create [--profile NAME]   # -> {id, cdp_url, live_url}
    como browser stop <id>

  Profiles (persistent, logged-in identities):
    como browser profile ls
    como browser profile create <name> [--shared] [--description ...]
    como browser profile login <name>      # human signs in once via the live view
    como browser profile rm <id>

``create`` returns a Browser Use cloud browser made with the **platform's** key —
no Browser Use key is needed on this machine. Attach a CDP driver to ``cdp_url``
(e.g. the ``browser-harness`` skill via ``BU_CDP_URL``); ``live_url`` is a watch
link; tear it down with ``stop``. The Browser Use key never leaves the platform —
same broker pattern as the LLM gateway.

A **profile** is a persistent identity (cookies/localStorage). Log in once
(``como browser profile login <name>``), then start authenticated browsers with
``como browser create --profile <name>``. The agent never sees the underlying
provider profile id — it references a profile by name or id.

LinkedIn isn't blocked, but **avoid automating a LinkedIn-logged-in profile** — it's
a high ban risk for that account (anonymous LinkedIn automation is fine). For LinkedIn
data, prefer ``como linkedin`` (the ghost API) — no account, no ban risk.
"""

from __future__ import annotations

import json

import httpx
import typer

from .._config import DEFAULT_TIMEOUT, resolve_api_key, resolve_base_url

app = typer.Typer(
    no_args_is_help=True,
    help="Cloud browsers + persistent browser profiles (via the como broker).",
)
profile_app = typer.Typer(
    no_args_is_help=True,
    help="Persistent, logged-in browser profiles agents reuse.",
)
app.add_typer(profile_app, name="profile")


def _client() -> tuple[str, dict[str, str]]:
    base, key = resolve_base_url(None), resolve_api_key(None)
    return base, {"Authorization": f"Bearer {key}"}


# --------------------------------------------------------------------------- #
# Sessions
# --------------------------------------------------------------------------- #
@app.command("create")
def create(
    profile: str | None = typer.Option(
        None, "--profile", "-p", help="Start the browser on a saved profile (name or id) — already logged in."
    ),
) -> None:
    """Create a cloud browser. Prints {id, cdp_url, live_url} as JSON.

    Attach a CDP driver to `cdp_url` (e.g. `BU_CDP_URL=<cdp_url>` for the
    browser-harness skill); stop it with `como browser stop <id>` when done.
    With `--profile`, the browser starts authenticated to whatever that profile
    holds cookies for.
    """
    base, headers = _client()
    body = {"profile": profile} if profile else {}
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as c:
            resp = c.post(f"{base}/v1/browser", headers=headers, json=body)
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
    base, headers = _client()
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as c:
            resp = c.delete(f"{base}/v1/browser/{browser_id}", headers=headers)
    except httpx.HTTPError as exc:
        typer.secho(f"Stop failed: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    if resp.status_code not in (200, 204):
        typer.secho(f"Stop failed ({resp.status_code}): {resp.text}", fg="red", err=True)
        raise typer.Exit(code=1)
    typer.secho("Stopped.", fg="green")


# --------------------------------------------------------------------------- #
# Profiles
# --------------------------------------------------------------------------- #
def _fmt_row(cols: list[str], widths: list[int]) -> str:
    return "  ".join(c.ljust(w) for c, w in zip(cols, widths, strict=False))


@profile_app.command("ls")
def profile_ls(
    json_out: bool = typer.Option(False, "--json", help="Print raw JSON instead of a table."),
) -> None:
    """List browser profiles you can use (shared + your own private)."""
    base, headers = _client()
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as c:
            resp = c.get(f"{base}/v1/browser/profiles", headers=headers)
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        typer.secho(f"Couldn't list profiles: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    rows = resp.json()
    if json_out:
        typer.echo(json.dumps(rows, indent=2))
        return
    if not rows:
        typer.secho("No browser profiles yet. Create one with `como browser profile create`.", fg="yellow")
        return
    headers_row = ["NAME", "STATUS", "VISIBILITY", "HAS COOKIES FOR", "ID"]
    table = [
        [
            p["name"],
            p["status"],
            p["visibility"],
            ", ".join(p.get("cookie_domains") or []) or "—",
            str(p["id"]),
        ]
        for p in rows
    ]
    widths = [max(len(r[i]) for r in [headers_row, *table]) for i in range(len(headers_row))]
    typer.echo(_fmt_row(headers_row, widths))
    for r in table:
        typer.echo(_fmt_row(r, widths))
        if next((p for p in rows if str(p["id"]) == r[-1] and p.get("has_linkedin")), None):
            typer.secho(
                "    ⚠ has LinkedIn cookies — avoid logged-in LinkedIn automation (ban risk).", fg="yellow"
            )


@profile_app.command("create")
def profile_create(
    name: str = typer.Argument(..., help="A label, e.g. 'Bookface'."),
    description: str | None = typer.Option(None, "--description", "-d"),
    shared: bool = typer.Option(False, "--shared", help="Let any workspace member use it (default: private)."),
) -> None:
    """Create a browser profile (empty until you log in). Prints it as JSON."""
    base, headers = _client()
    body = {"name": name, "description": description, "visibility": "shared" if shared else "private"}
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as c:
            resp = c.post(f"{base}/v1/browser/profile", headers=headers, json=body)
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        typer.secho(f"Couldn't create profile: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    p = resp.json()
    typer.echo(json.dumps(p, indent=2))
    typer.secho(f"\nNow log in once:  como browser profile login {p['name']!r}", fg="green")


@profile_app.command("rm")
def profile_rm(
    profile_id: str = typer.Argument(..., help="The profile id from `como browser profile ls`."),
) -> None:
    """Delete a browser profile (creator or workspace admin)."""
    base, headers = _client()
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as c:
            resp = c.delete(f"{base}/v1/browser/profile/{profile_id}", headers=headers)
    except httpx.HTTPError as exc:
        typer.secho(f"Delete failed: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    if resp.status_code not in (200, 204):
        typer.secho(f"Delete failed ({resp.status_code}): {resp.text}", fg="red", err=True)
        raise typer.Exit(code=1)
    typer.secho("Deleted.", fg="green")


def _resolve_profile_id(base: str, headers: dict[str, str], profile: str) -> str:
    """Resolve a profile name-or-id to its id."""
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as c:
            lst = c.get(f"{base}/v1/browser/profiles", headers=headers)
            lst.raise_for_status()
    except httpx.HTTPError as exc:
        typer.secho(f"Couldn't list profiles: {exc}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    match = next((p for p in lst.json() if str(p["id"]) == profile or p["name"] == profile), None)
    if match is None:
        typer.secho(f"No profile named or id'd {profile!r}. See `como browser profile ls`.", fg="red", err=True)
        raise typer.Exit(code=1)
    return str(match["id"])


def _post_profile(base: str, headers: dict[str, str], path: str, *, body: dict | None = None, what: str) -> dict:
    """POST to a profile endpoint, surfacing the backend's error detail on failure."""
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as c:
            resp = c.post(f"{base}{path}", headers=headers, json=body or {})
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        detail = exc.response.text if isinstance(exc, httpx.HTTPStatusError) else str(exc)
        typer.secho(f"{what}: {detail}", fg="red", err=True)
        raise typer.Exit(code=1) from exc
    return resp.json()


def _linkedin_warn(p: dict) -> None:
    if p.get("has_linkedin"):
        typer.secho(
            "⚠ This profile has LinkedIn cookies — avoid using it for LinkedIn automation "
            "(high ban risk if it's logged in).",
            fg="yellow",
        )


def _has_local_gui() -> bool:
    """True when this machine plausibly has a browser we can open (false on a
    headless agent/server). Mirrors browser-harness's check."""
    import os
    import platform

    system = platform.system()
    if system in ("Darwin", "Windows"):
        return True
    if system == "Linux":
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return False


def _auto_open_live(url: str | None) -> None:
    """Open the live view in the local browser when a GUI is present, so a
    co-located human can watch / sign in; a no-op on a headless agent. Mirrors
    browser-harness `start_remote_daemon`. Notes go to stderr (stdout stays clean
    for `--open`'s JSON)."""
    import webbrowser

    if not url or not _has_local_gui():
        return
    try:
        webbrowser.open(url, new=2)
        typer.secho("(opened the live view in your browser)", fg="green", err=True)
    except Exception as exc:
        typer.secho(f"(couldn't auto-open the live view: {exc} — open the URL above)", fg="yellow", err=True)


@profile_app.command("login")
def profile_login(
    profile: str = typer.Argument(..., help="Profile name or id to log into."),
    login_url: str | None = typer.Option(
        None, "--login-url", help="Optional starting page, e.g. https://bookface.ycombinator.com"
    ),
    open_only: bool = typer.Option(
        False,
        "--open",
        help="Open the login browser, print {browser_id, live_url, expires_at} as JSON, and exit "
        "(for agents — relay the live_url to a human, then call --finish).",
    ),
    finish: bool = typer.Option(
        False, "--finish", help="Finalize a login a human has already completed (persist + mark ready), then exit."
    ),
) -> None:
    """Log a human into the profile's browser once; agents reuse it afterwards.

    Default (interactive): open a live view, press Enter when signed in, save. For
    an **agent**, split it — ``--open`` returns the live view URL and exits so you
    can hand it to a human ("please log in and tell me when done"), then ``--finish``
    saves once they confirm. The live browser auto-stops at ``expires_at`` (and
    ``como browser profile cancel`` tears it down early), so an abandoned login
    never runs forever.

    You *can* log into LinkedIn, but avoid then automating that profile — high ban
    risk for the account (anonymous LinkedIn automation is fine).
    """
    if open_only and finish:
        typer.secho("Use either --open or --finish, not both.", fg="red", err=True)
        raise typer.Exit(code=1)
    base, headers = _client()
    pid = _resolve_profile_id(base, headers, profile)

    # --finish: a human already signed in via a prior --open; persist it.
    if finish:
        p = _post_profile(base, headers, f"/v1/browser/profile/{pid}/login/complete", what="Couldn't finalize login")
        typer.secho(f"Saved. Profile {p['name']!r} is now: {p['status']}.", fg="green")
        _linkedin_warn(p)
        return

    # Open (or reconnect to) the live login browser.
    session = _post_profile(
        base,
        headers,
        f"/v1/browser/profile/{pid}/login",
        body={"login_url": login_url} if login_url else {},
        what="Couldn't open login browser",
    )

    # --open: hand the session to the caller (agent) and exit — no blocking wait.
    # Auto-open the live view locally if a human's here; drive it to the login page
    # via browser-harness with BU_CDP_URL=<cdp_url> (the browser starts blank).
    if open_only:
        _auto_open_live(session.get("live_url"))
        keys = ("browser_id", "cdp_url", "live_url", "login_url", "expires_at")
        typer.echo(json.dumps({k: session.get(k) for k in keys}))
        return

    # Interactive: show the live view (auto-open it), block until done, then finish.
    typer.secho("\nOpen this live view, go to the site you want, and sign in:", fg="green", bold=True)
    typer.echo(f"  Live view: {session['live_url']}")
    if session.get("login_url"):
        typer.echo(f"  Starting page (navigate here yourself): {session['login_url']}")
    if session.get("expires_at"):
        typer.echo(f"  Expires: {session['expires_at']}")
    _auto_open_live(session.get("live_url"))
    typer.echo("\nWhen you've finished logging in, press Enter to save the session…")
    input()
    p = _post_profile(base, headers, f"/v1/browser/profile/{pid}/login/complete", what="Couldn't finalize login")
    typer.secho(f"\nSaved. Profile {p['name']!r} is now: {p['status']}.", fg="green")
    _linkedin_warn(p)


@profile_app.command("cancel")
def profile_cancel(
    profile: str = typer.Argument(..., help="Profile name or id whose in-progress login to cancel."),
) -> None:
    """Abort an in-progress login — tear down the live browser without saving."""
    base, headers = _client()
    pid = _resolve_profile_id(base, headers, profile)
    _post_profile(base, headers, f"/v1/browser/profile/{pid}/login/cancel", what="Couldn't cancel login")
    typer.secho("Cancelled — login browser torn down (nothing saved).", fg="green")
