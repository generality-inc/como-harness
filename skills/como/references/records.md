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
