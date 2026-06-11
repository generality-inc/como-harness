# Orchestrating research & list-building

Read this for any multi-step or multi-row job (build a list from a source, research every
row of a list, posts→people→ICP). It's the altitude above the individual commands.

## The one principle: a unit of work is a coding agent

Anything that **drives a browser or does real research is a coding agent** — a Claude Code
instance with this skill + the `browser-harness` skill — that *iterates* (look → act →
verify). It is **not** a single LLM call. Reserve bare `como run` LLM calls for cheap
in-code steps *inside* an agent: classify a row, extract JSON from page text, score a fit.

So: the agent operates the browser and decides; `como run` is a tool the agent's code calls
for narrow reasoning. Never collapse a browse-and-decide loop into one LLM prompt.

## The three run shapes (same agent, different placement)

| Shape | What it is | Use when |
|---|---|---|
| **Local single** | one Claude Code agent on the user's machine | small jobs; interactive; you're already local |
| **Cloud single** | one agent in a Daytona sandbox with a cloud browser (the platform's **research agent runner**) | one heavier job you want off the user's machine / unattended |
| **Cloud parallel** | local Claude Code is the **orchestrator**: it fans out N cloud agents (Daytona sandboxes, each with its own Browser Use browser), then **aggregates** their results and pushes to a platform list | many independent rows (per company / per batch / per person) — the common case at scale |

Every agent — local or cloud — has the same toolbox: `como linkedin` (ghost data),
`como run` (gateway LLM-in-code), the `browser-harness` skill (cloud browser by default,
see [cloud-browser.md](cloud-browser.md)), and `como lists` for platform lists.

Browser is **cloud by default** in every shape; tell the user. The cloud agents already use
a cloud browser, so local↔cloud behavior matches.

## Playbook 1 — build a list from a source
e.g. *"go to bookface, take every company from the last 10 batches, make a list."*
1. **Scrape** the source with a browser agent (browser-harness, cloud; carry the user's
   login via profile-sync if the source is auth-walled — see cloud-browser.md).
2. **Structure** the scraped pages into rows (`como run` to extract `{name, url, batch, …}` as JSON).
3. **Write** the rows to a platform list (`como lists` — create the list, add entries).
4. **Scale it:** split the source (e.g. one batch per agent) across **cloud-parallel** agents;
   the local orchestrator aggregates their JSON and does one list write. Dedupe on write.

## Playbook 2 — research every row of a list
e.g. *"read this list and research each company/role."*
1. **Read** the list locally (`como lists` → entries/records). Decide whether you even need
   to pull it locally or can hand row-ranges straight to cloud agents.
2. **Fan out**: one research agent per row (or per chunk). Each does the *classic research* —
   `como linkedin` (company → people → posts), the company's own site via browser-harness,
   `como run` to summarize/score.
3. **Aggregate & write back** to the list (enrich each row) — local orchestrator collects, or
   each agent writes its own row.

## Playbook 3 — posts → people → ICP
e.g. *"look at this person's LinkedIn posts, the people in them, and find the ICPs for <target>."*
1. `como linkedin profile posts --profile <id>` → the person's posts.
2. For each post, gather the **engaged people** (commenters/reactors → profiles) via `como linkedin`.
3. **ICP-classify** each profile against the target profile with `como run` (a cheap in-code
   LLM step: "does this person match <ICP criteria>? score + reason"). Pull the full record
   first — never classify off a shallow search hit.
4. **Write the matches** to a list for review.

## Notes on what exists vs. what's coming
- `como linkedin`, `como run`, `browser-harness` are live today.
- **`como lists`** (read/create/edit platform lists) is the list-editing capability being
  added — if `como lists --help` errors, it isn't in your installed CLI yet; tell the user.
- The **cloud research agent** is the platform's existing runner (Daytona + Browser Use +
  Claude Code in a sandbox). Spawning a batch of them ad-hoc from local is the orchestration
  surface we're building toward; until it's a one-command call, describe the plan to the user.
