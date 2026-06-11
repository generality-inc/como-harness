# Driving a browser for sales research

Some sources have no API — a YC/bookface page, a company's own site, a portal behind a
login. For those, **use the `browser-harness` skill** (it's a separate skill; invoke it).
This doc is the como-specific policy on top of it.

## Cloud by default — say so
Start a **cloud** browser (Browser Use), **not** the user's local Chrome, unless the user
explicitly asks for local. When you start one, **tell the user**: e.g. *"Using a cloud
browser (Browser Use) for this — say the word if you'd rather I drive your local Chrome."*

Why cloud by default: it doesn't take over the user's machine/Chrome, it runs unattended,
and it's the same browser the cloud research agents use — so local and cloud behave the same.

The mechanism lives in the `browser-harness` skill — read it for the exact calls. The shape:
```python
# in browser-harness:
uuid = start_remote_daemon("work", ...)   # provisions a Browser Use cloud browser, prints a liveUrl
# … drive it: new_tab(url), js(...), click_at_xy(...), http_get(...) …
stop_remote_daemon("work")                # ALWAYS stop when done — it ends billing
```
Only fall back to local Chrome (Way 1 in browser-harness) if the user asks for it.

## The browser is operated by a coding agent, not a single LLM call
Driving a browser is **agent work** — a Claude Code instance using the `browser-harness`
skill, iterating (screenshot → act → verify). Do **not** try to do browser steps as one
`como run` LLM call. Use `como run` only for cheap in-code reasoning *within* the agent
(e.g. "given this page text, extract the company rows as JSON"). See
[workflows.md](workflows.md) for how this composes into local / cloud / parallel runs.

## Carrying a login into the cloud browser
If a source needs the user's session (e.g. bookface), `browser-harness` can sync the local
Chrome profile's cookies into the cloud browser (`sync_local_profile` → `start_remote_daemon(profileId=…)`).
Cookies only — not extensions/history. Use this when the source is auth-walled; otherwise a
fresh cloud browser is fine.
