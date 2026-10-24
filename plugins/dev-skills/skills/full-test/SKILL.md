---
name: full-test
argument-hint: "[fix-loop] [--suites=..|--all] [--redeploy=..] [--reseed|--no-reseed] [--dry-run]"
description: "Runs a project's full test battery against its preprod environment to validate a branch before promotion: detects the branch-to-environment mapping and preprod suites, redeploys if needed, gates on the served SHA, runs the suites, follows progress and reports blind spots. Has an autonomous fix-loop mode. Never touches production: also loaded to refuse tests or reseeds aimed at prod."
when_to_use: "test preprod, validate my branch, run all tests on preprod, full test, redeploy and test, make preprod green, fix-loop; also when asked to run e2e/the test battery or a reseed against production or the live site (this skill must be loaded to refuse and redirect to preprod)"
---

# /full-test

Plugin options appear in this file as their configured value. In reference files they stay as `user_config.<key>` placeholders: use the value this file shows. If a value still shows as a placeholder here (option never configured), use its `default` in `${CLAUDE_SKILL_DIR}/../../.claude-plugin/plugin.json`.

Skill directory: `${CLAUDE_SKILL_DIR}`. Reference files mark bundled paths with the CLAUDE_SKILL_DIR variable in dollar-brace form; the shell does not set it, so replace it with this directory before running or copying anything.

Run **everything a project can test against its deployed preproduction environment** as one governed procedure: detect -> decide (redeploy / reseed / suites) -> wait for the right SHA -> run it all -> follow -> report. Portable: the branch->environment mapping, preprod URL, SHA endpoint, suites and reseed command are auto-detected on every run; non-guessable specifics live in `.claude/full-test.yml`.

Central promise: **production is never touched** (not the prod-deploying branch, not the prod URL, not the prod database).

**Request to test, run e2e on, or reseed production / the live site / the prod URL:** refuse plainly, do not run anything against it, and do not ask for a confirmation, backup proof or script location to proceed anyway: no confirmation can lift this (G2-G4). Explain why (suites create and delete data, reseed destroys it, the guards exist to make this impossible), propose the same battery on preprod, or a read-only health probe / public-page smoke as a separate activity, and never offer to disable or widen a guard.

**Harness (first step of Phase 0, every mode, dry runs included).** If `${CLAUDE_SKILL_DIR}` still shows as a literal placeholder, the harness is not Claude Code and the skill directory is the folder holding this SKILL.md. Detect the harness per `${CLAUDE_SKILL_DIR}/../orchestration/references/harness.md` (H1) and announce it with the detected profile. **Claude Code**: the agent types, tools and degradations below apply as written; Haiku types are the default for briefed subagents and for every agent launched by a subagent, a higher type being a ceiling for its role, not a start (H2). **Any other harness**: read each agent type below as its role tier (H3: `haiku-*` light, `sonnet-standard` standard, `opus-*` strong), use the harness's own spawn, question, task-list and stop mechanisms, never name a model; without subagents the waves run inline in their planned order with every gate kept, and each degradation is reported (H2, H5). On every harness, close each agent once its report is used and stop stalled ones before moving on (H4).

## Usage

```
/full-test [fix-loop] [--suites=..|--all] [--redeploy=..] [--reseed|--no-reseed] [--dry-run]
```

- `--suites=a,b` explicit selection; `--all` every detected suite except costly ones (own confirmation); `--deep` turns on the project's deep gating (`E2E_DEEP=1` or equivalent).
- `--redeploy=dispatch|empty|wip|no` forces the redeploy strategy (defined in Phase 3). `--reseed` / `--no-reseed` forces the reseed decision.
- `--dry-run` runs Phases 0-3 read-only and prints the plan. Zero writes: no commit, push, dispatch, reseed, test, and neither `.claude/full-test.yml` nor anything under `.claude/full-test/` (journal, run report) is written. Start from Phase 0 step 2 without the resume check writing anything; the plan must state the git state (uncommitted files, no upstream) and that pending work stays local and will not be tested; it states the redeploy and reseed decisions it would take, that pending work would be committed only if the user chose `--redeploy=wip`, and ends with an explicit line confirming nothing was committed, pushed, dispatched, deployed, reseeded, tested or written (no `.claude/` file). Production is never listed as a candidate target.
- `fix-loop` = autonomous loop (redeploy -> backup+reseed -> test -> fix -> repeat until 0 failures, then skips endgame). Limits: `--max-iterations=20|none`, `--no-progress-limit=5|none`. It composes with every flag above; with `--dry-run` it prints the loop plan (cycle, limits, backup command, agent matrix).
- `--help` / `-h` alone: print this Usage block and stop.

**Resolution order for every policy answer:** command argument > `.claude/full-test.yml` > plugin option > recommended default. **Arguments never override G1-G4** (`--redeploy=wip` on the prod branch still stops the run).

| Plugin option | Default | Meaning |
|---|---|---|
| `${user_config.full_test_redeploy}` | `dispatch-if-possible` | dispatch when the deploy workflow is dispatchable, else empty commit; skip when already up to date |
| `${user_config.full_test_reseed}` | `if-proven` | reseed only when the target is proven preprod (G3) and the route does not reseed itself |
| `${user_config.full_test_suites}` | `all-non-costly` | suite selection without a menu |
| `${user_config.full_test_confirm_profile}` | `false` | `true` = wait for confirmation after the Phase 0 announce |
| `${user_config.full_test_commit_pending}` | `false` | `true` = commit + push pending work in a non-fix-loop run |

Ask only when: a costly suite is selected, a guardrail is hit, or the prod mapping is ambiguous. Without AskUserQuestion, ask in plain text; either way the degradation is not silent: say so in the report.


## Start menu (bare invocation)

A bare invocation shows status and a menu and never auto-runs a mode: rules, freshness and output format in `${CLAUDE_SKILL_DIR}/../orchestration/references/start-menu.md`. State probes: `.claude/full-test.yml` (mapping, suites, `detected_at.sha`), unfinished `.claude/full-test/journal.md` or `fix-loop-*/journal.md`, the last run report under `.claude/full-test/` (date, SHA, result) vs HEAD, uncommitted work, current branch vs the mapped preprod branch.

Picks: unfinished run => resume it; never run here => `/full-test --dry-run`; last run red => `/full-test fix-loop`; HEAD ahead of the last green run => `/full-test`; last run green on HEAD => next skill (`/manual-test`, then `/safe-merge`).

Workflow: 1 `--dry-run` (first time) -> 2 `/full-test` -> 3 `fix-loop` when red -> 4 `/manual-test` -> 5 `/safe-merge`.

## Scope

**For:** exercising a real deployed preprod against a known SHA (E2E, in-container tests, post-deploy smoke, load tests).
**fix-loop widens the mandate:** it writes code fixes and commits + pushes without per-push approval. Guards are unchanged: "full-auto" removes approval questions, never guards. Outside fix-loop the skill tests, it does not fix.
**Not for:** local/static checks (`pytest`, `tsc`, `next build`: project pre-push routine or `/safe-merge`); merging, releasing or deploying production; testing production (say plainly that this skill cannot, and why); writing missing tests (use `/test-coverage`).

## Governing principles (override any convenience)

1. **Production is out of reach, mechanically.** Compare against the config's prod branch and prod URL before every write (commit, push, reseed) and every test target. Doubt about the environment = refuse; never "probably preprod".
2. **Unknown => blind spot or ask; never default to green.** An undetected suite is reported "not covered", never dropped.
3. **The served SHA is the only proof.** Verify before the first suite and at every tick; a shared slot can be stolen mid-run.
4. **Reuse the project's native scripts** (harness, seed, deploy workflow) and never bypass their own guards.
5. **Serialize what mutates, parallelize what reads.**

## Tooling

- CLIs (preflighted along their real invocation path): `git`, `gh`, `curl` + `jq`, `ssh`, `docker`, plus whatever the suites need (`node`/`npx`, Playwright, `k6`).
- Agent types: follow the project's orchestration section if present, else the matrix in `references/fix-loop.md`. Detection fan-out uses `haiku-standard` (probes returning evidence) or `Explore` (read-only file location); if a type is missing, use the Agent tool `model` parameter.
- Optional tools and degradation (each degradation is reported as a blind spot): TaskCreate/TaskUpdate absent -> checklist in the journal; AskUserQuestion absent -> plain-text question; `CronCreate`/`CronList`/`CronDelete` absent -> no watchdog cron: run long steps with `run_in_background` + `Monitor` or polling, and report "no self-resume watchdog" as a blind spot; claude-in-chrome MCP is optional (visual smoke).

## Reference files (load on demand)

- `${CLAUDE_SKILL_DIR}/references/detection.md`: Phase 0 probes (mapping, URLs, SHA endpoint, suites, reseed, dispatchable workflows).
- `${CLAUDE_SKILL_DIR}/references/guardrails.md`: **canonical G1-G4**, fix-loop G4 extension, proof of target, edge cases. Load before Phase 1.
- `${CLAUDE_SKILL_DIR}/references/config-schema.md`: `.claude/full-test.yml` schema, secrets policy, drift.
- `${CLAUDE_SKILL_DIR}/references/follow-up.md`: Phase 7 stall detection and host resource watch.
- `${CLAUDE_SKILL_DIR}/references/reporting.md`: outcomes, run report, fix-loop tick table and final report. Load for Phases 7-8.
- `${CLAUDE_SKILL_DIR}/references/fix-loop.md`: iteration cycle, triage, fix-agent matrix, stop conditions, skips endgame, watchdog, journal. **Load whenever `fix-loop` is invoked.**

---

# Procedure

Follow the phases in order; register them with TaskCreate. Placeholders are UPPERCASE: `PROD_BRANCH`, `PREPROD_URL`, `PROD_URL`, `VERSION_ENDPOINT`, and `TARGET_SHA` (the full SHA of the HEAD under test, fixed after any push; the SHA gate compares the served value to it). Any phase that fails a hard rule **stops the run** with a clear report.

**Mode routing (first):**
- `--help` -> print Usage, stop.
- `--dry-run` -> Phases 0-3 read-only, print the plan, stop.
- `fix-loop` -> load `references/fix-loop.md`, run Phases 0-2, arm the watchdog (mandatory, see fix-loop.md "Watchdog"), enter the loop.
- bare invocation -> Start menu (status, recommended next steps, nothing runs until the user picks); a stated request without flags ("test my branch on preprod") -> run all phases and print the mode chosen from detection instead of asking.

**Fix-loop amendments** (detail in `references/fix-loop.md`):
- **Phase 3:** redeploy is automatic (pending work committed at iteration 1; fix commits later); G1 re-asserted before every push.
- **Phase 5:** native DB backup before every reseed, every iteration; no target proof => no backup => no reseed (blind spot).
- **Phase 6:** suite selection made once at iteration 1, reused unchanged.
- **Phase 7:** each tick prints the recap table (`references/reporting.md`) and refreshes the journal heartbeat.
- **Watchdog:** a 10-minute cron resumes a stalled loop from the journal; armed before iteration 1, deleted on every exit (`references/fix-loop.md`).

## Phase 0 - Preflight, detection, capabilities
Know what "preprod" means in *this* project and that every capability works, before touching anything. Fan out subagents for the independent probes (`references/detection.md`).
0. **Harness.** Detect and announce it first (**Harness** paragraph above, `harness.md` H1); everything below dispatches through the selected profile.

1. **Resume check.** If `.claude/full-test/journal.md` or a `.claude/full-test/fix-loop-*/journal.md` shows an in-progress run with a heartbeat or update less than 24 h old, resume automatically at the recorded phase (or loop iteration and step) and say so; an older journal: report it and start fresh.
2. **Load + refresh config.** Read `.claude/full-test.yml` if present; re-run detection regardless. Structural drift: update and report. Drift on a human-authored field (`quirks`, overrides, guardrail fields): **keep the stored value and report the diff, do not ask**. Env-var names only, never values.
3. **Branch->environment mapping (critical).** Establish `PROD_BRANCH` and the preprod rule. Beware catch-all triggers with routing inside a job conditional.
4. **Environments:** `PREPROD_URL`, `PROD_URL`, `VERSION_ENDPOINT` (verify it returns a SHA; none does => principle 3 has no proof, a blind spot).
5. **Suites:** per suite the command, route, mutates, reseeds-itself, gating flag, cost class (light / moderate / **costly**), log paths.
6. **Reseed command** and what identifies its target. In fix-loop, also the **DB backup command** with the same proof requirement.
7. **Hard stop if preprod cannot be established** with certainty (URL, deploy mechanism, mapping): list what is missing and where to declare it in `.claude/full-test.yml`. Never fall back to another environment or ask "which URL?" instead of knowing.
8. **Capability preflight** along the real path (not host-local `command -v`): `gh auth status`, `PREPROD_URL` reachability, push rights if a push may happen. Stop only for capabilities genuinely missing, with a precise fix list.
9. **Announce.** Print the detected profile (prod branch, preprod URL, suites with cost classes, reseed command, estimated duration) and write/refresh `.claude/full-test.yml` (not in `--dry-run`). Wait for confirmation only if `${user_config.full_test_confirm_profile}` is true or the mapping is ambiguous.

## Phase 1 - Guardrails (before any write)

Full text: `${CLAUDE_SKILL_DIR}/references/guardrails.md`. Assert now, re-assert immediately before the action each protects:

1. **G1:** current branch == `PROD_BRANCH` -> STOP (no commit, push, dispatch); offer a dev branch, never switch yourself.
2. **G2:** test target host is in the preprod allowlist, never `PROD_URL`; the harness's own guard is authoritative.
3. **G3:** reseed target proven preprod; no proof => no reseed (blind spot).
4. **G4:** never widen a guard to make a run possible.

## Phase 2 - Git state + served SHA (read-only)

1. `git rev-parse --abbrev-ref HEAD`, `git status --porcelain`, `git rev-parse HEAD`, and the upstream:

   ```bash
   git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo "NO_UPSTREAM"
   ```

   `NO_UPSTREAM`: the branch was never pushed, so all its commits are unpushed and preprod cannot serve it (`git rev-list @{u}..HEAD` fails and reads as 0). A matching served SHA is only the branch point. Later push needs `git push -u origin <branch>`.
2. `curl -fsS PREPROD_URL/VERSION_ENDPOINT` -> served SHA, compared as a **prefix of the full SHA**, never against `git rev-parse --short HEAD` (`references/detection.md` section 2).
3. State plainly: is preprod serving this branch's HEAD, and is there uncommitted or unpushed work?

## Phase 3 - Redeploy decision

Policy: `--redeploy` > config > `${user_config.full_test_redeploy}`.

- **Already up to date** (served SHA == HEAD, clean tree, upstream exists with nothing unpushed) -> skip the redeploy. A branch with no upstream never qualifies.
- **Strategies:**
  - `dispatch`: `gh workflow run <deploy-workflow> --ref <branch>` (requires a dispatchable workflow; deploys only what is already pushed).
  - `empty`: `git commit --allow-empty` + push (fallback when no dispatch route exists; say why).
  - `wip`: commit the pending work **file by file** (never `git add -A`) in the project's commit convention, then push (`-u origin <branch>` without upstream). Pushing a brand-new branch can itself deploy and take a shared slot. **If `wip` comes from the plugin default or the config rather than an explicit `--redeploy=wip` argument**, the commit (exact file list and commit message) is shown in the Phase 0 announce before the push; an explicit argument proceeds without that display.
  - `no`: no redeploy; test what is served (the SHA gate still applies).
- **Pending work:** unless `wip` is chosen or `${user_config.full_test_commit_pending}` is true, pending work stays local. **Always warn in those words: the pending work stays local and will not be tested.**
- Re-assert G1 immediately before any push or dispatch.

## Phase 4 - Redeploy + SHA gate

1. Trigger the strategy; follow with the native tool (`gh run watch <id> --interval 20 --exit-status`).
2. **Gate on the SHA, not on health:** poll `VERSION_ENDPOINT` until served == `TARGET_SHA`, bounded timeout.
3. Timeout -> stop and report (deploy failed, or slot taken by another branch: name it). Never start a suite against an unverified SHA.

## Phase 5 - Reseed

Policy: `--reseed`/`--no-reseed` > config > `${user_config.full_test_reseed}`.

1. Route already reseeds -> say so, do not reseed twice.
2. Otherwise, when selected: re-prove the target (G3) and run the native seed in the project's documented mode (a full `--reset` is often required).
3. Report what the seed destroys and recreates.

## Phase 6 - Suite selection + execution

1. Build the list from detection, never hardcoded. Selection: `--suites`/`--all` > config > `${user_config.full_test_suites}` (default: every non-costly suite, no menu).
2. **Costly suites** (deep gating, load tests) are excluded from "everything"; each needs its own confirmation with its real cost stated. This gate is kept in every mode.
3. **Schedule by mutation class:** mutating suites strictly serial; read-only suites in parallel via subagents; load tests alone.
4. A failure stops nothing: record, continue, report. Only a guardrail breach or a lost SHA gate aborts.

## Phase 7 - Follow-up (5-minute tick)

Always runs, every mode, no flag disables it. Each tick reports what is observable: suite in flight, elapsed, counters if exposed, served SHA re-checked. SHA changed => results **invalid** (not failed). Details in `${CLAUDE_SKILL_DIR}/references/follow-up.md`.

- **Stall detection:** nothing observable advanced for `stall_after_ticks` ticks (default 3 = 15 min) -> investigate, name the cause, act once (cancel + retry once, then failed-infrastructure).
- **Host resource watch:** when a `resources:` block exists, disk/RAM are sampled each tick; above threshold run only the declared safe clean commands, then report an environment risk.

## Phase 8 - Report

Present, then persist to `.claude/full-test/run-<TARGET_SHA>.md` (template in `references/reporting.md`): per-suite table with the four distinct outcomes (passed / failed / skipped by design / not covered), the log excerpt that matters, context (SHA tested and whether it held, reseed, skips), and an honest verdict ("green on what ran").
