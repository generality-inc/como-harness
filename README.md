# como-harness ♞

The public **como** client: a typed Python SDK + `como` CLI for sales research and
list-building — ghost LinkedIn data, platform lists, the LLM gateway, and cloud browsers —
plus the `como-sales` agent skill. The same harness powers a person at their terminal, an
agent prototyping locally, and an agent running in the cloud.

## Setup prompt

Paste into Claude Code (or Codex):

```text
Set up https://github.com/generality-inc/como-harness for me.

Read `install.md` and follow the steps to install the `como` CLI, register the como-sales skill, and sign me in.
```

The agent will install the CLI, symlink the skill into your agent, install the browser-harness
CLI, and walk you through `como auth login` (one browser approval). Manual steps are in
[install.md](install.md).

## Updating

To update, paste into Claude Code (or Codex):

```text
Update my `como` CLI to the latest. Find the como-harness git clone — try `uv tool list`,
otherwise search my home directory for a `como-harness` checkout. cd into it, run `git pull`,
then `uv tool install -e ./sdk`. Confirm it worked with `como --version`.
```

**You only need that once.** After updating, `como` keeps itself current automatically — it
checks daily and fast-forward pulls the latest (run `como update` to force it, or set
`COMO_NO_UPDATE=1` to disable, e.g. for pinned/CI environments).

## Layout

```
core/         como-core — shared Pydantic types (company / job / profile / leads / …)
sdk/          como-sdk  — the `como` CLI + SDK (depends on como-core)
skills/como/  SKILL.md + references/ — the como-sales agent skill
install.md    first-time install + sign-in + skill registration
```
