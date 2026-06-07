# como-harness

The public **como** client: a typed Python SDK + `como` CLI for LinkedIn data,
plus the `como-sales` agent skill. The same harness powers a person working at
their terminal, an agent prototyping locally, and an agent running in the cloud.

## Layout

```
core/      como-core  — shared Pydantic types (company / job / profile / leads / …)
sdk/       como-sdk   — the `como` CLI + SDK (depends on como-core)
SKILL.md              — the como-sales agent skill
```

## Install

```bash
git clone https://github.com/generality-inc/como-harness
cd como-harness/sdk
uv tool install -e .        # installs the global `como` command
como --help
```

Register the skill with your agent (proper skill directory, not an `@import`):

```bash
# Claude Code
mkdir -p ~/.claude/skills/como-sales && ln -sf "$PWD/../SKILL.md" ~/.claude/skills/como-sales/SKILL.md
# Codex
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills/como-sales" && ln -sf "$PWD/../SKILL.md" "${CODEX_HOME:-$HOME/.codex}/skills/como-sales/SKILL.md"
```

## Auth

```bash
como auth login
```
