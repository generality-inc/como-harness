# Driving a browser for sales research

Some sources have no API — a YC/bookface page, a company's own site, a portal behind a
login. This doc is the **como policy: where the browser comes from and how to set it up.**
The mechanics of *operating* a page (screenshots, clicks, scraping) live in the separate
**`browser-harness` skill — a dependency underneath this one.** Read it *after* you've
set up the como-provided browser here, not before, and only to drive the page.

## The model — read this before touching a browser

1. **The browser comes from como (the broker), never from a local Browser Use key.** You
   ask como for a browser and it hands back only a connection (a `cdp_url`). The provider
   key stays on the platform — same pattern as the LLM gateway.
2. **Cloud/remote by default. Do NOT use the user's local Chrome** unless they explicitly
   ask to watch or drive it locally. When you start a cloud browser, say so:
   *"Using a cloud browser for this — say the word if you'd rather I drive your local Chrome."*
   Hand them the `live_url` if they want to watch.
3. **Profile-first for anything behind a login.** Before doing *anything* on an auth-walled
   site, sort out the identity (next section). Never drive a fresh, logged-out browser into
   a login wall — the agent cannot sign in (no credentials/MFA, and it must stop at auth
   walls). A human logs in **once**, ahead of the task.
4. **Only then** invoke the `browser-harness` skill to operate the page, attached to the
   como `cdp_url` via `BU_CDP_URL`.

## Step 1 — auth-walled? Sort out the profile FIRST

A **profile** is a persistent cloud identity (cookies/localStorage) the platform stores. Log
in once; every browser you later start on that profile is already authenticated. The
underlying provider profile id never reaches you — you reference a profile by name or id.

**Decision before any browser work:**

- **Public page (no login)** → skip to Step 2 with a plain `como browser create`.
- **Needs a login** → is there already a profile for this site?
  ```bash
  como browser profile ls          # shared + your own; shows STATUS and HAS COOKIES FOR
  ```
  - **A usable profile exists** (covers the site, `status: ready`) → use it in Step 2 with
    `--profile <name>`.
  - **No profile / not logged in** → create one and **have the human log in before you do
    anything else**:
    ```bash
    como browser profile create "Bookface" --description "YC bookface session"
    como browser profile login "Bookface"
    #   → prints a live_url; the human opens it, signs in, presses Enter to save.
    ```
    `login` is human-in-the-loop by design — **stop and ask the user to complete it**, then
    continue. Status is observed, never guessed: `new` → (human login) → `ready`, and only an
    agent hitting a wall flips it to `needs_login` (tell the user to re-run `profile login`).

## Step 2 — get the browser from como, then drive it with browser-harness

```bash
# logged-in site → start ON the profile (already authenticated):
SESSION=$(como browser create --profile "Bookface")   # -> {id, cdp_url, live_url}
# public page → fresh browser, no profile:
# SESSION=$(como browser create)

CDP=$(echo "$SESSION" | jq -r .cdp_url); ID=$(echo "$SESSION" | jq -r .id)
echo "$SESSION" | jq -r .live_url      # share with the user if they want to watch

# NOW hand off to the browser-harness skill (the layer under this), attached to the como CDP url:
BU_CDP_URL="$CDP" browser-harness <<'PY'
new_tab("https://bookface.ycombinator.com"); wait_for_load(); print(page_info())
PY

# ALWAYS tear it down when finished — a running cloud browser bills until it times out:
como browser stop "$ID"
```

`browser-harness` attaches to an existing browser via `BU_CDP_URL` (see its own docs for the
attach + the iterate loop: screenshot → act → verify). It is **only** the driver — the
"which browser, cloud-or-local, which identity" decisions are made *here*, in como, before
you ever invoke it. Only fall back to local Chrome if the user explicitly asked.

## The browser is operated by a coding agent, not one LLM call

Driving a browser is **agent work** — a Claude Code instance using `browser-harness`,
iterating. Do **not** do browser steps as a single `como run` LLM call. Use `como run` only
for cheap in-code reasoning *within* the agent (e.g. "given this page text, extract the rows
as JSON"). See [workflows.md](workflows.md) for how this composes into local / cloud / parallel runs.

## HARD RULE — never automate LinkedIn with a browser

Do **not** drive LinkedIn through `browser-harness` / a cloud browser / a profile — it is a
**ban risk** for the account. `como browser profile login` **refuses** LinkedIn login targets.
For **all** LinkedIn data — companies, people, jobs, posts, profiles — use **`como linkedin`**
(the ghost research API), which needs no LinkedIn account of your own. See [cli.md](cli.md).
