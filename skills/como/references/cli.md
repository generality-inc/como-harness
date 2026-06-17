# como linkedin — LinkedIn research data (CLI & SDK)

`como` is a typed CLI **and** Python SDK for LinkedIn research data via the Como API.
It covers profiles, companies, jobs, posts, leads, groups, ads, services, and geo IDs —
every resource as both a shell command (under **`como linkedin …`**) and an importable
client (`import como`).

This data comes from Como's **ghost** LinkedIn research API — read-only LinkedIn data;
it needs no LinkedIn account of your own.

This is the canonical reference. Read the **Core concepts** and the **Recipes** before
non-trivial work — most mistakes come from skipping them (using keyword search when you
have an ID, or reading a shallow search hit and thinking it's the full record).

---

## Setup

```bash
export COMO_API_KEY=como_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx     # required
export COMO_BASE_URL=https://api.como.sh                      # optional; override for non-prod
como --help                                                       # top-level help
como linkedin --help                                              # all LinkedIn resources
como linkedin <resource> --help                                   # resource help
como linkedin <resource> <command> --help                         # full option list for a command
```

`como linkedin <resource> <command> --help` is authoritative for the exact flags — this doc lists
the useful ones but `--help` never lies.

## Output

Default output is single-line JSON (pipe to `jq`). Add `--pretty` for human-readable,
syntax-highlighted JSON.

```bash
como linkedin company get --universal-name openai --pretty
como linkedin job search --company-id 1441 | jq '.elements[].title'
```

---

## Core concepts (read this)

**1. `get` returns the FULL object; `search` returns SHALLOW hits.**
A `*-search` command returns a paginated list of *lightweight* hits — typically just
`id`, `url`, `title`/`name`, and `location`. **Search results do NOT contain descriptions,
full profile sections, employee counts, etc.** To get the full record (e.g. a job's
`descriptionText`, a profile's experience, a company's `employeeCount`) you must call the
matching `get` with the id/url from the hit. Never classify or summarize from a search hit
alone — fetch the full object.

**2. Resolve to an ID first, then query by ID.** Almost every search accepts a
`--company-id`, `--profile-id`, or `--geo-id`. **Always prefer IDs over keyword `--search`** —
keyword search is fuzzy and returns *other companies' results*. The resolve-first pattern:

```bash
# company name/URL/id  ->  full record; the numeric id is top-level `.id`
como linkedin company get --url https://www.linkedin.com/company/openai | jq -r '.id'   # e.g. 11130470
# then scope by that id (clean, no cross-company noise):
como linkedin job search --company-id 11130470
```

Same for people (`profile get … | jq -r .id` → `--profile-id`) and locations (geo, below).

**3. Geo IDs for reliable location filtering.** Plain `--location "New York"` works but can
mis-resolve (`NY`→New Zealand, `UK`→Ukraine). For precision, resolve a geo id and pass it:

```bash
como linkedin geo search --search "New York" | jq -r '.elements[0].geoId'   # closest-match geo id
# then: --geo-id <id> on company/profile/job/leads/service search
```

**4. Pagination.** List commands take `--page` (1-based). Some also return and require a
`--pagination-token` for pages ≥ 2 (LinkedIn returns page 1 again if you omit it). Walk:
read page 1, grab `.pagination.paginationToken`, pass it with `--page 2`, repeat. Watch
`.pagination.totalPages`.

**5. Freshness.** Job/post listings can be **expired** even while a role is open elsewhere —
`job get` then returns an empty `element`. Treat an empty get as "stale on LinkedIn," not
"doesn't exist."

---

## Resources

### company

```bash
como linkedin company get --universal-name openai            # one of: --url | --universal-name
como linkedin company get --url https://www.linkedin.com/company/openai
como linkedin company get --universal-name 105628248         # a numeric company id also works (in --universal-name or --url)
como linkedin company search --search "fintech" --location "Australia" \
                    --company-size "11-50,51-200,201-500" --geo-id <id> --industry-id <id> --page 1
como linkedin company posts --company <url|id|universalName> --posted-limit month --page 1
```
`get` returns the full company: **`id`, `universalName`, `name`, `website`, `description`,
`employeeCount`, `employeeCountRange`, `followerCount`, `foundedOn`, `headquarter`, industry**.
`search` hits are shallow (`id`, `name`, `universalName`, `url`). `--company-size` takes
comma-joined ranges (`1-10,11-50,51-200,201-500,501-1000,1001-5000,5001-10000,10001+`).

### job

```bash
como linkedin job get --job-id 4153069088                    # one of: --job-id | --url. FULL record (descriptionText)
como linkedin job search --company-id 1441                   # PREFER company-id over --search
como linkedin job search --search "staff engineer" --location "US" \
                --workplace-type "hybrid,remote" --employment-type "full-time" \
                --posted-limit month --sort-by date --salary "100k+" \
                --experience-level <id> --geo-id <id> --page 1
```
- **`job search` is shallow** — `id`, `url`, `title`, `company`, `location`, `postedDate`.
  No description. **To read a JD you must call `job get --job-id <id>`** (returns
  `descriptionText`, `descriptionHtml`, `employmentType`, `workplaceType`, `salary`,
  `applicantTrackingSystem`, `applicantsCount`, `expireAt`).
- Enum-ish values (comma-join multis): `--sort-by` `date|relevance`; `--workplace-type`
  `on-site|hybrid|remote`; `--employment-type` `full-time|part-time|contract|internship|temporary`;
  `--posted-limit` `24h|week|month`; `--salary` like `40k+ … 200k+`.
- **To enumerate a company's open roles: resolve its id (`company get`), then
  `job search --company-id <id>` paginated, then `job get` each posting for the JD.**

### profile

```bash
como linkedin profile get --public-identifier williamhgates  # one of: --url | --public-identifier | --profile-id
como linkedin profile get --url https://www.linkedin.com/in/williamhgates --main          # --main = cheaper, lighter profile
como linkedin profile get --url <url> --find-email --skip-smtp                             # best-effort work-email lookup
como linkedin profile search --search "Mark" --current-company <url|id> --title "engineer" \
                    --location "US" --geo-id <id> --first-name Mark --last-name Peterson \
                    --school <id> --past-company <id> --follower-of <id> --page 1
como linkedin profile posts --profile <url|id> --page 1
como linkedin profile comments --profile <url|id>
como linkedin profile reactions --profile <url|id>
```
`get` returns the full profile (name, headline, experience, education, skills, location).
`--find-email` runs an independent email lookup (best-effort; not always found). `profile
search` is the *basic* people search and is limited — many results are anonymized "LinkedIn
Member" with no link; for serious people-finding use **`leads search`** instead.

### leads — the powerful people search (use this for "who works at / recently joined")

```bash
# Everyone matching a title at a company:
como linkedin leads search --current-companies <companyUrlOrId> --current-job-titles "Software Engineer" --page 1
# People who recently changed jobs into a company (recent hires):
como linkedin leads search --current-companies <companyUrlOrId> --recently-changed-jobs --page 1
# Rich inclusion + EXCLUSION filters (all comma-joined multi-value):
como linkedin leads search --search "Machine Learning Engineer" --locations "US" \
                  --seniority-level-ids "120,210" --profile-languages en \
                  --exclude-seniority-level-ids "300,310" --company-headcount "51-200,201-500"
```
`leads search` is the high-quality people search (no "LinkedIn Member" anonymization).
Filters include: `--current-companies --past-companies --current-job-titles --past-job-titles
--locations --geo-ids --schools --industry-ids --seniority-level-ids --function-ids
--years-at-current-company-ids --years-of-experience-ids --recently-changed-jobs
--posted-on-linkedin --profile-languages --company-headcount --company-headquarter-locations`
plus an `--exclude-*` variant for most of them, and `--session-id` (pin results to one
backend resource for consistent pagination). **Multi-value filters are comma-joined
strings, not repeated flags.**

### post

```bash
como linkedin post get --url "https://www.linkedin.com/feed/update/urn:li:activity:..."   # FULL post
como linkedin post search --search "AI agents" --posted-limit 24h --sort-by relevance --page 1
como linkedin post search --authors-company <url|id>                # all posts by a company's employees
como linkedin post company-posts --company <url|id|universalName> --posted-limit month --page 1
como linkedin post user-posts --profile <url|id> --posted-limit month --sort-by date --page 1
como linkedin post group-posts --group <url|id> --page 1
como linkedin post comments --post <url> --sort-by relevance --page 1
como linkedin post reactions --post <url> --page 1
como linkedin post comment-replies --comment <url> --page 1
como linkedin post comment-reactions --comment <url> --page 1
```
`post search` extra filters: `--content-type --mentioning-member --mentioning-company
--author-keywords --authors-industry-id`. Reactions return profiles in opaque-ID URL form;
to get a normal profile URL, `profile get` each (use `--main` to keep it cheap).

### group / ads / service / geo

```bash
como linkedin group get --group-id 1898033          # or --url
como linkedin group search --search "python developers" --page 1
como linkedin ads get --ad-id 1104386363            # or --url
como linkedin ads search --keyword sales --account-owner ai --countries "US,CA,FR" \
                --date-option custom-date-range --startdate 2025-01-01 --enddate 2025-12-31
como linkedin service search --search "web development" --location "Australia" --geo-id <id> --page 1
como linkedin geo search --search "berlin"          # -> .elements[].geoId / .title
```

---

## Common command chains

**Get all of a company's open jobs *with* descriptions** (resolve id → search → get each):
```bash
ID=$(como linkedin company get --url <companyUrl> | jq -r '.id')
como linkedin job search --company-id "$ID" --page 1            # repeat over .pagination.totalPages
como linkedin job get --job-id <id>                             # full descriptionText for each hit
```

**Find people at a company (and those who recently joined):**
```bash
como linkedin leads search --current-companies <companyUrlOrId> --current-job-titles "Engineer" --page 1
como linkedin leads search --current-companies <companyUrlOrId> --recently-changed-jobs --page 1
```

**Resolve a location to a geo id, then use it as a precise filter:**
```bash
GEO=$(como linkedin geo search --search "New York" | jq -r '.elements[0].geoId')
como linkedin leads search --current-companies <id> --geo-ids "$GEO"
```

**Read a company's basics / a person's full profile / a work email:**
```bash
como linkedin company get --url <companyUrl>        # employeeCount, website, foundedOn, headquarter, ...
como linkedin profile get --url <profileUrl>        # full profile
como linkedin profile get --url <profileUrl> --find-email
```

---

## Pagination & gotchas

- `profile search` paginates with `--page` only (no pagination token).
- `leads search`, `post comments`, `post reactions`, `post comment-reactions`,
  `ads search` support both `--page` and `--pagination-token`; pass the token for pages ≥ 2.
- Multi-value options (companies, geo IDs, seniority IDs, …) take **comma-joined strings**,
  not repeated flags.
- A `*-search` hit is shallow; always `get` the full object before relying on its fields.
- A `get` returns the object **flat** (top-level fields, e.g. `.id`, `.descriptionText`) — not wrapped in `.element`.
- An empty `get` result usually means the listing expired on LinkedIn, not that it never existed.

## Errors

Non-zero exit on HTTP errors; the message is on stderr. Status codes: `400` bad request,
`401`/`403` auth, `404` not found, `429` rate limit (back off), `5xx` upstream/server.

---

## Python SDK (`import como`)

The same surface is a typed, Pydantic-v2 client — sync and async.

```python
from como import Como

with Como() as client:                                  # reads COMO_API_KEY / COMO_BASE_URL
    company = client.company.get(url="https://www.linkedin.com/company/openai")   # Company model (flat; .id, .name, ...)
    jobs = client.job.search(company_id=company.id, page=1)          # shallow hits
    for hit in jobs.elements:
        job = client.job.get(job_id=hit.id)                          # full record
        print(job.title, len(job.description_text or ""))
```

```python
import asyncio
from como import AsyncComo

async def main():
    async with AsyncComo() as client:
        leads = await client.leads.search(current_companies=company_url, recently_changed_jobs=True)
        print(leads.pagination.total_pages)
asyncio.run(main())
```

- Resources mirror the CLI: `client.profile|company|job|post|leads|group|ads|service|geo`.
- Methods mirror commands: `.get(...)`, `.search(...)`, `.posts(...)`, `.comments(...)`,
  `.reactions(...)`. Params are snake_case (`company_id`, `public_identifier`, `posted_limit`).
- Responses are Pydantic models — fields are snake_case on the model (`description_text`,
  `employee_count`) even though the raw JSON wire form is camelCase.
- Pagination helpers: `como.pagination.iter_pages(...)` / `aiter_pages(...)` walk pages
  (token-aware) so you don't hand-roll the `--page`/token loop.

## Using an LLM in your code (`como run`)

When a sub-task needs an LLM — classify/score/extract/filter a batch, evaluate
something — write normal **Anthropic or OpenAI SDK** code and run it with
**`como run`**. The SDKs are pre-authed to route through the como gateway, so you
**never set an API key or base URL**, and there's no provider key on the machine.

```bash
como run -- python classify.py          # any command; gateway env injected for it only
como run -- uv run --with anthropic classify.py   # if the SDK isn't installed yet
```

```python
# classify.py — no api_key, no base_url; como run sets them
import anthropic
client = anthropic.Anthropic()
r = client.messages.create(
    model="claude-haiku-4-5", max_tokens=10,
    messages=[{"role": "user", "content": f"Is {title} a decision-maker? yes/no"}],
)
```

- Run LLM code **through `como run`** (not bare `python`) — that's what injects the
  gateway credentials, scoped to that one process. Bare `python` won't have them.
- Models available via the gateway: `claude-opus-4-8`, `claude-sonnet-4-6`,
  `claude-haiku-4-5`, `gpt-4.1-nano`. Using any other model name fails.
- Use `claude-haiku-4-5` (or `gpt-4.1-nano`) for cheap/bulk sub-calls; reserve the
  larger models for hard reasoning.
