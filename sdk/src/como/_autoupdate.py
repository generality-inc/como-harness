"""Best-effort auto-update for the editable-clone install.

`como` is installed as `uv tool install -e ./sdk` from a git clone, so the
running code *is* that clone's working tree. On a throttled cadence we fetch the
clone's remote and, if it's behind, **notify on stderr and fast-forward pull** —
the new code applies on the next `como` run.

Hard rules:
- **Fail-silent.** A flaky network, a non-git install, a dirty tree, a detached
  HEAD — none of these may ever break a command. Every failure is a no-op.
- **stderr only.** stdout carries JSON; nothing here may touch it.
- **Off for the cloud runner.** Set ``COMO_NO_UPDATE=1`` for deterministic,
  pinned environments (the runner does this).
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

_CHECK_INTERVAL_SECONDS = 24 * 3600
_FETCH_TIMEOUT = 5
_PULL_TIMEOUT = 30
_STAMP = Path.home() / ".config" / "como" / "update_check"

_CYAN = "\033[36m"
_YELLOW = "\033[33m"
_RESET = "\033[0m"


def _err(msg: str) -> None:
    color = sys.stderr.isatty()
    if color:
        sys.stderr.write(msg + "\n")
    else:
        # strip ANSI for non-tty (logs)
        for code in (_CYAN, _YELLOW, _RESET):
            msg = msg.replace(code, "")
        sys.stderr.write(msg + "\n")
    sys.stderr.flush()


def _clone_root() -> Path | None:
    """The git clone root, or None if this isn't an editable-clone install.

    This file lives at ``<clone>/sdk/src/como/_autoupdate.py``."""
    for parent in Path(__file__).resolve().parents:
        if (parent / ".git").exists():
            return parent
    return None


def _git(root: Path, *args: str, timeout: int) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _commits_behind(root: Path) -> int | None:
    """Number of commits the local HEAD is behind its upstream, or None if it
    can't be determined (no upstream, detached HEAD, error)."""
    res = _git(root, "rev-list", "--count", "HEAD..@{u}", timeout=_FETCH_TIMEOUT)
    if res is None or res.returncode != 0:
        return None
    try:
        return int(res.stdout.strip() or "0")
    except ValueError:
        return None


def _throttled() -> bool:
    try:
        return (time.time() - _STAMP.stat().st_mtime) < _CHECK_INTERVAL_SECONDS
    except OSError:
        return False


def _mark_checked() -> None:
    try:
        _STAMP.parent.mkdir(parents=True, exist_ok=True)
        _STAMP.touch()
    except OSError:
        pass


def maybe_autoupdate() -> None:
    """Throttled startup hook: fetch, and if behind, notify + fast-forward pull."""
    if os.environ.get("COMO_NO_UPDATE") or _throttled():
        return
    root = _clone_root()
    if root is None:
        return
    _mark_checked()  # mark first so a hang doesn't re-fetch every call
    if _git(root, "fetch", "--quiet", timeout=_FETCH_TIMEOUT) is None:
        return
    behind = _commits_behind(root)
    if not behind or behind <= 0:
        return
    _err(f"{_CYAN}⬆ como: {behind} update(s) available — pulling the latest…{_RESET}")
    pulled = _git(root, "pull", "--ff-only", "--quiet", timeout=_PULL_TIMEOUT)
    if pulled is not None and pulled.returncode == 0:
        _err(f"{_CYAN}✓ como updated — applies on your next run "
             f"(run `uv tool install -e ./sdk` only if a dependency changed).{_RESET}")
    else:
        _err(f"{_YELLOW}! como couldn't fast-forward (local changes?) — run `como update`.{_RESET}")


def force_update() -> int:
    """Explicit `como update`: fetch + fast-forward pull, verbose. Returns exit code."""
    root = _clone_root()
    if root is None:
        _err(f"{_YELLOW}como isn't an editable-clone install — nothing to update.{_RESET}")
        return 1
    _mark_checked()
    if _git(root, "fetch", "--quiet", timeout=_FETCH_TIMEOUT) is None:
        _err(f"{_YELLOW}could not reach the remote — check your network.{_RESET}")
        return 1
    behind = _commits_behind(root)
    if behind is None:
        _err(f"{_YELLOW}couldn't determine update status (no upstream / detached HEAD).{_RESET}")
        return 1
    if behind == 0:
        _err(f"{_CYAN}✓ como is already up to date.{_RESET}")
        return 0
    pulled = _git(root, "pull", "--ff-only", timeout=_PULL_TIMEOUT)
    if pulled is not None and pulled.returncode == 0:
        _err(f"{_CYAN}✓ pulled {behind} update(s) — applies on your next run "
             f"(run `uv tool install -e ./sdk` if a dependency changed).{_RESET}")
        return 0
    _err(f"{_YELLOW}! couldn't fast-forward (local changes or a diverged branch). "
         f"Resolve in the clone at {root}, then retry.{_RESET}")
    return 1
