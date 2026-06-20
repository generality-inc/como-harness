# Shaping the CRM schema (`como crm objects`, `como crm attributes`)

The **catalog** is the workspace's data model: object *types* and their
*attributes* (columns). Most work only needs the existing catalog — read it to
discover slugs, then write records/lists. Reach for these commands when you need
a **new** object type, column, or dropdown option. Writes need `crm:write`.

> Schema changes restructure the workspace (deleting an object/attribute loses
> its data). Prefer reusing existing objects/attributes; create new ones
> deliberately.

## Objects (the types: Companies, People, Deals, …)
```bash
como crm objects ls                                 # slugs + names + ids
como crm objects create --slug investors --singular Investor --plural Investors [--icon … --color …]
como crm objects update investors --plural "Investors & Funds"
como crm objects rm investors
```

## Attributes (the columns on an object)
```bash
como crm attributes ls --object companies           # every column + its options
como crm attributes create --object companies --slug tier --name Tier --type select
como crm attributes update <attr_id> --name "ICP Tier"
como crm attributes rm <attr_id>                     # archive
como crm attributes reorder --object companies <attr_id1>,<attr_id2>,…
```
Types: `text number currency rating date datetime select multi_select status
checkbox domain email personal_name phone location user_reference
record_reference`. `select` / `multi_select` / `status` carry **options**;
`record_reference` / `relationship` are set via `como crm records link`, never in
`record.data`.

## Options (choices on select / status / multi_select)
```bash
como crm attributes option add    <attr_id> --slug lead --label Lead [--color blue]
como crm attributes option update <attr_id> <option_id> --label "Lead investor"
como crm attributes option rm     <attr_id> <option_id>
```

## Relationships (a typed link between two objects, both directions)
```bash
como crm attributes relationship \
  --left-object companies  --left-slug investors  --left-name Investors  --left-cardinality many \
  --right-object investors --right-slug portfolio  --right-name Portfolio --right-cardinality many
```
Creates the paired attribute on each object; populate it per-record with
`como crm records link <id> --attribute investors --to <ids>`.

## Notes
- There's no by-slug lookup endpoint — `--object` accepts a slug and the CLI
  resolves it by listing. Attribute commands take attribute **ids** (get them
  from `attributes ls`).
- For **list-scoped** columns (values per list membership, not on the record),
  use `como crm lists attrs …` instead — see [lists.md](lists.md).
