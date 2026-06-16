---
name: como-sales
description: The `como` platform for sales research & list-building — ghost LinkedIn data (companies, jobs, people/leads, posts), reading/creating/editing platform lists, running LLM-in-code through the como gateway, and orchestrating research agents (local or cloud). Use for company/people/job research, building & enriching lead lists, ICP discovery, and any `como linkedin` / `como lists` / `como run` task.
metadata:
  short-description: como — sales research, list-building, and agent orchestration
---

# como

`como` is the platform CLI + SDK for sales research and list-building. This file is a
thin index — **read the reference doc for whatever you're doing before non-trivial work.**

## What you can do → where to read

| If you need to… | Read |
|---|---|
| Pull LinkedIn research data (companies, jobs, people/leads, posts, geo) | **[references/cli.md](references/cli.md)** — the full `como linkedin` + SDK reference |
| **Read / build a list** (target accounts, lead lists) on the platform | **[references/lists.md](references/lists.md)** — `como lists ls / records / create / add` |
| **Author / upload / run a cloud agent** (qualify every record in a list, again & again) | **[references/agents.md](references/agents.md)** — `como agents template / create / ls / run` |
| Run an LLM **inside code** (classify / score / extract / filter a batch) | **[references/cli.md](references/cli.md)** → "Using an LLM in your code (`como run`)" |
| **Drive a browser** (a source with no API — bookface/YC, a company site) | **[references/cloud-browser.md](references/cloud-browser.md)** — browser comes from **como, cloud by default** (never local unless asked); **profile-first** for logged-in sites (use/create one + have the user log in *before* starting); `browser-harness` is the driver underneath |
| Orchestrate a **multi-step / multi-agent** job (build a list from a source, research every row, posts→people→ICP) | **[references/workflows.md](references/workflows.md)** — run shapes + the canonical playbooks |

## Two rules that prevent most mistakes (full detail in `references/cli.md`)
1. A `search` returns **shallow** hits — call the matching `get` for the full record.
2. Resolve an entity to an **id** first, then query by `--company-id` / `--geo-id` rather than fuzzy `--search`.

## One orchestration rule (full detail in `references/workflows.md`)
Anything that **drives a browser or does real research is a coding agent** (Claude Code +
this skill + the `browser-harness` skill) — **not** a single LLM call. Use bare `como run`
LLM calls only for cheap in-code steps (classify/extract/filter), never to operate the
browser. Browser work defaults to a **cloud** browser; tell the user you're using cloud.

Auth: `como auth login` stores a `como_live_` key (`COMO_API_KEY`). Add `--pretty` for readable JSON.

## Install / keep the CLI current
- First-time install + sign-in + skill registration: see **`install.md` at the como-harness repo root**.
- The `como` CLI is an **editable clone** of `como-harness` and **auto-updates** — once a day it
  notifies and fast-forward pulls itself (the symlinked skill updates with it). So you normally
  don't need to do anything.
- To update **now** (e.g. a command hit a schema/version mismatch like a Pydantic validation
  error from a field the API changed), run **`como update`** yourself — don't ask the user. If
  that reports it isn't a clone install, find the clone (`uv tool list`, or search for a
  `como-harness` checkout under the user's dev dir), `git pull`, and `uv tool install -e ./sdk`
  if a dependency changed.
