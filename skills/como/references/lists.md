# Reading & building lists (`como crm lists`)

A **list** is a curated container of records (companies / people) — a target
account list, a lead list, an ICP segment. `como crm lists` reads a list, builds it,
manages its entries, and defines its per-list columns. Authenticated by your
`como_live_` key (acts as **you**). A brand-new list has **no view** until you
add one — same as the dashboard's "Start with a view" step. Decide table vs
kanban and which columns matter, then create it (`como crm lists view create`); a
list without a view renders empty in the app.

Resolve a list by **name** (case-insensitive), **slug**, or **id** — every
command accepts any. `como crm lists ls` to find one.

## List lifecycle
```bash
como crm lists ls                                  # NAME  SLUG  ID
como crm lists get "US - Seed"                      # one list's metadata (JSON)
como crm lists create "My targets" --object companies [--emoji 🎯]   # --object takes a slug or id
como crm lists update "My targets" --name "Hot targets" --emoji 🔥
como crm lists duplicate "My targets"               # clone shell + columns + views (no entries)
como crm lists set-parent "My targets" --object people
como crm lists rm "My targets"                      # soft-delete (entries/views/columns go with it)
como crm lists reorder <id1>,<id2>,<id3>            # sidebar order
```

## Entries (records in the list)
```bash
como crm lists records "My targets"                 # rows: name + status + data + list_data
como crm lists records "My targets" --json          # full JSON incl. list_data
como crm lists add    "My targets" <rec_id>          # add one (or: add <list> id1,id2,id3)
como crm lists remove "My targets" <rec_id>          # remove one (or comma-separated) — inverse of add
como crm lists reorder-entries "My targets" <id1>,<id2>,<id3>
```
- `records` returns each row as `{id, name, status, data, list_data}` — `data`
  is the record's own attributes; **`list_data`** is the list-scoped column
  values (below). `entries` is the lower-level `{record_id + data}` view.

## List-scoped columns (`list_data`)
A list can have its own columns that only exist within it (e.g. "Stage",
"Review score") — their values live per-membership in `list_data`, not on the
record.
```bash
como crm lists attrs ls "My targets"
como crm lists attrs create "My targets" --slug stage --name Stage --type select
como crm lists entry-data "My targets" <rec_id> --data '{"stage":"warm"}'   # set values (merges)
```
(For select/status columns, add the choices with `como crm attributes option add` —
see [crm-schema.md](crm-schema.md).)

## Views (how a list renders)
```bash
como crm lists view ls "My targets"
como crm lists view create "My targets" --name "Hot" --type table|kanban
como crm lists view columns <view_id> domain,name,stage     # ordered, by slug or id
como crm lists view sorts   <view_id> stage:desc,name:asc
como crm lists view filter  <view_id> --json '<tree>'       # or --clear
como crm lists view update  <view_id> --name "Hot" --default   # rename / set-default / --type convert
como crm lists view operators                               # what each attribute type supports
```

## Building a list (typical flow)
1. `como crm lists create "<name>" --object companies` (or find one with `ls`).
2. **Give it a view** so it isn't empty in the app: `como crm lists view create "<name>"
   --name "Table" --type table`, then shape it (`view columns/sorts/filter`).
   Pick kanban instead when the list is a pipeline. (The dashboard prompts a human
   for this same choice; an agent makes it explicitly.)
3. Get record ids — research with `como linkedin …` then `como crm records upsert …`
   (see [records.md](records.md)), or pull from an existing list.
4. `como crm lists add "<name>" id1,id2,id3`.
5. Optional: add list-scoped columns (`attrs create`) + set values (`entry-data`).

## Notes
- Writes need `crm:write` (your `como login` key has it). One entry per record
  per list; lists hold one object type.
- This is platform data, distinct from `como linkedin` (ghost research).
