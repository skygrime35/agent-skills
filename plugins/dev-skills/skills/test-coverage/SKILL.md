---
name: test-coverage
argument-hint: "[audit|build|verify|speed] [--domains=<list>] [--gaps=<sev>] [--levers=<list>] [--runners=<list>] [--project=<path>] [--no-dynamic] [--dry-run] [--help]"
description: "Use to grow a project's test suite until it covers every possible scenario of every feature — every button, route, endpoint, CLI command, background job — so that any bug becomes detectable by the suite. One governed run: inventory every feature (static + dynamic pass), derive every outcome per feature (nominal, expected errors, edge cases, bounded action chains), map scenarios to existing tests, then write the missing ones. Modes: audit (inventory + coverage mapping, P0-P3 gaps, writes only its report), build (writes ALL missing tests behind one hard gate, never touches application code — a discovered bug becomes a skipped test + a finding), verify (mechanical re-checks, zero writes), speed (makes the suite faster with precision-preserving levers — parallelism, DB reuse, retry budgets — never deleting, skipping or weakening a test). Tests run locally/CI only, never against production; preprod-only scenarios are gated toward /full-test. Portable via auto-detection + a .claude/test-coverage.yml config."
---

# /test-coverage

Grow a project's test suite until every scenario of every feature is either covered by a living test, consciously waived, or a named blind spot — so the suite itself becomes the bug detector. The skill inventories the entire feature surface with cheap parallel agents, derives every outcome each feature can produce, maps that against the existing tests (unit, integration, e2e, emulator), and writes everything missing.

This skill is **portable across any project**. It auto-detects the project's surfaces (web frontend, API, CLI, jobs), its test frameworks and runners, and whether the app is launchable for a dynamic exploration pass, on every run — and remembers the non-guessable specifics in a per-project `.claude/test-coverage.yml`. The living inventory persists in `.claude/test-coverage/inventory.yml`, timestamped by git SHA, diffable across runs through stable IDs.

Its central promise is a negative one: **it never fixes application code and never touches production.** A test that reveals a bug stays in the suite as an annotated skip plus a P0/P1 finding; an assertion is never weakened to go green — a suite that lies is worse than no suite. In `speed` it may edit test **infrastructure** (runner configs, conftest/setup files, the harness runner and its call structure) — never a test body, never an assertion, never application code.

## Usage

```
/test-coverage                    # interactive: detect the project, then propose audit, build, verify or speed
/test-coverage audit              # inventory features + scenarios, map coverage, P0-P3 gaps; writes inventory + report
/test-coverage build              # write ALL missing tests (consumes a fresh audit), one global hard gate, runs locally
/test-coverage verify             # mechanical consistency checks only — near-free, re-runnable, zero writes
/test-coverage speed              # measure per-test/step timings, plan + apply precision-preserving speed levers behind one hard gate, prove same tests / same results
/test-coverage --project=<path>   # target project directory (default: current directory)
/test-coverage --domains=<list>   # restrict to these inventory domains (e.g. auth,billing)
/test-coverage --gaps=<sev>       # build only these severities (e.g. P0,P1; default: all)
/test-coverage --levers=<list>    # speed: restrict to these levers (e.g. xdist,reuse-db,cov-off); others stay listed as not-applied
/test-coverage --runners=<list>   # speed: restrict to these runners (e.g. pytest,vitest); others stay listed as not-measured
/test-coverage --no-dynamic       # skip the dynamic exploration pass; it becomes a declared blind spot
/test-coverage --dry-run          # detect, plan, list what would be explored/derived/written (speed: plan levers from the last fresh baseline, apply nothing). Zero writes
/test-coverage --help             # print this Usage block and stop
```

If invoked with `--help`/`-h` and nothing else, print the Usage block above verbatim and stop.

Arguments override questions; anything not passed as an argument is asked interactively. An argument never overrides a **guardrail** — no flag skips the hard gate before writing tests, no flag lets a test target a production host, and `--gaps=` narrows a run without silently shrinking the inventory: excluded gaps stay `missing`, never disappear. Likewise no flag lets `speed` drop, skip or weaken a test — a quarantine entry exists only after an explicit per-entry human confirmation, and it is still executed; `--levers=`/`--runners=` narrow a run, the rest stays listed as not-applied / not-measured.

## What this skill is for / non-goals

**For:** building and maintaining an exhaustive test suite — the full feature inventory, the full scenario derivation, the coverage mapping, and the tests that close every gap — run and proven locally, with statuses honest enough that "green" means something — and, in `speed`, making that same suite as fast as the machine allows without losing a test or a bit of strictness.

**Not for:** executing the battery against preproduction — that is `/full-test`'s job; the two are complementary and independent (this skill manufactures the suite, `/full-test` runs it against preprod), and scenarios that require preprod are written but marked `gated-preprod` with a pointer to `/full-test`, never executed here. Not for fixing application bugs — a discovered bug is a finding, not a work item. Not for gating merges (→ `/safe-merge`) or judging the code quality of existing tests beyond whether they cover their scenario. Not for making a red suite green through speed changes — a failure that disappears under a lever is a lost detection, and the lever is refused.

## Eight governing principles (these override any convenience)

1. **An unknown scenario is worse than an untested one.** You cannot cover what you never inventoried — a bug in an unlisted feature is invisible forever, while a listed-but-missing scenario is at least a ranked gap. Inventory precedes everything; an unexplorable surface (app not launchable, domain excluded) is a **named blind spot** in every report. Verdicts are **green on what ran**.
2. **An expected error is a behavior to prove, not to assume.** The test of an error case verifies the error **actually occurs**, with the right observable (status, message, state left behind). If it does not occur — or a crash occurs instead — that is not a green test nor a scenario to delete: it is a discovered bug, and it is exactly the kind the whole exercise exists to catch.
3. **The skill manufactures tests, never fixes.** A discovered bug ⇒ the test is kept as an annotated skip/todo (`TC-BUG-nn / SCEN-nnnn`) + a P0/P1 finding + a `bugs:` entry in the inventory. Application code is **never** modified, and an assertion is never weakened to pass — one "adjusted" assertion converts a bug detector into a bug notarizer.
4. **Exhaustive per action, bounded by shared state.** Every outcome of every isolated action (nominal, each expected error, canonical edges); chains of 2-3 actions only where they share state (login→session, cart→checkout); anything longer is class `costly` — listed, priced, gated behind its own confirmation. Without this bound the inventory is infinite and arbitration impossible.
5. **A minted ID is minted forever.** FEAT/SCEN IDs survive refactors via fingerprint matching (anchor → symbol → arbitrated candidate); ambiguities are settled by the arbitration agent, never auto-merged; >30 % unmatched features stops the run and proposes an explicit re-baseline. Reused or re-minted IDs make audits undiffable and turn the finding history into noise.
6. **Written tests run locally/CI only — never against production.** Production hosts live in the config (`prod_hosts:`); before any test execution the runner's targets are checked against them, and `rg` sweeps the written tests for prod URLs. A scenario that genuinely needs preprod is written, marked `gated-preprod`, and handed to `/full-test` — this skill never inherits its deploy/reseed powers.
7. **Fan out massively for reading; one pair of hands per write; no silent caps.** Exploration, derivation, and mapping run on `sonnet-quick`/`sonnet-standard` (low/medium effort) across **disjoint domains** — out-of-scope discoveries are referrals routed by the main loop, never double-inventoried. One single `opus-deep` spend per run arbitrates — audit wave 6 (dedupe, kill evidence-less scenarios, settle IDs, rank P0-P3), speed wave 3 (rank levers, veto the unverifiable). `inventory.yml` is written by the main loop alone; in build, one agent per test file. The build worklist is **all** open gaps by default — any narrowing (`--gaps=`, a partial go) is stated in the report, never silent.
8. **Faster is only faster if it detects exactly the same bugs.** `speed` proves every lever by three invariants — same collected count per runner, same pass/fail/skip **id sets**, zero assertion diff — and refuses (reverts) any lever that breaks one, even if it is faster. A test that turns flaky under parallelism is isolated into a serial group, never deleted, never skipped; a retry budget is only reduced when replaced in the same lever by an equivalent guard (infrastructure vs functional failure classification) that keeps every functional failure visible. Recurrently-red steps may enter a **quarantine** — confirmed by the human one entry at a time, still executed once per run and reported apart. Speed is measured, never estimated: baseline before, proof after.

## Tooling

External CLIs: `git`, `rg`/`grep`, `jq`, `python3` (YAML probes), and **the project's own test runners** (detected, never reimplemented). Claude Code capabilities: **Agent tool** with the machine-local agent types (`sonnet-quick`, `sonnet-standard`, `opus-standard`, `opus-deep` — detected in Phase 0 under `~/.claude/agents/`; absent ⇒ fall back to the Agent tool's `model` parameter + session effort); **claude-in-chrome** MCP for the dynamic web pass (emulator/CLI harness for other surfaces when detected); **AskUserQuestion** for salvos and the hard gate; **TaskCreate/TaskUpdate** for phase tracking and mid-run resumability — a `go all` on 100+ tests must survive a crash; **Monitor** (or a background Bash) for the long baseline and campaign runs of `speed`, so a 40-minute suite never blocks the loop.

## Reference files (load on demand)

| File | When |
|---|---|
| `references/detection.md` | Phase 0 of any mode — probes, launchability, domain partition, referral protocol |
| `references/config-schema.md` | Reading/writing `.claude/test-coverage.yml` |
| `references/inventory-schema.md` | Reading/writing `inventory.yml`; ID stability rules; audit trailer |
| `references/scenario-derivation.md` | Audit wave 4 — the derivation grid per feature kind, bounding rules, cost classes |
| `references/audit-grid.md` | Mode audit — finding taxonomy, severity ladder, report + trailer contract |
| `references/writing.md` | Mode build — isolation, fixtures, skip/todo patterns, discovered-bug protocol |
| `references/speed.md` | Mode speed — measurement per runner, lever catalogue with precision invariants + verification recipes, flakiness protocol, allowed write surface, report + `speed:` config |
| `references/reporting.md` | Any report — statuses never collapsed, verdict wording, journal format |

---

# Procedure

Follow phases in order. TaskCreate the phases at start; append one line per completed step to `.claude/test-coverage/journal.md` (except in `verify`, which writes nothing). Placeholders are UPPERCASE (`PROJECT_ROOT`, `AUDIT_SHA`, `D` = domain count, `S` = suite count, `R` = runner count, `N` = flakiness-campaign run count).

**Mode routing (do this first):**
- `--help` → print the Usage block, stop.
- `verify` → Phase 0 steps 1–2 only (no interview, no config write) → **Mode: verify**. Zero writes anywhere, journal included.
- `--dry-run` → Phase 0 read-only, then print the plan (domains, agents that would fan out, scenarios that would be derived, tests that would be written) and stop. With `speed`: the lever plan is built from a **fresh** `speed.baseline`; none ⇒ ask whether to measure now — the baseline JSON is then the only file produced, stated as such — or stop with a plan marked « non mesuré ».
- `audit` / `build` → Phase 0 → the mode's section.
- `speed` → Phase 0 (probe P6 included) → **Mode: speed**; loads `references/speed.md` plus `writing.md` §1 (agent contract), §4 (baseline rules) and §5 (prod guardrail).
- bare `/test-coverage` → Phase 0 → propose the sensible mode (no inventory ⇒ audit; fresh inventory + open gaps ⇒ build; treated audit ⇒ verify or a new audit; a recorded baseline slower than `speed.target_minutes` ⇒ speed), confirm.

## Phase 0 — Resume, config, detection (all modes)

1. **Resume check.** If `.claude/test-coverage/journal.md` shows an in-progress run, read it and **offer to resume** at the last completed phase rather than blindly restarting — a half-written build must continue from its last completed test file, not re-plan; a half-applied `speed` resumes at its next lever with the gate answers already given, never re-measures a fresh baseline.
2. **Load + refresh config.** Read `.claude/test-coverage.yml` (schema: `references/config-schema.md`). **Re-run detection regardless — config goes stale.** On drift touching a human-authored field (`quirks`, `accepted_risks`, confirmed `prod_hosts`, `speed.serial_groups`, `speed.quarantine`, `speed.target_minutes`), **show the diff and ask before overwriting**. Secrets policy: env-var **names** only, never values.
3. **Detection fan-out** (`references/detection.md`) — one `sonnet-quick` per probe family: surfaces (web/api/cli/jobs); test frameworks with exact run commands, paths, `mutates_state`; launchability (how to start the app locally, proven by starting it — never assumed); routing/menu map; previous inventory + drift vs `generated_at.sha`; **timing capability** (P6 — per runner, how per-test/step durations and result id sets can be obtained, existing timing sources, freshness of `speed.baseline`).
4. **Announce + confirm.** One AskUserQuestion salvo (≤4): low-confidence surfaces, launchability if unproven, scope; in `speed`, whether to run the baseline measurement now (its expected duration stated — it executes the suite, it is not a project write). Skip anything config/args/`accepted_risks` already answer. Write/refresh `.claude/test-coverage.yml` (not in `verify`/`--dry-run`).

## Mode: audit

1. **Domain partition.** From the wave-1 probes, the main loop partitions the codebase into disjoint domains (globs; a `misc` catch-all is mandatory) and writes the partition into the inventory **before any fan-out**. Every explorer gets its globs plus the referral rule: an out-of-scope discovery is reported as one line (path + suspicion), never inventoried — the main loop routes referrals to the owning agent.
2. **Fan-out** — orchestration table (`--domains=` prunes rows 3, 7, 8):

| # | Work package | Files / area | Agent | Depends on | Wave |
|---|---|---|---|---|---|
| 1 | Detection probes: surfaces, frameworks, launchability, routing map, previous inventory + drift | repo root | sonnet-quick ×4-6 | Phase 0 | 1 |
| 2 | Domain partition + fan-out plan | probe output | main loop | 1 | 1 |
| 3 | Exhaustive static exploration — every button, route, handler, command, submenu, dormant feature | domain globs | sonnet-quick/standard ×D | 2 | 2 |
| 4 | Existing-test index — one agent per framework/suite (test → target map) | test dirs | sonnet-quick ×S | 2 | 2 |
| 5 | Dynamic pass if launchable (claude-in-chrome / emulator); not launchable ⇒ declared blind spot | running app | sonnet-standard | 2 | 2 |
| 6 | Reconcile static × dynamic, dedupe across domains, route referrals | raw inventory | sonnet-standard | 3, 5 | 3 |
| 7 | Scenario derivation per domain — nominal / each expected error / edges / bounded chains, cost classes | domain features | sonnet-standard ×D | 6 | 4 |
| 8 | Scenario ↔ existing-test mapping per domain | scenarios + index | sonnet-standard ×D | 4, 7 | 5 |
| 9 | Arbitration: final dedupe, kill anything without evidence, settle ambiguous ID matches, rank P0-P3 | per-domain syntheses + disputed cases only | **opus-deep** | 8 | 6 |
| 10 | Write `inventory.yml` + French report with machine-readable trailer | — | main loop | 9 | 7 |

   Waves 2-5 attach **evidence** to every feature/scenario (`file:line`, a screenshot or navigation trace from the dynamic pass, a probe output); wave 6 pre-dedupes so the arbitration receives per-domain syntheses and disputed cases, never the raw inventory. A dynamically-seen feature must be attached to a static entry point (route/URL/command) before it may mint a FEAT — otherwise it is a candidate for arbitration.
3. **Report + registers.** Write `.claude/test-coverage/audit-<YYYY-MM-DD>-<SHORTSHA>.md` in French per `references/audit-grid.md`: gaps P0→P3 (P0 = critical path with zero tests; P1 = expected error never verified on a main flow; P2 = uncovered edge case; P3 = costly chain / quality), **Risques assumés** from `accepted_risks:`, blind spots (unlaunchable surfaces, excluded domains), machine-readable trailer for build. Update the inventory's `coverage.status` per scenario. Verdict: « couvert sur le périmètre vérifié ».

## Mode: build

1. **Audit intake.** Load the latest audit. Fresh = `git diff --name-only AUDIT_SHA..HEAD -- <domain globs>` is empty ⇒ worklist = **all** `open` + `skipped` findings (scenarios `missing`/`partial`); `waived` and `gated-preprod` excluded by nature. Stale/absent ⇒ propose `audit` first (Recommended) or mechanically re-verify each consumed gap before acting.
2. **Baseline.** Run the existing suite locally **before writing anything**; record pre-existing failures — they are never attributed to new tests. A red baseline is stated in plain words at the gate.
3. **HARD GATE (the only one).** Present the full plan: gaps sorted P0→P3, grouped by target test file (framework + domain), files created vs modified, run commands, cost estimate, exclusions (`costly` scenarios each behind their own confirmation with their real cost stated; `gated-preprod` written but never run here). AskUserQuestion: go all / go per-group / no. Anything other than a clear go ⇒ **stop; nothing is written.**
4. **Parallel writing, isolation = the file.** First a serialized preliminary package for shared fixtures/helpers. Then one agent per target test file (`sonnet-standard`; `opus-standard` for e2e), in waves: each agent writes its tests, **runs only its own file locally**, iterates to green, never touches another test file nor application code, and re-checks the prod guardrail before every run.
5. **Discovered bug** (expected error absent, or a crash instead): keep the test as the framework's native skip/todo annotated `TC-BUG-nn / SCEN-nnnn`, add the `bugs:` entry, emit the P0/P1 finding. Never a fix, never a weakened assertion.
6. **Non-regression.** Full local suite at the end (mutating suites serialized, read-only in parallel), diffed against the baseline; any new breakage caused by shared fixtures is repaired before reporting.
7. **Close-out** (main loop alone): update `coverage` statuses (`covered`, `mapped_at_sha`), stamp the consumed audit's trailer (`applied` / `skipped` / `obsolete`, `treated:`), write the French report — tests written, discovered bugs each with its repro, remaining gaps, gated scenarios handed to `/full-test`, verdict **green on what ran**.

## Mode: speed

Load `references/speed.md`. Goal: the same suite, provably the same detections, in as little wall-clock as the machine allows. Runner kinds: `pytest`, `vitest/jest`, `playwright`, `custom-harness` (a project script driving steps — `mutates_state: true`, no known framework binary), `other` (measured if the config gives a command, otherwise a blind spot). `--runners=` prunes runners, `--levers=` prunes levers; both narrowings are stated in the report.

1. **Runner intake.** From `runners[]` + probe P6, list the runner kinds present with their timing recipe (`speed.md` §1) and timing sources (`speed.timing_sources`). A runner with no obtainable per-item timing is still measured for wall time and id sets; missing per-item data is a named blind spot.
2. **S1 Baseline — measure before touching anything.** Each runner runs **once, unchanged**, with its recipe: wall time, collected count, pass/fail/skip **id sets**, per-test/step durations, top-50 slowest, setup/teardown share. Custom harness: also ingest the declared timing history. Write `.claude/test-coverage/speed-baseline-<SHORTSHA>.json`. A red baseline is the reference set, not something to fix. A baseline older than HEAD on any `runners[].paths` ⇒ re-measure. Under `--dry-run`: reuse a fresh baseline; none ⇒ ask before measuring, never measure silently.
3. **S2 Analysis fan-out** — orchestration table (R = runner count):

| # | Work package | Files / area | Agent | Depends on | Wave |
|---|---|---|---|---|---|
| 1 | Probe P6 + baseline plan (recipes, expected durations, serialization of mutating runners) | runner configs | sonnet-quick ×R | Phase 0 | 1 |
| 2 | Baseline runs — mutating runners serialized, read-only in parallel | whole suite | main loop (background + Monitor) | 1 | 1 |
| 3 | pytest: shared-state census (autouse fixtures, `cache.clear()`, session/module fixtures, `transaction=True`, external services), xdist / reuse-db readiness, coverage tax | `conftest.py`, `pytest.ini`/`pyproject`, test dirs | sonnet-standard ×(1 per ~500 tests, disjoint dirs) | 2 | 2 |
| 4 | vitest/jest: pool, isolate, fileParallelism, `setupFiles` cost, jsdom-vs-node per file | `vitest.config`, setup files, slowest files | sonnet-standard | 2 | 2 |
| 5 | playwright: worker cap vs measured saturation, sharding, project split, retry semantics, remote target | `playwright.config`, slowest specs | opus-standard | 2 | 2 |
| 6 | custom harness: step dependency graph (produces/consumes), retry/timeout budget, infra-vs-functional failure classes, recurrently-red steps, parallelizable phases | harness runner + step modules + timing history | opus-standard ×(1 per phase group) + 1 for the runner | 2 | 2 |
| 7 | Arbitration: rank levers by gain/risk, **veto any lever whose invariant cannot be verified**, size serial groups, draft quarantine candidates | per-runner syntheses | **opus-deep** | 3–6 | 3 |
| 8 | Plan + HARD GATE | — | main loop | 7 | 4 |
| 9 | Apply levers one at a time, one runner per agent, each lever followed by its verification recipe | allowed write surface only (`speed.md` §5) | sonnet-standard (pytest/vitest), opus-standard (playwright/harness) | gate | 5 |
| 10 | Flakiness campaign (N runs), serial-group isolation | — | main loop + agents | 9 | 6 |
| 11 | Final proof + French report + `speed:` config block | — | main loop | 10 | 7 |

4. **S3 HARD GATE (the only one).** Present: the baseline table per runner; the ranked lever list, each with estimated gain, its precision invariant, its verification recipe and its rollback; the exact files that will be modified (must be ⊆ the allowed write surface — anything else is a plan bug, not a request); proposed serial groups; **quarantine candidates, each requiring its own explicit yes** (a "go all" never confirms a quarantine); cost (every lever re-runs its runner's full suite, plus the N-run campaign). AskUserQuestion: go all / go per-lever / no. Anything other than a clear go ⇒ **stop; nothing is written** (the baseline JSON already exists as a measurement artefact and is stated as such).
5. **S4 Apply — one lever at a time, per runner.** The agent edits only its runner's infrastructure files, runs the runner's **full** suite, checks the three invariants (`speed.md` §3) against the baseline, records the measured gain, and **reverts the lever if any invariant fails** (« levier refusé : … » with the evidence). A lever that is faster but loses a failure is refused, never tuned until it passes. Prod guardrail re-checked before every run.
6. **S5 Flakiness campaign** (`speed.md` §4). After all levers on a runner: N runs (default 3; 2 for e2e/harness, stated), random order where the runner supports it. Green at baseline and red in ≥1 run ⇒ isolate (serial group / own worker / serial phase), re-run N; still red ⇒ `TC-FLAKY-nn` finding (P2), stays isolated, never skipped.
7. **S6 Close-out** (main loop alone): write the `speed:` block into `.claude/test-coverage.yml` (baseline, applied, refused + reason, serial groups, quarantine, touched files, cov profile), write `.claude/test-coverage/speed-<YYYY-MM-DD>-<SHORTSHA>.md` in French per `speed.md` §6 with its trailer, journal lines, verdict « plus rapide à précision identique sur ce qui a tourné ».

## Mode: verify

Load only `.claude/test-coverage.yml` + `references/inventory-schema.md` (+ `references/speed.md` §3 when `speed.applied` is non-empty). Main loop or a single `sonnet-quick` — never more. Checks: **V1** inventory freshness (`git diff generated_at.sha..HEAD -- <globs>`); **V2** ID integrity (uniqueness, counters ≥ max, `chain_of` targets exist); **V3** living mapping (every test referenced by a `covered` scenario still exists, file + name, via `rg`); **V4** orphan skips (every `skip`/`todo`/`xfail` in the suite maps to an open `TC-BUG-nn` or a waiver — an orphan is phantom coverage, FAIL); **V5** status bijection (`covered` ⇒ ≥1 living test; `bug-found` ⇒ open `bugs:` entry; `waived` ⇒ `accepted_risks` entry); **V6** bounded green suite (fast unit suites only; unexecuted e2e/integration = **named BLIND SPOT**, not a pass); **V7** reverse drift (on-disk tests unmapped in the inventory ⇒ a signal for the next audit, not a FAIL); **V8** prod guardrail (`rg` the config's `prod_hosts` across test files — any unguarded hit is FAIL); **V9** speed invariants — only when `speed.applied` is non-empty: collected count per runner equals `speed.baseline.collected` (via each runner's count command), every serial-group marker still exists in the file it points to, every quarantine entry names a living test/step and carries `confirmed_by`; **V10** zero assertion drift in `speed.touched_files` — `git diff <speed.applied[].at_sha>..HEAD` on those files touches only infrastructure files or allowlisted marker lines (`speed.md` §3c), and no `skip`/`xfail`/`fixme`/`todo` was added (an addition is FAIL — phantom speed). Each check → **PASS / FAIL / WAIVED / BLIND SPOT**, never collapsed; waived counted in one quiet footer line. Print the table + verdict **green on what ran**. Writes nothing, not even the journal.
