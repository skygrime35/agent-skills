# Delivery: the artifact and its proof

"An artifact I can actually access and run from outside the build environment" has a different canonical form per type — this file defines it. The live checkpoint always presents: **the live URL first** (web-reachable types — see `hosting.md`), then the **exact artifact path**, **exact launch/install command** (copy-pasteable, actually executed once), and **proof**.

## Proof forms

- **Live URL** — the strongest proof, and the primary one for every web-reachable type: the user clicks and tries the must-haves themselves. The screenshot below is captured *through* that URL, as a record.

- **Screenshot** — anything visual (web-app, static-site, tui, browser-ext). This machine is headless: drive a browser with Playwright (`npx playwright screenshot` or a short script) or the claude-in-chrome MCP if connected; for TUIs, capture the terminal buffer or render via `textual run --screenshot` where supported. Show the *interesting* screens (the must-haves working), not just the landing page. Deliver via SendUserFile.
- **Transcript** — cli, library, bot-worker: the real commands and their real output, unedited, including at least one error-path demonstration (bad input → clean message).
- **curl output** — api: each must-have endpoint hit for real, showing request and response.

The **run** skill is the preferred way to launch the app for proof capture — it already knows the per-project-type launch patterns.

## Per-type artifact form

- **web-app:** production build in `dist/`/`.next` + `npm run preview` (or equivalent) as the launch command. If there's a backend: `docker compose up` as the one-command launch. Never present the dev server as "the artifact".
- **api:** one-command launch (`uvicorn app.main:app` or `docker compose up`), `/docs` reachable, `.env.example` documenting every variable.
- **cli:** installable package — `uv tool install .` / `cargo install --path .` / `npm i -g .` — verified by invoking the installed binary **from outside the repo directory**.
- **tui:** same as cli.
- **library:** built package file (path given) + fresh-env install proof: new venv/project → install → import/use snippet runs.
- **static-site:** `dist/` folder + preview command; note where it could be dropped (any static host) without doing it.
- **bot-worker:** launch command + Dockerfile; proof = logs of one event actually processed (simulated upstream is fine — say so).
- **browser-ext:** built zip + "Load unpacked" instructions; drive Chromium for a screenshot if possible, else transcript + blind spot.

## Rules

1. **The launch command is executed before it is presented.** A quickstart that was never run is a claim, not a deliverable.
2. **Proof shows must-haves**, not just that the process starts.
3. **Blind spots stated at the live checkpoint, with what was verified instead** ("native build unverified — Expo web preview attached").
4. Outside the project directory and the scratchpad, the only permitted mutations are the hosting ones (`hosting.md`: the new `<project>` vhost, compose project, cert, registry entry — all recorded in the deployment registry) — and those follow its guardrails to the letter.
