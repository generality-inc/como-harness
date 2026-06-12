# Driving a browser for sales research

Some sources have no API — a YC/bookface page, a company's own site, a portal behind a
login. For those, drive a browser with the **`browser-harness` skill** (separate skill;
invoke it). This doc is the como-specific policy + how to get the browser.

## Cloud by default — through como, and say so
Use a **cloud** browser, **not** the user's local Chrome, unless the user explicitly asks
for local. Get it from como (the broker) — **don't** use a Browser Use key locally; como
holds the key and hands back only a connection. When you start one, **tell the user**:
*"Using a cloud browser for this — say the word if you'd rather I drive your local Chrome."*

Why cloud by default: it doesn't take over the user's machine/Chrome, runs unattended, needs
no Browser Use key on the machine, and it's the same browser the cloud research agents use —
so local and cloud behave the same.

## The flow: `como browser` → attach `browser-harness`
```bash
# 1. ask como for a cloud browser (platform's key; only a CDP url comes back)
SESSION=$(como browser create)            # -> {"id": "...", "cdp_url": "...", "live_url": "..."}
CDP=$(echo "$SESSION" | jq -r .cdp_url)
ID=$(echo "$SESSION" | jq -r .id)
echo "$SESSION" | jq -r .live_url         # share this with the user to watch

# 2. drive it with the browser-harness skill, attached to that CDP url:
BU_CDP_URL="$CDP" browser-harness <<'PY'
new_tab("https://example.com"); wait_for_load(); print(page_info())
PY

# 3. ALWAYS tear it down when done
como browser stop "$ID"
```
`browser-harness` attaches to an existing browser via `BU_CDP_URL` (see its `install.md`).
Only fall back to local Chrome (Way 1 in browser-harness) if the user asks for it.

## The browser is operated by a coding agent, not a single LLM call
Driving a browser is **agent work** — a Claude Code instance using `browser-harness`,
iterating (screenshot → act → verify). Do **not** do browser steps as one `como run` LLM
call. Use `como run` only for cheap in-code reasoning *within* the agent (e.g. "given this
page text, extract the company rows as JSON"). See [workflows.md](workflows.md) for how this
composes into local / cloud / parallel runs.

## Auth-walled sources → use a **browser profile** (log in once, reuse forever)
`como browser create` gives a **fresh** cloud browser (no cookies). For a source behind a
login (e.g. bookface), don't make the user log in every run — use a **profile**: a persistent
cloud identity the platform stores. The human logs in **once**; afterwards every browser you
start on that profile is already authenticated.

```bash
# one-time, human in the loop — they sign in via a live view:
como browser profile create "Bookface" --description "YC bookface session"
como browser profile login "Bookface"
#   → prints a live_url; the human opens it, navigates anywhere, signs in, presses Enter to save.

# every run after that — start authenticated, no login needed:
SESSION=$(como browser create --profile "Bookface")   # -> {id, cdp_url, live_url}
CDP=$(echo "$SESSION" | jq -r .cdp_url); ID=$(echo "$SESSION" | jq -r .id)
BU_CDP_URL="$CDP" browser-harness <<'PY'
new_tab("https://bookface.ycombinator.com/companies"); wait_for_load(); print(page_info())
PY
como browser stop "$ID"
```
List profiles with `como browser profile ls` (shared + your own). Profiles are **private** by
default (`--shared` to let the whole workspace use one). Status is **observed, never guessed**:
a fresh profile is `new`, a human login makes it `ready`, and it only flips to `needs_login`
when an agent actually hits a login wall — if that happens, tell the user to re-run
`como browser profile login <name>`. The underlying provider profile id never reaches you; you
only ever name a profile.

## HARD RULE — never automate LinkedIn with a browser
Do **not** drive LinkedIn through `browser-harness` / a cloud browser / a profile — it is a
**ban risk** for the account. `como browser profile login` **refuses** LinkedIn login targets,
and a profile that ends up holding `linkedin.com` cookies is flagged with a warning. For **all**
LinkedIn data — companies, people, jobs, posts, profiles — use **`como linkedin`** (the ghost
research API), which needs no LinkedIn account of your own. See [cli.md](cli.md).
