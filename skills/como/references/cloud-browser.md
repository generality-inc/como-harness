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

## Auth-walled sources (carrying the user's login)
`como browser` gives a **fresh** cloud browser (no user cookies). If a source needs the
user's own session (e.g. bookface behind their login), use `browser-harness`'s profile sync
instead — `sync_local_profile(...)` → `start_remote_daemon(profileId=…)` — which carries the
local Chrome **cookies** into a cloud browser. That path uses the user's own Browser Use key
(from browser-harness), not the broker; tell the user you're using it so they know why.
