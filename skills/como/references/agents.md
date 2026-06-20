# Authoring, uploading & running cloud agents (`como agents`)

A **cloud agent** is a reusable research-agent definition you upload to your workspace and
**run over a list again and again**. Each run is a full **coding agent** in a cloud sandbox
(Claude Code + the `como` skill + `browser-harness`) — not a single LLM call — so it can browse
careers sites, call `como linkedin`, read full job descriptions, and emit structured fields with
evidence. This is how the platform turns "research every company in a list" into one repeatable,
billable job.

Use this for: scoring/qualifying every record in a list by something that needs real research
(e.g. "how many offshore back-office roles is this company hiring for", "what RCM platform do
they use", "are they SOC2 certified"). The classic example is outship's `technical-roles-signal`.

## The shape of an agent
Four things define an agent (see `como agents template` for a ready-to-edit skeleton):

| field | what it is |
|---|---|
| `name` | display name (slug auto-derived; pass `slug` to override) |
| `mission` | **the prompt** handed to the sandboxed coding agent. Write it like a research brief (see below) |
| `input_fields` | record fields injected into the prompt at run time, e.g. `["name","domain","linkedin"]` |
| `output_schema` | a **JSON Schema**; its top-level **scalar** properties (string/number/integer/boolean) are the values you can map onto a CRM column |
| `budget_usd` | hard $ ceiling per record run (default 2.0) — the per-run gateway key's max-budget |

Only **scalar** top-level properties are mappable onto columns. Nested objects/arrays (e.g. an
`evidence` object) are stored but not column values — use them for proof/rationale.

## Workflow
```bash
# 1. scaffold a definition, then edit the mission + output_schema:
como agents template > offshore-ops.json
$EDITOR offshore-ops.json

# 2. upload it to your workspace (needs the agents:create permission — admin & member both hold it):
como agents create --from-file offshore-ops.json     # -> the stored agent (id + slug)
como agents ls                                        # NAME  SLUG  OUTPUT FIELDS

# 3. bind it to a column + run it over a list. Binding (agent -> column + output field)
#    is done in the web app (Agents column). Once bound, run a batch as often as you like:
como agents run --attribute <column_id> --list <list_id>   # one sandboxed run per record
```
`run` returns a batch id; the runs execute on the agent worker (one per record, ~4 concurrent).
Re-run any time — that's the "again and again".

## Writing a good `mission` (this is 90% of agent quality)
Model it on outship's `technical-roles-signal`. A strong mission:
- **States the target precisely** — what counts, what doesn't, and "when in doubt, …". The agent
  judges from **full content (the JD body), never the title**.
- **Names the sources and tools**: the careers site via `browser-harness` (boards are often an
  Ashby/Greenhouse/Lever embed with a public API — use it), and LinkedIn via the **`como linkedin`**
  CLI (`job search` → titles only → `job get --job-id` → full `descriptionText`). De-dupe across sources.
- **Demands evidence**: for every counted item keep a source URL + one-line reason; write rich
  rationale to a Markdown file (`evidence/<field>.md`) and put the **path** (not the prose) in the
  JSON to avoid escaping mistakes — the platform reads the file back.
- **Never automates LinkedIn with a browser** — that's a ban risk. LinkedIn data goes through
  `como linkedin` only (see [cli.md](cli.md)). Careers sites / portals are fine via browser-harness.

## `output_schema` tips
- Keep the column values as a few **scalar** fields (`total_open_roles`, `matching_role_count`).
- Add a nested `evidence` object (items + sources + a `rationale` path) for proof — it won't be a
  column but it's stored on the run and shown on hover.
- It must be valid JSON Schema with **≥1 scalar top-level property**, or upload is rejected (422).

## Auth & gotchas
- `como agents create` needs **`agents:create`**, `rm` needs **`agents:delete`**, `link`/`unlink`
  need **`agents:update`**, and `run` needs **`agents:run`**. The **admin** and **member** roles both
  carry all four (guest holds none), so any non-guest member can author and run agents. A human
  `como_live_` key acts as your own member, so your real role applies.
- Runs cost money (the `budget_usd` ceiling per record × list size). Start on a small list.
- Binding an agent to a column is currently a web-app step; the CLI authors/uploads/runs.
