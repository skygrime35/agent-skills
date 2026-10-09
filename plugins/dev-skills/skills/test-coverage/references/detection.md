# Detection — probes, launchability, domain partition, referrals

Phase 0 of every mode. One `haiku-standard` per probe family, fanned out in parallel, synthesized by the main loop. Every probe returns either a **verified fact with its evidence** (file:line, command output) or an **explicit unknown** — never a plausible guess. **Trust the code over the docs**: a README that says "run `make test`" is a hypothesis until the command has been executed or its target read.

## 1. Probe families (wave 1)

### P1 — Surfaces
What kinds of user-facing surface does this project have? Tell-tales:

| Surface | Tell-tales |
|---|---|
| web-frontend | `package.json` with react/vue/svelte/next/nuxt; `index.html`; route dirs (`pages/`, `app/`, `src/routes/`) |
| api | route registration (`urls.py`, `router.`, `@app.get`, controllers/, OpenAPI spec) |
| cli | `bin` in package.json; `argparse`/`click`/`clap`/`cobra`; `main()` with arg parsing |
| jobs / workers | cron configs, celery/bull/sidekiq, `schedule`, queue consumers |
| mobile | `android/`, `ios/`, `pubspec.yaml`, react-native config |
| desktop | electron/tauri configs |
| webhooks | inbound routes verifying signatures (stripe, github, …) |

Each surface gets `confidence: high|low`; `low` queues a Phase 0 salvo question.

### P2 — Test frameworks and runners
For each framework found (vitest, jest, pytest, playwright, cypress, go test, cargo test, JUnit, emulator suites…), record: **exact run command** (from lockfiles/scripts, then proven by `--help` or a dry listing — never invented), test paths/globs, `kind` (unit | integration | e2e | emulator), `mutates_state` (touches a DB, filesystem, external service?), how to run **a single file** (build's per-agent isolation depends on it), and the native skip/todo idiom (consumed by `writing.md`).

### P3 — Launchability
Can the app be started locally, and how? Evidence ladder: a dev script (`npm run dev`, `make run`, `docker compose up`) → required env vars present or mockable → **actually start it and hit one page/endpoint**. Only a successful start proves `launchable: true`. Failure or missing secrets ⇒ `launchable: false` + the reason — the dynamic pass becomes a **declared blind spot**, never an inferred inventory. Protocol per surface: web ⇒ claude-in-chrome against the local URL (site permission required — if not granted, blind spot); mobile ⇒ emulator only if the project's own tooling scripts one; cli ⇒ the binary itself is the "running app".

### P4 — Routing / menu map
The skeleton the partition and the dynamic pass both use: route tables, navigation components, menu definitions, CLI subcommand trees, job schedules. Output: a tree of entry points with their source locations.

### P5 — Previous inventory + drift
If `.claude/test-coverage/inventory.yml` exists: read `generated_at.sha`, run `git diff --name-only SHA..HEAD -- <domain globs>`, list touched domains, count features whose `fingerprint.anchor` no longer greps. This drives bare-mode routing and the re-baseline decision (`inventory-schema.md` §3).

### P6 — Timing capability (mode speed; cheap enough to run always)
For each runner from P2: how **per-item durations** and **pass/fail/skip id sets** can be obtained (`speed.md` §1 recipes — pytest `--durations`/junit, vitest/jest JSON reporter, playwright JSON reporter + `--list`, a custom harness's own timing file or an env-gated hook); whether the project already keeps a timing history (declared as `speed.timing_sources`, format named from the file actually read); the parallelism settings **in effect** (`addopts`, `-n`, `workers`, `pool`, `isolate`, retries, step retries/timeouts) with `file:line`; and whether `speed.baseline` exists and is fresh (`git diff --name-only <baseline.sha>..HEAD -- <runners[].paths>` empty). A config comment documenting a measured limit (e.g. a worker cap because a shared target saturates) is recorded as **evidence**, never as an obstacle to remove.

## 2. Domain partition (the anti-overlap contract)

Built by the **main loop** from P1+P4 output, before any wave-2 fan-out:

- Every file/route belongs to **exactly one** domain, by disjoint globs. Prefer the project's own seams (top-level feature dirs, route groups, django apps, cargo workspace members) over invented ones.
- A `misc` catch-all domain is **mandatory** — its globs are "everything not matched above". A partition with holes silently un-inventories whatever falls through.
- Target size: a domain a `haiku-standard`/`sonnet-standard` agent can exhaust in one context (~30-80 source files). Bigger ⇒ split; a 3-file domain ⇒ merge into a neighbor.
- The partition is written into `inventory.yml` (`domains:`) before fan-out; `--domains=` prunes agents, never the partition itself.

## 3. Referral protocol

Each wave-2/4 explorer receives its globs plus this rule, verbatim in its prompt: *"If you discover functionality whose source lives outside your globs, do NOT inventory it. Emit one referral line: `REFERRAL: <path> — <one-line suspicion>`. The orchestrator routes it."* The main loop collects referrals, deduplicates them, and either routes each to the owning domain's agent (if still running / in a follow-up ask) or queues it for wave 6. A referral that ends up unowned is a **finding** (partition hole), not a silent drop.

## 4. Dynamic pass rules (wave 5)

- Navigate by the P4 menu tree: every menu, submenu, modal, context menu, keyboard shortcut discovered is walked once. Record each interactive element (buttons, links, toggles, forms) with its URL/route and a navigation trace.
- **Attachment rule**: a dynamically-seen feature must be attached to a static entry point (route, component file, command) before it may mint a FEAT. Unattachable ⇒ candidate handed to arbitration with its trace — it may be dead code's ghost, a CDN widget, or a real partition hole.
- Never log in with real production credentials; use the project's seeded dev accounts or fixtures. Never point the browser at a `prod_hosts` entry.

## 5. Config drift

Detection re-runs every invocation; `detected_at.sha` is the stamp. Structural drift (a framework appeared, a run command died, launchability flipped) updates `.claude/test-coverage.yml` with a one-line report. Drift on human-authored fields (`quirks`, `accepted_risks`, confirmed `prod_hosts`, `speed.serial_groups`, `speed.quarantine`, `speed.target_minutes`) ⇒ show the diff and ask, never silently overwrite — a shrunken `prod_hosts` list is a widened blast radius.
