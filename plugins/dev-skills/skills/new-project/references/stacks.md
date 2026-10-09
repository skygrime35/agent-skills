# Canonical project types & stack matrix

Classification pilots everything downstream: stack, scaffold, linters, tests, artifact form, proof form. Pick the **primary** type (a web app with an API is `web-app` fullstack, not two projects).

Resolution order for the stack: user's explicit wish → `~/.claude/new-project.yml` per-type preference → matrix default below → (off-matrix) research pass. Before committing to a stack, check Phase 0's runtime detection — never propose a toolchain that isn't installed without flagging the install as part of the plan, and any install is **user-space only** (`uv`, `corepack`/`nvm`, `rustup`), never a system-wide package change (SKILL.md principle 8).

## The matrix

| Type | Default stack | Scaffold | Linters | Tests | Artifact | Proof |
|---|---|---|---|---|---|---|
| **web-app** | Vite + React + TypeScript (Next.js if SSR/SEO matters) | `npm create vite@latest` | eslint, tsc `--noEmit`, prettier | vitest + Playwright smoke | prod build + `npm run preview` (+ Dockerfile if backend) | screenshot of key screens |
| **api** | Python 3.12 + FastAPI + uv | `uv init` | ruff (lint+format), mypy | pytest + httpx | `uvicorn` cmd or docker image; OpenAPI at `/docs` | `curl` transcript of real endpoints |
| **cli** | Python + uv + Typer (Rust + clap if perf/distribution matters) | `uv init` / `cargo new` | ruff+mypy / clippy+fmt | pytest / `cargo test` | `uv tool install .` wheel / release binary | transcript: `--help` + real invocations |
| **tui** | Python + Textual (Rust + ratatui) | `uv init` / `cargo new` | as cli | as cli | as cli | terminal screenshot or recorded transcript |
| **library** | language of the target ecosystem | native init | ecosystem standard | unit tests, **must-haves covered** | built package (wheel/tarball/crate) | fresh-env install + usage transcript |
| **static-site** | Astro (plain HTML if truly tiny) | `npm create astro@latest` | eslint, prettier | build = the test; link check | `dist/` + preview server | screenshot |
| **bot-worker** | Python + uv (Node if the SDK is JS-first) | `uv init` | ruff, mypy | pytest with mocked upstream | run command + `.env.example` + Dockerfile | log transcript of one real/simulated event handled |
| **browser-ext** | Vite + TypeScript, Manifest V3 | vite webextension template | eslint, tsc, `web-ext lint` | vitest for logic | zip loadable via "Load unpacked" | screenshot in Chromium if drivable, else transcript + **blind spot** |

Conventions that ride along with every stack: `.gitignore` from the ecosystem template, `.env.example` whenever env vars exist (never a real `.env` in git), pinned/lockfile dependencies. **Web-reachable types (web-app, api, static-site, bot-worker with a web surface) additionally get a Dockerfile/compose file suitable for the hosting recipe** (`hosting.md`) — loopback port binding parameterized, `restart: unless-stopped`, named volumes for stateful services — because the hosted URL is part of their deliverable. **And when the brief's data expectations imply persistence** ("things are still there next time, from another device too"), the web-app type is **fullstack by default**: a real backend + database in the same compose stack — never a localStorage stand-in for a spec that promises persistence.

## Off-matrix procedure

For mobile, desktop GUI, games, embedded, plugins for a specific host…

1. **Research briefly** (one agent, web search allowed): the current mainstream stack for that platform with the best CLI-only story.
2. **Prefer stacks this machine can at least build or preview headlessly**: mobile → Expo (web preview + QR); desktop → Tauri (build yes, GUI launch no); games → web-based (Phaser/three.js) unless told otherwise.
3. **Name the blind spots in the spec, before Checkpoint 1** — e.g. "iOS native build impossible on this machine; artifact = Expo project + QR code, native build is a blind spot". The user GOes with eyes open. A blind spot is never discovered at the live checkpoint.
4. Everything else (DoD, proof, atomic commits, docs) applies unchanged — only the *form* of artifact and proof adapts.
