# Writing the CRM (`como crm records`)

`como crm records` is full CRUD over CRM **records** — a record is one row of an
object (a Company, a Person, a Deal). Authenticated by your `como_live_` key
(acts as **you**, with your workspace role). This is how an agent **fills and
maintains the CRM** — the same data the web app shows.

Default output is single-line JSON (pipe to `jq`); add `--pretty` for readable.

## The one rule: prefer `upsert` over `create`

`upsert` is idempotent — match an existing record by an **identity attribute**
(`--match slug=value`) and merge, or create if none matches. Re-running is safe
and only changed fields move. **Use it for anything you might run twice**
(enrichment, re-imports, scheduled fills). `create` always inserts a new row.

```bash
como crm records upsert --object companies --match domain=acme.com \
  --name "Acme" --data '{"yc_batch":"S26","stage":"warm"}'      # → record + created + changed_fields
como crm records create --object companies --name "Acme" --data '{"domain":"acme.com"}'
```

`--object` takes a **slug or id** (`companies`, `people`, `deals`, or a custom
object — see `como crm objects ls`). `--data` is a JSON object of attribute values
keyed by **attribute slug** (`como crm attributes ls --object companies` to see
them). `--list <name|slug|id>` also adds the new record to a list.

## Read

```bash
como crm records get <id>
como crm records list   --object companies --limit 50 --offset 0    # newest first (limit ≤ 500)
como crm records list   --object companies --view <view_id>         # in a saved view's filter+sort order
como crm records search "acme" --object companies                   # ILIKE on name (q ≥ 2 chars)
como crm records duplicates --object companies --data '{"domain":"acme.com"}'   # dedup BEFORE inserting
como crm records lists  <id>                                        # which lists this record is in
como crm records related <id>                                       # every relationship edge touching it
```

## Update — merges `data`, never replaces

`update` sends only the fields you pass, and **merges** `--data` into the
record's existing bag (a partial update never wipes other keys — including
enrichment fields). To change one cell, pass just that key.

```bash
como crm records update <id> --name "Acme Inc" --status active
como crm records update <id> --data '{"stage":"hot"}'      # merges; other data preserved
como crm records update <id> --owner <member_id>           # set the owner
como crm records update <id> --unset-owner                 # clear the owner
```

## Recording a finding with evidence

When you research a value for a record and want to **back it with proof** (so the
cell shows your reasoning + sources on hover), attach an **evidence** payload to
the write. This is the deliverable shape for a research agent: a value **plus**
the proof behind it.

**You decide which command to use based on where your target attribute lives** —
there are two scopes, and the same finding lands in a different place depending
on which you pick:

- **COMPANY / object attribute** — the value belongs to the **record itself** (a
  column on the Company / Person / Deal object). Write it with `records update`:

  ```bash
  como crm records update <record_id> --data '{"<slug>": <value>}' --evidence-file evidence.json
  # or inline:  --evidence '{"<slug>": { … }}'
  ```

- **LIST attribute** — the value belongs to the record's **entry in a specific
  list** (a list-scoped column, see [lists.md](lists.md)). Write it with `lists
  entry-data`:

  ```bash
  como crm lists entry-data <list_id> <record_id> --data '{"<slug>": <value>}' --evidence-file evidence.json
  # or inline:  --evidence '{"<slug>": { … }}'
  ```

If your mission says the target is a company/object attribute, use the first
form; if it's a list attribute, use the second. The `<slug>` is the target
attribute's slug (your mission gives it to you; otherwise `como crm attributes ls
--object <obj>` or `como crm lists attrs ls <list>`). `<value>` is the value you
researched. The value + its evidence land on the **record** (object form) or on
that record's **list entry** (list form) — nowhere else.

### The evidence shape (`EvidenceEntry`, keyed by slug)

`--evidence` / `--evidence-file` carries a JSON object **keyed by attribute slug**
— one `EvidenceEntry` per slug you're writing:

```jsonc
{
  "<slug>": {
    "rationale":  "<markdown>",   // REQUIRED — Markdown explaining the value.
                                  //   This is the key field; write it even for a
                                  //   "found nothing" zero rather than fabricate.
    "items": [                    // the granular units behind the value (may be empty)
      { "label":  "<short label>",        // e.g. a role title, a person, a competitor
        "urls":   ["https://…", "…"],     // source link(s) for THIS item (may be empty)
        "detail": "<one-line reason/snippet>" }
    ],
    "sources": [                  // optional — distinct pages/queries you consulted
      { "url": "https://…", "title": "<page title>" }
    ],
    "confidence": 0.0             // optional, 0..1
  }
}
```

`rationale` is the only required field; everything else is optional (`items` may
be empty — an honest "nothing found"). Each `item` renders as a uniform row
(label + detail + its source links). The same slug must appear in **both** the
`--data` value and the evidence object — they describe the same cell.

**Recommended: write the evidence to a file and pass `--evidence-file`** rather
than inlining it. The JSON has nested quotes and Markdown, so inlining via
`--evidence '<json>'` is easy to break with shell escaping. Example:

```bash
cat > evidence.json <<'JSON'
{
  "hiring_signal": {
    "rationale": "**Strong** — 3 open offshore back-office roles found across the careers page and the Greenhouse board.",
    "items": [
      { "label": "AR/AP Specialist (Manila)", "urls": ["https://acme.com/careers/ar-ap", "https://boards.greenhouse.io/acme/jobs/123"], "detail": "Full-time, posted 2w ago — offshore finance ops." },
      { "label": "Medical Coder (Remote, PH)", "urls": ["https://acme.com/careers/coder"], "detail": "RCM / back-office, contractor." }
    ],
    "sources": [
      { "url": "https://acme.com/careers", "title": "Acme — Careers" },
      { "url": "https://boards.greenhouse.io/acme", "title": "Acme on Greenhouse" }
    ],
    "confidence": 0.8
  }
}
JSON

# object attribute on the record:
como crm records update <record_id> --data '{"hiring_signal":"strong"}' --evidence-file evidence.json
# OR — list attribute on the record's entry in a list:
como crm lists entry-data <list_id> <record_id> --data '{"hiring_signal":"strong"}' --evidence-file evidence.json
```

The write **merges per slug**: only the slugs you pass are overwritten, so
re-running over the same record replaces just that cell's value + evidence and
leaves the rest intact.

## Relationships (reference attributes)

Reference/relationship attributes (e.g. a Company's `people`) are **not** set via
`--data` — use `link` / `unlink`:

```bash
como crm records link  <id> --attribute people --to <rec_id>,<rec_id>   # replace the reference set
como crm records unlink <id> --attribute people                          # clear it
```

## Delete / restore / merge

```bash
como crm records rm <id>                 # soft-delete (one id → DELETE)
como crm records rm id1,id2,id3          # bulk soft-delete
como crm records restore <id>
como crm records merge <survivor_id> --victim <victim_id>   # fold victim into survivor (data deep-merged)
```

## Notes
- Writes need the `crm:write` scope (your `como login` key has it; the cloud
  sandbox's `ghost:read` key does not — it emits and the API writes).
- `data` keys must be real attribute slugs on the object; reference-type slugs
  are rejected in `data` (use `link`). See [crm-schema.md](crm-schema.md) to add
  columns/objects, and [lists.md](lists.md) to group records into lists.
- A common pipeline: research with `como linkedin`, `upsert` the winners here,
  add them to a list. See [workflows.md](workflows.md).
