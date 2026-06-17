---
name: como-install
description: Install the `como` CLI, register the como-sales skill in this agent, install the browser-harness CLI, and sign in — with minimal prompting.
---

# Installing `como`

Follow these steps to set up `como` for the user. `como` is the typed CLI **and** Python SDK
for the platform — ghost LinkedIn research data, reading/building lists, running an LLM through
the como gateway, and provisioning cloud browsers. Do each step yourself; only ask the user for
the one interactive step (signing in).

## Prerequisites
- **uv** (Python toolchain): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **git**

## 1. Install the `como` CLI
The CLI lives in `sdk/` and depends on the sibling `core/`, so install from the clone as an
editable tool (a later `git pull` then updates it with no reinstall).

```bash
git clone https://github.com/generality-inc/como-harness
cd como-harness
uv tool install -e ./sdk
command -v como            # should print the como path
```

Prefer a stable location like `~/Developer/como-harness`, not `/tmp`. If `como: command not
found`, run `uv tool update-shell` and restart the shell.

## 2. Register the `como-sales` skill in this agent
So future sessions know how to use `como`, symlink this repo's skill package into the agent's
skills directory (the whole `skills/como` directory, so its `references/` come along). Run from
the repo root:

```bash
# Claude Code
mkdir -p ~/.claude/skills && ln -sfn "$PWD/skills/como" ~/.claude/skills/como-sales

# Codex (if used)
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills" && ln -sfn "$PWD/skills/como" "${CODEX_HOME:-$HOME/.codex}/skills/como-sales"
```

The symlink keeps the skill in sync with the repo — a `git pull` updates the instructions too.

## 3. Sign in
```bash
como auth login
```
This opens the user's browser to **app.como.sh**; they pick a workspace and click Approve. A
scoped `como_live_` key is written to `~/.config/como/credentials.json` (0600). Every later
`como` call picks the key up automatically and talks to production.

Verify:
```bash
como linkedin company get --search "Stripe"     # should print JSON
```

## 4. Install the browser-harness CLI (for browser automation)
Some research drives a real browser — a careers site, a portal behind a login. `como` uses the
**browser-harness** CLI for that. Install the CLI the same way:

```bash
git clone https://github.com/browser-use/browser-harness
cd browser-harness
uv tool install -e .
command -v browser-harness
```

> Install the **CLI only** — do **not** register browser-harness as an agent skill yet. (That's
> a separate, later step.)

## Keeping `como` current
The CLI **auto-updates**: on a throttled cadence (once a day) `como` checks its clone's remote
and, if it's behind, prints a one-line notice and **fast-forward pulls** for you — the new code
applies on your next run, and the symlinked skill picks up the new instructions. Force it any
time with:

```bash
como update
```

It's fail-silent (a flaky network or local changes never break a command) and writes only to
stderr. Re-run `uv tool install -e ./sdk` only if an update changed dependencies. **Disable the
auto-check** (e.g. for deterministic CI / cloud-runner environments) with `COMO_NO_UPDATE=1`.

> **Already installed before auto-update existed?** Bootstrap once with a manual pull, or paste
> this to your coding agent:
>
> > Update my `como` CLI: find the `como-harness` git clone (`uv tool list`, or search my home
> > dir for a `como-harness` checkout), `cd` into it, run `git pull`, then `uv tool install -e
> > ./sdk`. Confirm with `como --version`.

## Troubleshooting
- **`como: command not found`** → `uv tool update-shell`, restart the shell.
- **`Missing API key`** → run `como auth login` (step 3), or export `COMO_API_KEY`.
- **Sent to the wrong environment** (e.g. app-dev) → `COMO_BASE_URL` is set in your shell. The
  CLI talks to production by default; `unset COMO_BASE_URL` to restore it. The login page always
  follows whichever API base the CLI calls.
