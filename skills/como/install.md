---
name: como-install
description: Install the `como` CLI (+ the browser-harness CLI it uses) and sign in, with minimal prompting.
---

# `como` CLI installation

Install the `como` CLI and sign in. `como` is the typed CLI **and** Python SDK for the
platform — ghost LinkedIn research data, reading/building lists, running an LLM through the
como gateway, and provisioning cloud browsers. For day-to-day usage read `SKILL.md`; this
file is only for install, sign-in, and updates.

## Prerequisites
- **uv** (Python toolchain): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **git**

## 1. Install the `como` CLI
The CLI lives in this repo's `sdk/` and depends on the sibling `core/`, so install it from a
clone as an editable tool (same shape as browser-harness). Editable means a later `git pull`
updates the CLI with **no reinstall**.

```bash
git clone https://github.com/generality-inc/como-harness
cd como-harness
uv tool install -e ./sdk
command -v como            # should print the como path
```

Prefer a stable location like `~/Developer/como-harness`, not `/tmp`. If `como: command not
found`, run `uv tool update-shell` and restart your shell.

## 2. Sign in
```bash
como auth login --base-url https://api.como.sh
```
This opens your browser to **app.como.sh**, where you pick a workspace and click Approve. A
scoped `como_live_` key is written to `~/.config/como/credentials.json` (0600); every later
`como` call picks it up automatically, and the prod base URL is persisted so you stay on prod.

Verify:
```bash
como linkedin company get --search "Stripe"     # should print JSON
```

## 3. Install browser-harness (for browser automation)
Some research drives a real browser — a careers site, a portal behind a login. `como` uses the
**browser-harness** CLI for that. Install the CLI the same way:

```bash
git clone https://github.com/browser-use/browser-harness
cd browser-harness
uv tool install -e .
command -v browser-harness
```

> Install the **CLI only** — do **not** register browser-harness as an agent skill yet. (Skill
> registration is a separate, later step.)

## Keeping `como` current
The CLI is an editable clone, so updating is just a pull:

```bash
cd <your como-harness clone> && git pull
```

The next `como` run uses the new code immediately. Only if a pull changes dependencies (rare)
re-run `uv tool install -e ./sdk`. There's no self-update banner — pull when you're told to, or
when a command errors with a schema/version mismatch.

## Troubleshooting
- **`como: command not found`** → uv's tool bin isn't on PATH. `uv tool update-shell`, restart the shell.
- **`Missing API key`** → run `como auth login` (step 2), or export `COMO_API_KEY`.
- **Sent to the wrong environment** (e.g. app-dev) → your saved `base_url` points at dev. Re-run
  `como auth login --base-url https://api.como.sh`; the explicit base overwrites it. The login
  page always follows whichever API base the CLI calls.
