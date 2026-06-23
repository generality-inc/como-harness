# CLAUDE.md

Guidance for AI agents editing the `como` Python SDK + CLI. Read this before
touching code — the conventions are load-bearing.

## Critical rule: brand neutrality

The Como API is a 1:1 passthrough over a third-party scraping service.
**Never name that service** in code, comments, docstrings, error messages,
file names, or commits. To callers, Como is the origin. LinkedIn is fine —
that's the data being described.

Specs under `specs/` are already scrubbed. Sanitize any new fetches.

## Package map

```
packages/python/
├── pyproject.toml
├── specs/                    # JSON schemas per endpoint — source of truth
│   └── _index.json           # resource→file map, lists every como_path
├── src/como/
│   ├── __init__.py           # public re-exports (curated, no leakage)
│   ├── _config.py            # COMO_API_KEY, COMO_BASE_URL
│   ├── _params.py            # clean_params, require_one_of
│   ├── _transport.py         # SyncTransport / AsyncTransport, error mapping
│   ├── client.py             # Como / AsyncComo — attaches all resources
│   ├── errors.py             # ComoError → ComoAPIError → status-specific
│   ├── pagination.py         # iter_pages, aiter_pages (signature-aware)
│   ├── models/               # one file per resource + _common.py
│   ├── resources/            # one file per resource: Sync + Async classes
│   └── cli/                  # one file per resource + _app.py + _output.py
└── tests/                    # respx-mocked, no network
```

## The pattern — every resource follows it

`profile.py` is the canonical reference. To add or modify an endpoint:

**1. Model** (`models/<resource>.py`)

Inherit from `models._common.BaseModel` (sets `to_camel` alias generator,
`populate_by_name=True`, `extra="allow"`). Default every field to `None` or
`[]`. Reuse `Pagination`, `DatePart`, `LocationField`, `MediaImage` from
`_common.py` and `Post`, `Comment`, `Reaction`, `PostActor` from `post.py`.

**2. Resource** (`resources/<resource>.py`)

```python
_PATH_GET = "/v1/ghost/foo"

def _get_params(*, url, foo_id) -> dict[str, str]:
    require_one_of(url=url, foo_id=foo_id)
    return clean_params({"url": url, "fooId": foo_id})

class FooResource(SyncResource):
    def get(self, *, url=None, foo_id=None) -> Foo:
        body = self._t.get(_PATH_GET, params=_get_params(url=url, foo_id=foo_id))
        return Foo.model_validate(body.get("element") or {})

class AsyncFooResource(AsyncResource):
    async def get(self, *, url=None, foo_id=None) -> Foo:
        body = await self._t.get(_PATH_GET, params=_get_params(url=url, foo_id=foo_id))
        return Foo.model_validate(body.get("element") or {})
```

Rules:
- Path constants at top, prefixed `_PATH_`. Format: `/v1/ghost/<kebab>`.
- Free-standing `_<action>_params` helpers — sync and async share param building.
- Always go through `clean_params({...})`. Never hand-build query strings.
- Use `require_one_of(a=a, b=b)` for must-have-one-of identifiers.
- Unwrapping:
  - Single element: `body.get("element") or {}`
  - List: validate whole body (*Result model has `elements` + `pagination`)
  - **`ads.get` validates whole body** (no envelope). Don't change this.
  - **`geo.search` returns `{id, elements}`** (no envelope, no pagination).

**3. Wire** (`client.py`)

Add `self.foo = FooResource(self._transport)` to both `Como.__init__` and
`AsyncComo.__init__`. Keep alphabetical.

**4. Export** (`resources/__init__.py`)

Re-export `FooResource` and `AsyncFooResource`. Alphabetical.

**5. CLI** (`cli/<resource>.py`)

```python
app = typer.Typer(no_args_is_help=True, help="Foo operations.")

@app.command("get")
def get_foo(
    url: str | None = typer.Option(None, "--url"),
    foo_id: str | None = typer.Option(None, "--foo-id"),
    pretty: bool = typer.Option(False, "--pretty"),
) -> None:
    """Get a foo by URL or ID."""
    with Como() as client:
        result = client.foo.get(url=url, foo_id=foo_id)
    emit(result, pretty=pretty)
```

Register in `cli/_app.py`: `app.add_typer(_foo_cli.app, name="foo")`.

Rules:
- One `typer.Typer` per resource. `no_args_is_help=True` always.
- CLI flags kebab-case; Python args snake_case.
- Always end with `emit(result, pretty=pretty)`.
- For `Optional[bool]` SDK args, pass `flag or None` so unset stays unset.

**6. Test** (`tests/test_<resource>.py`)

respx against `BASE = "https://api.test.local"`; env vars in an autouse
fixture. Cover happy path + one edge (require_one_of, special shape, or
param translation). See `tests/test_resources.py`.

## Conventions

- **Python: snake_case. Wire: camelCase.** Pydantic alias generator handles
  models; `clean_params` dict keys must already be camelCase (translate at
  that boundary).
- **Optional everywhere.** Payloads are sparse. `extra="allow"`
  keeps unknown fields accessible.
- **Bools on the wire are strings.** `clean_params` casts `True` → `"true"`.
- **Lists are CSV strings on the wire.** `clean_params` handles `list[str]`.

## Gotchas

- `pagination_token` isn't universal. `profile.search` doesn't take one;
  `profile.posts`, `post.comments`, `leads.search`, `ads.search` do.
  `iter_pages` introspects the signature — don't add the kwarg blindly to
  "be consistent."
- `post.company_posts` and `company.posts` share `/v1/ghost/company-posts`.
  `post.user_posts` and `profile.posts` share `/v1/ghost/profile-posts`.
  Two surface methods, one wire call — both must keep working.
- Spec source of truth: `specs/<resource>__<action>.json`. The `como_path`
  field is authoritative for the route.

## Tooling

```bash
uv sync                          # install
uv run pytest -q                 # tests (no network)
uv run ruff check src/ tests/    # lint
uv run ruff format src/ tests/   # format
uv run como --help               # CLI
```

Lint config in `pyproject.toml` under `[tool.ruff]`: line-length 120,
target py313, rules `E F W I B UP SIM RUF`. `RUF012` is ignored — Pydantic
v2 deep-copies field defaults per instance, so `elements: list[X] = []` is
safe and idiomatic.

## Don't

- Commit or push without explicit user approval.
- Reference any data source, infrastructure, or costs not part of the public `como` API.
- Hand-build query strings — always `clean_params`.
- "Fix" the special shapes (`ads.get`, `geo.search`).
- Add `pagination_token` to a method that doesn't need it.
