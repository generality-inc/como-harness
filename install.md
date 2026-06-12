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
como auth login --base-url https://api.como.sh
```
This opens the user's browser to **app.como.sh**; they pick a workspace and click Approve. A
scoped `como_live_` key is written to `~/.config/como/credentials.json` (0600) and the prod base
URL is persisted. Every later `como` call picks the key up automatically.

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
The CLI and the skill are both the editable clone, so updating is one pull:

```bash
cd <your como-harness clone> && git pull
```

The next `como` run uses the new code, and the symlinked skill picks up the new instructions.
Re-run `uv tool install -e ./sdk` only if a pull changed dependencies. There's no self-update
banner — pull when told to, or when a command errors with a schema/version mismatch.

## Troubleshooting
- **`como: command not found`** → `uv tool update-shell`, restart the shell.
- **`Missing API key`** → run `como auth login` (step 3), or export `COMO_API_KEY`.
- **Sent to the wrong environment** (e.g. app-dev) → the saved `base_url` points at dev. Re-run
  `como auth login --base-url https://api.como.sh`; the explicit base overwrites it. The login
  page always follows whichever API base the CLI calls.
