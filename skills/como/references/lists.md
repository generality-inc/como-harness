# Reading & building lists (`como lists`)

A **list** is a curated container of records (companies / people) — a target account list,
a lead list, an ICP segment. `como lists` reads a list's contents and adds records to it,
authenticated by your `como_live_` key (which acts as **you** — your own workspace member,
with your real permissions). This is the same data the web app's Lists show.

## Commands
```bash
como lists ls                          # every list in your workspace: NAME  SLUG  ID
como lists get "US - Seed/A/B > 20M"   # one list's metadata (JSON)
como lists records "US - Seed/A/B > 20M"   # the rows: each record's name + status + data
como lists records <id> --json         # full record data (name + record.data + list_data)
como lists create "My targets" --object <object_id> [--emoji 🎯]
como lists add <list> <record_id>      # add a record (or: add <list> id1,id2,id3)
```

Resolve a list by **name** (case-insensitive), **slug**, or **id** — every command accepts any.
`ls` first to find the id when you need it.

## How it reads
- `records` returns each row as `{id, name, status, data, list_data}` — `data` is the record's
  own attributes (the company/person fields); `list_data` is the **list-scoped** attribute values
  (columns that exist only on this list). Use it to see who's in a list and their enrichment.
- `entries` is the lower-level view (`record_id` + `list_data` only, no record identity) — prefer
  `records` for anything human-readable.

## Building a list (typical flow)
1. Find or create the list: `como lists ls` (or `como lists create "<name>" --object <companies_object_id>`).
2. Get record ids to add — from research (`como linkedin company get …` → resolve to platform
   records) or an existing list.
3. `como lists add <list> <record_id>` (single) or `como lists add <list> id1,id2,id3` (bulk).

## Notes
- A human API key acts with **your** workspace role. If you get a 403 on create/add, your role
  lacks `lists:create` / `list_entries:add` — read access still works.
- `create` needs the **parent object id** (which object the list holds — e.g. Companies). Get it
  from the platform; lists are always scoped to one object.
- This is platform data, distinct from `como linkedin` (ghost research). A common pipeline:
  research with `como linkedin`, then materialize the winners into a list here. See
  [workflows.md](workflows.md).
