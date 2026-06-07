# como

Python SDK and CLI for the Como API.

A typed, ergonomic client for nine LinkedIn-data resources: profiles, companies,
posts, jobs, groups, ads, services, leads, and geographic IDs. Sync and async
clients, Pydantic v2 models, full CLI surface.

---

## Install

```bash
# in a project
uv add como          # or: pip install como

# from this monorepo, for development
cd packages/python
uv sync
```

## Authentication

The client reads two environment variables:

| Variable              | Default                     | Description           |
| --------------------- | --------------------------- | --------------------- |
| `COMO_API_KEY`        | _required_                  | Bearer token          |
| `COMO_API_BASE_URL`   | `https://api.como.sh`    | Override API base URL |

Or pass them explicitly:

```python
from como import Como
client = Como(api_key="como_live_...", base_url="https://api.como.sh")
```

---

## Quick start — CLI

```bash
export COMO_API_KEY=como_live_...

como --help                       # top-level help
como profile --help               # resource help
como profile get --url https://www.linkedin.com/in/williamhgates --pretty
como profile search --title "engineer" --location "San Francisco"
como company get --universal-name openai
como post get --url "https://www.linkedin.com/feed/update/urn:li:activity:..."
como job search --search "staff engineer"
como leads search --current-companies "urn:li:company:1234" --recently-changed-jobs
como geo search --search "berlin"
```

Add `--pretty` for syntax-highlighted JSON. Without it, output is single-line
JSON suitable for piping into `jq`:

```bash
como profile search --search kayla | jq '.elements[].linkedinUrl'
```

## Quick start — Python (sync)

```python
from como import Como

with Como() as client:
    profile = client.profile.get(public_identifier="williamhgates")
    print(profile.first_name, profile.headline)

    page = client.profile.search(title="engineer", location="San Francisco")
    for hit in page.elements:
        print(hit.name, hit.linkedin_url)
```

## Quick start — Python (async)

```python
import asyncio
from como import AsyncComo

async def main():
    async with AsyncComo() as client:
        profile = await client.profile.get(url="https://www.linkedin.com/in/williamhgates")
        print(profile.first_name)

asyncio.run(main())
```

---

## Resources

Every resource is available on both `Como` and `AsyncComo` with matching
method signatures (just `await` the async ones).

| Accessor          | Methods                                                                                       |
| ----------------- | --------------------------------------------------------------------------------------------- |
| `client.profile`  | `get`, `search`, `posts`, `comments`, `reactions`                                             |
| `client.company`  | `get`, `search`, `posts`                                                                      |
| `client.post`     | `search`, `get`, `company_posts`, `user_posts`, `comments`, `reactions`, `group_posts`, `comment_replies`, `comment_reactions` |
| `client.job`      | `get`, `search`                                                                               |
| `client.group`    | `get`, `search`                                                                               |
| `client.ads`      | `get`, `search`                                                                               |
| `client.service`  | `search`                                                                                      |
| `client.leads`    | `search`                                                                                      |
| `client.geo`      | `search`                                                                                      |

### Parameter naming

SDK methods accept **snake_case** Python kwargs; the client translates them to
camelCase on the wire. Multi-value filters take a comma-joined string:

```python
client.leads.search(
    search="engineer",
    current_companies="urn:li:company:1,urn:li:company:2",
    geo_ids="103644278",
    recently_changed_jobs=True,
)
```

### Constraints

Some endpoints require **at least one** of a set of identifiers — passing none
raises `ValueError`. Examples:

- `profile.get`: one of `url`, `public_identifier`, `profile_id`
- `company.get`: one of `url`, `universal_name`, `search`
- `job.get`: one of `job_id`, `url`
- `group.get`: one of `url`, `group_id`
- `ads.get`: one of `ad_id`, `url`

---

## Pagination

List endpoints return a result object with `elements` and `pagination`:

```python
page = client.profile.search(search="kayla", page=1)
print(page.pagination.total_pages, page.pagination.pagination_token)
```

Use `iter_pages` / `aiter_pages` to walk every page automatically:

```python
from como import Como, iter_pages

with Como() as client:
    for page in iter_pages(client.profile.search, search="kayla", max_pages=5):
        for hit in page.elements:
            print(hit.name)
```

The helper inspects the resource method's signature, so endpoints that don't
take a `pagination_token` won't be passed one.

---

## Errors

All errors inherit from `ComoError`. The HTTP status maps to a specific subclass:

| Status     | Exception              |
| ---------- | ---------------------- |
| 400        | `ComoBadRequestError`  |
| 401 / 403  | `ComoAuthError`        |
| 404        | `ComoNotFoundError`    |
| 429        | `ComoRateLimitError`   |
| 5xx        | `ComoServerError`      |
| (network)  | `ComoNetworkError`     |
| (other)    | `ComoAPIError`         |

```python
from como import Como, ComoAuthError, ComoRateLimitError

try:
    with Como() as client:
        client.profile.get(url="https://...")
except ComoAuthError:
    print("check your key")
except ComoRateLimitError as e:
    print("slow down", e.status_code, e.body)
```

Each `ComoAPIError` exposes `.status_code`, `.body` (parsed JSON if available),
and `.response` (the underlying `httpx.Response`).

---

## Development

Tooling lives at the `packages/python/` level.

```bash
# install everything (runtime + dev deps + the local package in editable mode)
uv sync

# run the test suite (respx-mocked, no network)
uv run pytest -q

# lint and format
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# run the CLI locally
uv run como --help
```

### Project layout

```
packages/python/
├── pyproject.toml
├── specs/                      # JSON schemas per endpoint (source of truth for shapes)
├── src/como/
│   ├── __init__.py             # public API: Como, AsyncComo, errors, iter_pages
│   ├── _config.py              # env vars, defaults
│   ├── _params.py              # clean_params, require_one_of
│   ├── _transport.py           # httpx wrappers, error mapping
│   ├── client.py               # Como / AsyncComo entry points
│   ├── errors.py               # exception hierarchy
│   ├── pagination.py           # iter_pages / aiter_pages
│   ├── models/                 # Pydantic v2 models (snake_case ↔ camelCase via to_camel)
│   ├── resources/              # one file per resource, sync + async classes
│   └── cli/                    # Typer-based CLI, one file per resource
└── tests/                      # respx-mocked tests
```

### Adding a new endpoint

1. Drop the spec JSON in `specs/<resource>__<action>.json`.
2. Add response models to `src/como/models/<resource>.py`.
3. Add a path constant + `_<action>_params` helper + sync and async methods to
   `src/como/resources/<resource>.py`.
4. If new — wire the resource into `client.py` and re-export from
   `resources/__init__.py`.
5. Add a Typer command in `src/como/cli/<resource>.py` (mirror the SDK method
   signature) and register it in `cli/_app.py`.
6. Add a respx-mocked test to `tests/test_<resource>.py`.

That's the pattern — every existing resource follows it.
