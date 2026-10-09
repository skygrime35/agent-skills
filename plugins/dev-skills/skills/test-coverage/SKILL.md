---
name: test-coverage
description: "Grow a project's test suite until every scenario of every feature (button, route, endpoint, CLI command, job) is covered. Modes: audit (inventory + P0-P3 gaps), build (write missing tests, never touches app code), verify (mechanical checks), speed (faster suite, same detections)."
when_to_use: "Use for test coverage, missing tests, untested features, speed up the test suite, or covering every scenario. Tests run locally/CI only, never against production."
argument-hint: "[audit|build|verify|speed] [--dry-run] [flags...]"
---

# /test-coverage

Plugin options appear in this file as their configured value. In reference files they stay as `user_config.<key>` placeholders: use the value this file shows. If a value still shows as a placeholder here (option never configured), use its `default` in `${CLAUDE_SKILL_DIR}/../../.claude-plugin/plugin.json`.

Auto-detects surfaces, test frameworks, launchability and persists its state in `.claude/test-coverage.yml` and `.claude/test-coverage/inventory.yml` (stable IDs, timestamped by git SHA). It **never fixes application code and never touches production**: a test that reveals a bug stays as an annotated skip plus a P0/P1 finding. In `speed` it may edit test **infrastructure** only (runner configs, conftest/setup, harness runner), never a test body, an assertion or application code.

Reports follow `${user_config.test_coverage_report_language}` (auto = the user's conversation language, fallback en); every file, identifier and comment is English. The report templates in `references/` are written in English; when the report language differs, translate their headings and labels (the meaning and every rule stay identical).

## Usage

```
/test-coverage                    # detect the project, auto-select audit, build, verify or speed (routing rule below) and print the choice
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

With `--help`/`-h` and nothing else, print the Usage block verbatim and stop.

**Policy resolution** (every answer): command argument > `.claude/test-coverage.yml` > plugin option > recommended default. Plugin options: `${user_config.test_coverage_default_scope}` (`all` or `drifted-domains`), `${user_config.test_coverage_dynamic_pass}` (dynamic pass on/off), `${user_config.test_coverage_speed_target_minutes}` (used when `speed.target_minutes` is unset). Ask only when no safe default exists or a guardrail is hit. An argument never overrides a **guardrail**: no flag skips the build hard gate, no flag lets a test target a production host, `--gaps=` never shrinks the inventory (excluded gaps stay `missing`), no flag lets `speed` drop, skip or weaken a test (a quarantine entry needs an explicit per-entry human confirmation and is still executed). `--levers=`/`--runners=` narrow a run; the rest stays listed as not-applied / not-measured.

## Scope

Builds and maintains the exhaustive suite (inventory, scenario derivation, coverage mapping, gap-closing tests, proven locally) and, in `speed`, makes it faster without losing a test or a bit of strictness. Not for: running the battery against preproduction (`/full-test`; preprod-only scenarios are written, marked `gated-preprod`, never run here; the `prod_hosts` key name is shared with the full-test config), fixing application bugs (a bug is a finding), gating merges (`/safe-merge`), or making a red suite green through speed changes (such a lever is refused).

## Governing principles (override any convenience)

1. **Inventory precedes everything.** An unexplorable surface (app not launchable, domain excluded) is a **named blind spot** in every report. Verdicts are **green on what ran**.
2. **An expected error is a behavior to prove.** The test verifies the error actually occurs with the right observable (status, message, state left behind); if it does not occur, it is a discovered bug, never a green test nor a deleted scenario.
3. **Manufacture tests, never fix.** A discovered bug => annotated skip/todo (`TC-BUG-nn / SCEN-nnnn`) + P0/P1 finding + `bugs:` inventory entry. Never modify application code; never weaken an assertion to pass.
4. **Exhaustive per action, bounded by shared state.** Every outcome of every isolated action (nominal, each expected error, canonical edges); chains of 2-3 actions only where they share state; longer chains are class `costly`: listed, priced, behind their own confirmation.
5. **A minted ID is minted forever.** FEAT/SCEN IDs survive refactors via fingerprint matching (anchor, symbol, arbitrated candidate); ambiguities go to arbitration, never auto-merged; >30 % unmatched features stops the run and proposes an explicit re-baseline.
6. **Tests run locally/CI only, never against production; this covers existing tests too.** **Host sweep before ANY test execution** (baseline, timing run, non-regression, verify): `rg -n -o "https?://[A-Za-z0-9.-]+" <the test files and the code they import>` and list every host. Allowed without asking: `localhost`, `127.0.0.1`, `::1`, `0.0.0.0`, `*.local`, `*.test`, `*.internal`, compose service names, and hosts the config lists as preprod or mock. Any other host is **denied by default** (whether or not it is in `prod_hosts:` and whether or not it looks like production): a test reaching it unmocked is deselected from the run (`--deselect`, `-k 'not ...'`, or the runner's equivalent); if it cannot be deselected safely, that runner is not run at all. Report each denied host as a blind spot and ask to confirm `prod_hosts` or a mock. Never run a denied test to "see what happens", not even once. Preprod-only scenarios are written, marked `gated-preprod`, handed to `/full-test`; never inherit its deploy/reseed powers.
7. **Fan out for reading; one pair of hands per write; no silent caps.** Exploration, derivation and mapping run across **disjoint domains** (out-of-scope discoveries are referrals routed by the main loop). A single arbitration spend per run (audit wave 6, speed wave 3). `inventory.yml` is written by the main loop alone; in build, one agent per test file. The build worklist is **all** open gaps by default; any narrowing is stated in the report.
8. **Faster only if it detects exactly the same bugs.** `speed` proves every lever with three invariants (same collected count per runner, same pass/fail/skip id sets, zero assertion diff) and reverts any lever breaking one. A flaky-under-parallelism test goes to a serial group, never deleted or skipped; a retry budget shrinks only with an equivalent guard in the same lever. Quarantine is confirmed one entry at a time, still executed, reported apart. Baseline before, proof after.

## Agents and tools

Roles: **probe/explorer/verify** = `haiku-standard`; **derivation/mapping/reconcile/pytest-vitest edits** = `sonnet-standard`; **e2e, harness, playwright** = `opus-standard`; **arbitration** = `opus-deep` only on explicit user request or after `opus-standard` failed on it. Follow the project's orchestration section if present; otherwise use these types, among the agent types the Agent tool offers (missing type => the Agent tool's `model` parameter). Also: `git`, `rg`/`grep`, `jq`, `python3`, the project's own test runners (detected, never reimplemented), claude-in-chrome MCP for the dynamic web pass (absent => dynamic pass is a declared blind spot).

Degradations (each reported): no `AskUserQuestion` => plain-text question with the same options; no `TaskCreate`/`TaskUpdate` => phase checklist in `journal.md`; no `Monitor` => `run_in_background` plus polling.

## Reference files (load on demand)

| File | When |
|---|---|
| `${CLAUDE_SKILL_DIR}/references/detection.md` | Phase 0 of any mode — probes, launchability, domain partition, referral protocol |
| `${CLAUDE_SKILL_DIR}/references/config-schema.md` | Reading/writing `.claude/test-coverage.yml` |
| `${CLAUDE_SKILL_DIR}/references/inventory-schema.md` | Reading/writing `inventory.yml`; ID stability rules; audit trailer |
| `${CLAUDE_SKILL_DIR}/references/scenario-derivation.md` | Audit wave 4 — derivation grid per feature kind, bounding rules, cost classes |
| `${CLAUDE_SKILL_DIR}/references/audit-grid.md` | Mode audit — finding taxonomy, severity ladder, report + trailer contract |
| `${CLAUDE_SKILL_DIR}/references/writing.md` | Mode build — isolation, fixtures, skip/todo patterns, discovered-bug protocol |
| `${CLAUDE_SKILL_DIR}/references/speed.md` | Mode speed — measurement, lever catalogue, invariants, flakiness, write surface, report, `speed:` config |
| `${CLAUDE_SKILL_DIR}/references/reporting.md` | Any report — statuses never collapsed, verdict wording, journal format |

---

# Procedure

Follow phases in order. TaskCreate the phases at start; append one line per completed step to `.claude/test-coverage/journal.md` (except in `verify`, which writes nothing). Placeholders are UPPERCASE (`PROJECT_ROOT`, `AUDIT_SHA`, `D` = domain count, `S` = suite count, `R` = runner count, `N` = flakiness-campaign run count).

**Mode routing (do this first):**
- `--help` => print the Usage block, stop.
- `verify` => Phase 0 steps 1-2 only (no config write) => **Mode: verify**. Zero writes anywhere, journal included.
- `--dry-run` => Phase 0 read-only, then print the plan (domains, fan-out, scenarios to derive, tests to write) and stop. With `speed`: the lever plan is built from a **fresh** `speed.baseline`; none => ask whether to measure now (the baseline JSON is then the only file produced, stated as such) or stop with a plan marked "not measured".
- `audit` / `build` => Phase 0 => the mode's section.
- `speed` => Phase 0 (probe P6 included) => **Mode: speed**; loads `speed.md` plus `writing.md` §1 (agent contract), §4 (baseline rules), §5 (prod guardrail).
- bare `/test-coverage` => Phase 0 => apply the routing rule and **print the choice, no question**: no inventory => audit; fresh inventory + open gaps => build (still behind its hard gate); treated audit => verify; a recorded baseline slower than the speed target => speed.

## Phase 0 — Resume, config, detection (all modes)

1. **Resume.** A recent in-progress run in `journal.md` resumes automatically at its last completed phase (a half-written build continues from its last completed test file; a half-applied `speed` at its next lever with gate answers kept, never re-measuring a fresh baseline). Say so in one line.
2. **Config.** Read `.claude/test-coverage.yml` (`config-schema.md`). **Re-run detection regardless** (config goes stale). On drift of a human-authored field (`quirks`, `accepted_risks`, confirmed `prod_hosts`, `speed.serial_groups`, `speed.quarantine`, `speed.target_minutes`): **keep the human value and report the diff; never overwrite.** Env-var **names** only, never values.
3. **Detection fan-out** (`detection.md`): one `haiku-standard` per probe family: surfaces; test frameworks (exact run commands, paths, `mutates_state`); launchability (proven by starting the app); routing/menu map; previous inventory + drift vs `generated_at.sha`; **timing capability** (P6).
4. **Announce.** Print the detected scope and the resolved policy (apply `${user_config.test_coverage_default_scope}` and the dynamic-pass option). Ask (one AskUserQuestion salvo, <=4) only for what has no safe default: low-confidence surfaces, unproven launchability, and in `speed` whether to run the baseline now (its expected duration stated; it executes the suite). Write/refresh `.claude/test-coverage.yml` (not in `verify`/`--dry-run`).

## Mode: audit

1. **Domain partition.** The main loop partitions the codebase into disjoint domains (globs; a `misc` catch-all is mandatory) and writes it into the inventory **before any fan-out**. Every explorer gets its globs plus the referral rule (`detection.md` §3).
2. **Fan-out** (`--domains=` prunes rows 3, 7, 8):

| # | Work package | Files / area | Agent | Depends on | Wave |
|---|---|---|---|---|---|
| 1 | Detection probes: surfaces, frameworks, launchability, routing map, previous inventory + drift | repo root | haiku-standard x4-6 | Phase 0 | 1 |
| 2 | Domain partition + fan-out plan | probe output | main loop | 1 | 1 |
| 3 | Exhaustive static exploration — every button, route, handler, command, submenu, dormant feature | domain globs | haiku-standard (sonnet-standard for dense domains) x D | 2 | 2 |
| 4 | Existing-test index — one agent per framework/suite (test -> target map) | test dirs | haiku-standard x S | 2 | 2 |
| 5 | Dynamic pass if launchable (claude-in-chrome / emulator); not launchable => declared blind spot | running app | sonnet-standard | 2 | 2 |
| 6 | Reconcile static x dynamic, dedupe across domains, route referrals | raw inventory | sonnet-standard | 3, 5 | 3 |
| 7 | Scenario derivation per domain — nominal / each expected error / edges / bounded chains, cost classes | domain features | sonnet-standard x D | 6 | 4 |
| 8 | Scenario <-> existing-test mapping per domain | scenarios + index | sonnet-standard x D | 4, 7 | 5 |
| 9 | Arbitration: final dedupe, kill anything without evidence, settle ambiguous ID matches, rank P0-P3 | per-domain syntheses + disputed cases only | **opus-deep** (explicit request or after opus-standard failure; else opus-standard) | 8 | 6 |
| 10 | Write `inventory.yml` + report with machine-readable trailer | — | main loop | 9 | 7 |

   Waves 2-5 attach **evidence** to every feature/scenario (`file:line`, screenshot/navigation trace, probe output); wave 3 pre-dedupes so arbitration (wave 6) gets per-domain syntheses and disputed cases, never the raw inventory. A dynamically-seen feature must attach to a static entry point before it may mint a FEAT, else it goes to arbitration.
3. **Report + registers.** Write `.claude/test-coverage/audit-<YYYY-MM-DD>-<SHORTSHA>.md` per `audit-grid.md` (gaps P0->P3: P0 = critical path with zero tests; P1 = expected error never verified on a main flow; P2 = uncovered edge case; P3 = costly chain / quality), accepted risks from `accepted_risks:`, blind spots, trailer for build. Update `coverage.status` per scenario. Verdict: "covered on the verified scope".

## Mode: build

1. **Audit intake.** Fresh = `git diff --name-only AUDIT_SHA..HEAD -- <domain globs>` is empty => worklist = **all** `open` + `skipped` findings (`missing`/`partial`); `waived` and `gated-preprod` excluded. Stale/absent => run `audit` first (recommended) or mechanically re-verify each consumed gap.
2. **Baseline.** After the host sweep (principle 6), run the existing suite locally, minus denied tests, **before writing anything**; record pre-existing failures (never attributed to new tests); state a red baseline plainly at the gate.
3. **HARD GATE (the only one; kept regardless of options).** Present the full plan: gaps P0->P3 grouped by target test file (framework + domain), files created vs modified, run commands, cost estimate, exclusions (`costly` scenarios each behind their own confirmation with real cost; `gated-preprod` written, never run). AskUserQuestion: go all / go per-group / no. Anything other than a clear go => **stop; nothing is written.** A "go ahead" in the original request does not count: the go must answer the plan just presented, and a small project never waives the gate.
4. **Parallel writing, isolation = the file.** First a serialized package for shared fixtures/helpers. Then one agent per target test file (`sonnet-standard`; `opus-standard` for e2e), in waves: each writes its tests, **runs only its own file locally**, iterates to green, never touches another test file nor application code, and applies principle 6 before every run.
5. **Discovered bug**: principle 3 (annotated skip/todo, `bugs:` entry, P0/P1 finding).
6. **Non-regression.** Full local suite at the end (mutating suites serialized, read-only in parallel), diffed against the baseline; any breakage from shared fixtures is repaired before reporting.
7. **Close-out** (main loop alone): update `coverage` statuses (`covered`, `mapped_at_sha`), stamp the consumed audit's trailer (`applied`/`skipped`/`obsolete`, `treated:`), write the report: tests written, discovered bugs each with repro, remaining gaps, gated scenarios handed to `/full-test`, verdict **green on what ran**.

## Mode: speed

Load `speed.md`. Goal: the same suite, provably the same detections, in minimal wall-clock. Runner kinds: `pytest`, `vitest/jest`, `playwright`, `custom-harness` (project script driving steps, `mutates_state: true`), `other` (measured only if the config gives a command, else a blind spot). `--runners=`/`--levers=` narrowings are stated in the report.

1. **Runner intake.** List runner kinds from `runners[]` + probe P6 with their timing recipe (`speed.md` §1) and `speed.timing_sources`. No obtainable per-item timing => still measure wall time and id sets; the gap is a named blind spot.
2. **S1 Baseline — before touching anything.** After the host sweep (principle 6), each runner runs **once, unchanged** (denied tests deselected and reported): wall time, collected count, pass/fail/skip **id sets**, per-test/step durations, top-50 slowest, setup/teardown share (custom harness: also its timing history). Write `.claude/test-coverage/speed-baseline-<SHORTSHA>.json`. A red baseline is the reference set, not something to fix. Baseline older than HEAD on any `runners[].paths` => re-measure. Under `--dry-run`: reuse a fresh baseline; none => ask before measuring, never measure silently.
3. **S2 Analysis fan-out** (R = runner count):

| # | Work package | Files / area | Agent | Depends on | Wave |
|---|---|---|---|---|---|
| 1 | Probe P6 + baseline plan (recipes, expected durations, serialization of mutating runners) | runner configs | haiku-standard x R | Phase 0 | 1 |
| 2 | Baseline runs — mutating runners serialized, read-only in parallel | whole suite | main loop (background + Monitor) | 1 | 1 |
| 3 | pytest: shared-state census (autouse fixtures, `cache.clear()`, session/module fixtures, `transaction=True`, external services), xdist / reuse-db readiness, coverage tax | `conftest.py`, `pytest.ini`/`pyproject`, test dirs | sonnet-standard x (1 per ~500 tests, disjoint dirs) | 2 | 2 |
| 4 | vitest/jest: pool, isolate, fileParallelism, `setupFiles` cost, jsdom-vs-node per file | `vitest.config`, setup files, slowest files | sonnet-standard | 2 | 2 |
| 5 | playwright: worker cap vs measured saturation, sharding, project split, retry semantics, remote target | `playwright.config`, slowest specs | opus-standard | 2 | 2 |
| 6 | custom harness: step dependency graph (produces/consumes), retry/timeout budget, infra-vs-functional failure classes, recurrently-red steps, parallelizable phases | harness runner + step modules + timing history | opus-standard x (1 per phase group) + 1 for the runner | 2 | 2 |
| 7 | Arbitration: rank levers by gain/risk, **veto any lever whose invariant cannot be verified**, size serial groups, draft quarantine candidates | per-runner syntheses | **opus-deep** (explicit request or after opus-standard failure; else opus-standard) | 3-6 | 3 |
| 8 | Plan + HARD GATE | — | main loop | 7 | 4 |
| 9 | Apply levers one at a time, one runner per agent, each followed by its verification recipe | allowed write surface only (`speed.md` §5) | sonnet-standard (pytest/vitest), opus-standard (playwright/harness) | gate | 5 |
| 10 | Flakiness campaign (N runs), serial-group isolation | — | main loop + agents | 9 | 6 |
| 11 | Final proof + report + `speed:` config block | — | main loop | 10 | 7 |

4. **S3 HARD GATE (the only one; kept regardless of options).** Present: baseline table per runner; ranked levers each with estimated gain, precision invariant, verification recipe, rollback; the exact files to modify (must be within the allowed write surface; anything else is a plan bug); proposed serial groups; the target `speed.target_minutes` (or `${user_config.test_coverage_speed_target_minutes}`); **quarantine candidates, each requiring its own explicit yes** (a "go all" never confirms a quarantine); cost (every lever re-runs its runner's full suite, plus the N-run campaign). AskUserQuestion: go all / go per-lever / no. Anything other than a clear go => **stop; nothing is written** (the baseline JSON already exists as a measurement artefact, stated as such).
5. **S4 Apply — one lever at a time, per runner.** The agent edits only its runner's infrastructure files, runs the runner's **full** suite, checks the three invariants (`speed.md` §3) against the baseline, records the gain, and **reverts the lever if any invariant fails** ("lever refused: ..." with evidence). A faster lever that loses a failure is refused, never tuned until it passes. Principle 6 re-checked before every run.
6. **S5 Flakiness campaign** (`speed.md` §4). After all levers on a runner: N runs (default 3; 2 for e2e/harness, stated), random order where supported. Green at baseline and red in >=1 run => isolate (serial group / own worker / serial phase), re-run N; still red => `TC-FLAKY-nn` finding (P2), stays isolated, never skipped.
7. **S6 Close-out** (main loop alone): write the `speed:` block into `.claude/test-coverage.yml` (baseline, applied, refused + reason, serial groups, quarantine, touched files, cov profile), write `.claude/test-coverage/speed-<YYYY-MM-DD>-<SHORTSHA>.md` per `speed.md` §6 with its trailer, journal lines, verdict "faster at identical precision on what ran".

## Mode: verify

Load only `.claude/test-coverage.yml` + `inventory-schema.md` (+ `speed.md` §3 when `speed.applied` is non-empty). Main loop or a single `haiku-standard`, never more. Checks: **V1** inventory freshness (`git diff generated_at.sha..HEAD -- <globs>`); **V2** ID integrity (uniqueness, counters >= max, `chain_of` targets exist); **V3** living mapping (every test referenced by a `covered` scenario still exists, file + name, via `rg`); **V4** orphan skips (every `skip`/`todo`/`xfail` in the suite maps to an open `TC-BUG-nn` or a waiver; an orphan is phantom coverage, FAIL); **V5** status bijection (`covered` => >=1 living test; `bug-found` => open `bugs:` entry; `waived` => `accepted_risks` entry); **V6** bounded green suite (fast unit suites only; unexecuted e2e/integration = **named BLIND SPOT**, not a pass); **V7** reverse drift (on-disk tests unmapped in the inventory => signal for the next audit, not a FAIL); **V8** prod guardrail (`rg` the config's `prod_hosts` across test files; any unguarded hit is FAIL); **V9** speed invariants — only when `speed.applied` is non-empty: collected count per runner equals `speed.baseline.collected`, every serial-group marker still exists where it points, every quarantine entry names a living test/step and carries `confirmed_by`; **V10** zero assertion drift in `speed.touched_files` — `git diff <speed.applied[].at_sha>..HEAD` on those files touches only infrastructure files or allowlisted marker lines (`speed.md` §3c), and no `skip`/`xfail`/`fixme`/`todo` was added (an addition is FAIL). Each check => **PASS / FAIL / WAIVED / BLIND SPOT**, never collapsed; waived counted in one quiet footer line. Print the table + verdict **green on what ran**. Writes nothing, not even the journal.
