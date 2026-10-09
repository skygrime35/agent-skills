---
name: full-test
argument-hint: "[fix-loop] [--suites=a,b|--all] [--deep] [--redeploy=dispatch|empty|wip|no] [--reseed|--no-reseed] [--dry-run] [--max-iterations=N] [--no-progress-limit=N] [--help]"
description: "Use to run a project's full battery of tests against its PREPRODUCTION environment — especially to validate a branch end-to-end before promoting it. One governed run: detect the branch→environment mapping and every preprod-targeting suite, decide whether to redeploy, optionally reseed the preprod database, wait until the deployed SHA matches the branch under test, run every selected suite, poll progress every 5 minutes, and report per-suite results with explicit blind spots. Also runs as an autonomous fix loop (/full-test fix-loop): redeploy → backup+reseed → test → triage → fix via orchestrated subagents → commit+push → repeat until 0 failures, then interview the human to unlock remaining skips. Production is mechanically out of reach: never pushes the prod-deploying branch, never tests the prod URL, never reseeds the prod database. Supports --dry-run (detect and plan only). Portable via auto-detection + a .claude/full-test.yml config; unknowns become explicit blind spots, never a green check."
---

# /full-test

Run **everything a project can test against its deployed preproduction environment**, as one governed procedure instead of a remembered ritual: detect → decide (redeploy / reseed / suites) → wait for the right SHA → run it all → follow along → report.

This skill is **portable across any project**. It auto-detects the branch→environment mapping, the preprod URL, the SHA-serving endpoint, every preprod-targeting test suite and the reseed command on every run, and remembers the non-guessable specifics in a per-project `.claude/full-test.yml`.

Its central promise is a negative one: **production is never touched.** Not the prod-deploying branch, not the prod URL, not the prod database.

## Usage

```
/full-test                       # interactive run: detect → questions → (redeploy) → (reseed) → test → follow → report
/full-test --suites=e2e,smoke    # explicit selection; skip the menu question
/full-test --all                 # every detected suite except the ones marked costly (those get their own confirmation)
/full-test --deep                # turn on the project's "deep" gating (E2E_DEEP=1 or equivalent)
/full-test --redeploy=dispatch|empty|wip|no   # force the redeploy strategy instead of asking
/full-test --reseed | --no-reseed             # force the reseed decision instead of asking
/full-test --dry-run             # detect and print the execution plan. Zero writes, pushes, reseeds or tests
/full-test --help                # print this Usage block and stop

/full-test fix-loop              # autonomous loop: redeploy → backup+reseed → test → fix (agents) → repeat until 0 failures, then handle skips
/full-test fix-loop --max-iterations=20|none      # total iteration cap (default 20)
/full-test fix-loop --no-progress-limit=5|none    # stop when the same failures persist N consecutive iterations (default 5)
```

`fix-loop` composes with `--suites`, `--all`, `--deep`, `--reseed`/`--no-reseed`, and `--dry-run` (which prints the loop plan — iteration cycle, limits, agent matrix — and executes nothing).

If invoked with `--help`/`-h` and nothing else, print the Usage block above verbatim and stop.

Arguments override questions; anything not passed as an argument is asked interactively. An argument never overrides a **guardrail** — `--redeploy=wip` on the prod branch still stops the run.

## What this skill is for / non-goals

**For:** exercising a real, deployed preprod against a known SHA — E2E suites, tests that run inside the preprod containers, post-deploy smoke checks, load tests: whatever the project actually ships.

**In `fix-loop` mode the mandate widens:** the skill also *writes code fixes* and *commits + pushes autonomously* (no per-push approval), looping redeploy→test→fix until zero failures. This wider mandate exists **only** inside fix-loop, and it never touches the guardrails: G1–G4 remain absolute — full-auto means "no approval questions", never "no guards". Outside fix-loop, nothing changes: the skill tests, it does not fix.

**Not for:** local/static checks that don't need a deployed environment (`pytest`, `mypy`, `ruff`, `tsc`, `next build`) — those belong to the project's pre-push routine or to `/safe-merge`. **Not for** merging, releasing, or deploying production. **Not for** testing production: if that is what the user wants, say plainly that this skill cannot do it and why.

## Five governing principles (these override any convenience)

1. **Production is out of reach, mechanically.** The prod-deploying branch and the prod URL live in the config; compare against them before *every* write (commit, push, reseed) and *every* test target. **Doubt about which environment you are addressing = refuse.** Never "probably preprod". This is the whole point of the skill.
2. **Unknown ⇒ explicit blind spot / ask the human — NEVER default to "green".** An undetected suite is reported as "not covered — blind spot", never silently dropped. A preprod that can't be identified stops the run rather than guessing a target.
3. **The served SHA is the only proof.** You never test "preprod", you test a specific SHA. Verify it before the first suite and re-verify at every follow-up tick — a shared preprod slot can be stolen mid-run, which invalidates results.
4. **Reuse the project's native scripts** (test harness, seed command, deploy workflow, load-test wrapper). Never reimplement them, and **never bypass their own guardrails** — a harness that refuses a URL is protecting the user, not obstructing you.
5. **Serialize what mutates, parallelize what reads.** On a single shared preprod slot, two mutating suites running at once corrupt each other's data. Fan out subagents (Agent tool) for independent read-only suites; keep mutating suites single-file.

## Tooling

**External CLIs** (Phase 0 preflight tests each along its real invocation path): `git`, `gh` (`gh workflow run`, `gh run list/view/watch`), `curl` + `jq`, `ssh`, `docker`/`docker compose`, `node`/`npx`, `python` + Playwright, `k6` (usually via `docker run`).

**Project-native scripts** (auto-detected, reused, never reimplemented): the E2E harness entrypoint, the DB seed/reset command, the deploy workflow, smoke/observability scripts, the load-test wrapper.

**Claude Code capabilities:** **TaskCreate/TaskUpdate** to register the phases so a long run stays visible and resumable; the **Agent tool** to fan out independent read-only suites and detection probes; **claude-in-chrome MCP** for an optional visual smoke of preprod pages.

## Reference files (load on demand)

- `references/detection.md` — how to establish the branch→environment mapping across CI platforms, find the preprod URL and the SHA-serving endpoint, enumerate preprod-targeting suites, find the reseed command, and tell dispatchable workflows from branch-gated ones.
- `references/guardrails.md` — the anti-production rules, how to *prove* a target is preprod, and the edge cases (shared slot, ambiguous mapping, prod-shaped URLs, seeds guarded only by a password).
- `references/config-schema.md` — the `.claude/full-test.yml` schema, secrets policy, committed/local split, drift handling.
- `references/reporting.md` — the run-report template, how to classify pass / fail / by-design skip / blind spot, the fix-loop tick table and the loop final report.
- `references/fix-loop.md` — the fix-loop mode: iteration cycle, failure triage, fix-agent orchestration (difficulty→model×effort matrix, parallelization), stop conditions, the skips endgame, loop journal/resume. **Load whenever `fix-loop` is invoked.**

---

# Procedure

Follow the phases in order. Register them with `TaskCreate` at the start so progress is visible and the run is resumable. Placeholders are UPPERCASE (`PROD_BRANCH`, `PREPROD_URL`, `PROD_URL`, `VERSION_ENDPOINT`, `TARGET_SHA`). Any phase that fails a hard rule **stops the run** with a clear report; nothing downstream runs.

**Mode routing (do this first):**
- `--help` → print Usage, stop.
- `--dry-run` → run **Phases 0 → 3** in read-only form (ask nothing that would mutate; present the decisions you *would* take), print the execution plan, stop. **No** commit, push, dispatch, reseed, or test. With `fix-loop`, also print the loop plan (iteration cycle, limits, backup command, agent matrix) — still zero writes.
- `fix-loop` → load `references/fix-loop.md`, run Phases 0–2 as written, **arm the watchdog** (a 10-minute session cron via `CronCreate` that reads the loop journal and resumes the loop when it stalls — mandatory, see fix-loop.md "Watchdog"), then enter the loop it describes. The phase amendments below apply on every iteration.
- default → run all phases.

**Phase amendments in fix-loop mode** (the detail lives in `references/fix-loop.md`; the phases below stay authoritative for everything not amended):
- **Phase 3** — the redeploy is no longer a question: commit + push automatically (pending work is included at iteration 1; empty commit when there is nothing to push; fix commits on later iterations). G1 is re-asserted before **every** push.
- **Phase 5** — **backup the preprod database before every reseed, on every iteration**, using the project's native backup command (`backup:` in the config). The backup target needs the same class of proof as the reseed target; no proof ⇒ no backup ⇒ no reseed, reported as a blind spot.
- **Phase 6** — the suite selection is asked **once**, at iteration 1; later iterations reuse it unchanged so results stay comparable across the loop.
- **Phase 7** — each 5-minute tick prints the fix-loop recap table (iteration, totals, done, pass/fail, skips, elapsed, ETA, served SHA — template in `references/reporting.md`) and refreshes the journal heartbeat.
- **Watchdog (all phases)** — the loop runs under a 10-minute `CronCreate` watchdog armed before iteration 1 and deleted on every exit path. It reads `journal.md`'s heartbeat (`iteration`, `step`, `step_detail`, `heartbeat_at`); if nothing advanced for `watchdog.stall_after_ticks` ticks (default 2 = 20 min) it resumes the loop at the recorded iteration and step, bounded by `watchdog.max_resumes` (default 5), guardrails unchanged. Because the cron only fires while the session is idle, fix-loop never blocks the REPL: every foreground command has a `timeout`, long waits go through `run_in_background`/`Monitor`, and no turn ends on a question outside the skips endgame.

## Phase 0 — Preflight, detection, capabilities

Goal: know exactly what "preprod" means in *this* project, and that every capability you'll need actually works — before touching anything. Fan out subagents for the independent detection probes (see `references/detection.md`).

1. **Resume check.** If `.claude/full-test/journal.md` shows an in-progress run — or a `.claude/full-test/fix-loop-*/journal.md` shows an in-progress loop — read it and **offer to resume** at the last completed phase (or the loop's recorded iteration and step) rather than blindly restarting (a redeploy already done should not be redone).
2. **Load + refresh config.** Read `.claude/full-test.yml` if present. **Re-run detection regardless** — config goes stale. On drift between detected and stored values, report it; if the drift touches a human-authored `quirks`/override field, **show the diff and ask before overwriting**. Enforce the secrets policy: env-var **names** only, never values.
3. **Detect the branch→environment mapping — the critical one.** Which branch (or tag) deploys **production**, which deploys **preprod**, and by what mechanism. Beware catch-all triggers (`branches: ["**"]`) where the routing lives in a conditional inside the job, not in the trigger. Establish `PROD_BRANCH` and the preprod rule.
4. **Detect the environments:** `PREPROD_URL`, `PROD_URL`, and `VERSION_ENDPOINT` — the endpoint that exposes the *running SHA*. Verify it actually returns a SHA (some `/version` endpoints deliberately withhold it without auth); if none does, that's a blind spot that costs you principle 3 — say so.
5. **Enumerate every preprod-targeting suite** and, for each: the exact command, the execution route (dispatchable workflow vs local), whether it **mutates** preprod data, whether it **reseeds by itself**, its gating flag (`E2E_DEEP=1` or equivalent), its cost class (light / moderate / **costly**), and where it writes logs/artifacts.
6. **Detect the reseed command** and, crucially, **what identifies its target** (host, compose project, database name, email domain scope). In fix-loop mode, also detect the **DB backup command** (`pg_dump`/`mysqldump` wrapper, a `make backup` target, an ops script) with the same target-proof requirement — fix-loop refuses to reseed without a fresh backup.
7. **Hard stop if preprod can't be established.** If `PREPROD_URL`, the deploy mechanism, or the branch→env mapping can't be determined **with certainty**, stop and list precisely what is missing and where to declare it in `.claude/full-test.yml`. Do **not** fall back to another environment, do **not** ask "which URL should I test?" as a substitute for knowing — the human filling in the config is the fix.
8. **Capability preflight.** Test each capability **the way the project actually invokes it**, not with a naive host-local `command -v`: if the seed only ever runs as `ssh HOST 'docker compose … exec backend …'`, test *that*, and a host-local absence of `psql`/`docker` is irrelevant. Check `gh auth status`, `PREPROD_URL` reachability, push rights if a push may happen. Stop only for capabilities genuinely missing along the real path — with a precise fix list. Don't false-flag.
9. **Announce + confirm.** Present the detected profile (prod branch, preprod URL, suites found with cost classes, reseed command) and an estimated run time. Write/refresh `.claude/full-test.yml`.

## Phase 1 — Guardrails (before any write)

Assert all of these now, and re-assert each one immediately before the action it protects. See `references/guardrails.md`.

1. **Current branch == `PROD_BRANCH` → STOP.** No commit, no push, no dispatch. Explain that pushing here would deploy production. **Offer** to move to a development branch; do not do it yourself — a test skill does not rearrange the user's branches. This holds even under `--redeploy=wip`.
2. **Test target ∈ the preprod whitelist, never `PROD_URL`.** Compare the resolved host, not a substring. If the harness has its own target guard, that guard is authoritative — **never work around it**; if it refuses your URL, the URL is wrong, not the guard.
3. **Reseed target must be *proven* preprod** — by host, compose project, database name, or the seed's own scoping — before the command runs. A guard that a password alone can lift is not proof. **No proof ⇒ no reseed**, reported as a blind spot rather than attempted.
4. **Never widen an existing guard** to make a run possible (adding a URL to a whitelist, exporting a password to lift a fail-closed check, passing `--prod`). If a run needs that, it is the wrong run.

## Phase 2 — Git state + served SHA (read-only)

1. `git rev-parse --abbrev-ref HEAD`, `git status --porcelain` (pending work), `git rev-parse HEAD`, and the upstream — **resolved before you use it**:

   ```bash
   git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo "NO_UPSTREAM"
   ```

   **Handle `NO_UPSTREAM` explicitly — it is a trap, not an edge case.** `git rev-list --count @{u}..HEAD` *fails* on a branch with no upstream and hands back an empty string, which reads as `0` — i.e. "nothing unpushed", the exact opposite of the truth. A branch with no upstream has **never been pushed**: all of its commits are unpushed, and the preprod cannot possibly be serving it (any matching SHA is a coincidence of the branch point, not evidence your work is deployed). Say so plainly, and remember that pushing it later needs `git push -u origin <branch>`.
2. `curl -fsS PREPROD_URL/VERSION_ENDPOINT` → the served SHA. **Compare it as a prefix of the full SHA** (`served == full[:len(served)]`), never against `git rev-parse --short HEAD` — short-SHA length is not stable across clones, and the mismatch lies convincingly. See `references/detection.md` §2.
3. Conclude and state plainly: **is preprod already serving this branch's HEAD, and is there uncommitted or unpushed work?**

## Phase 3 — Redeploy decision

- **Already up to date** (served SHA == HEAD **and** clean tree **and** an upstream exists with nothing unpushed) → say so and **propose skipping the redeploy** — it saves the whole deploy wait. Default to skipping if the user just confirms. **A branch with no upstream never qualifies**, even when the served SHA matches: that match means the branch still points at its (already deployed) branch point, not that your branch is deployed. Skipping there would test the wrong code and call it green.
- **Otherwise, ask whether to redeploy.** If yes and there is pending work, present the choice honestly:
  - **Commit + push the pending work** → it gets deployed and tested. Stage **file by file** (never `git add -A`), write a message in the project's commit convention, show it for approval before pushing. No upstream → `git push -u origin <branch>`; note that on a project where every non-prod branch deploys preprod, **pushing a brand-new branch triggers a deploy by itself** and can take the shared slot from whoever holds it.
  - **Redeploy what is already pushed** → the pending work stays local and **will not be tested**. Say this in those words; it is the trap this question exists to prevent.
- **How to redeploy without new code:** prefer **`gh workflow run <deploy-workflow> --ref <branch>`** when the deploy workflow is dispatchable — it keeps history clean. Fall back to an empty commit (`git commit --allow-empty`) only when no dispatch route exists, and say why.
- Re-assert guardrail 1 immediately before any push or dispatch.

## Phase 4 — Redeploy + SHA gate

1. Trigger the chosen strategy; follow the run with the project's native tool (`gh run watch <id> --interval 20 --exit-status`).
2. **Gate on the SHA, not on health.** Poll `VERSION_ENDPOINT` until the served SHA == `TARGET_SHA`, with a bounded timeout. A healthy preprod serving *someone else's* commit is a failure, not a pass.
3. Timeout → **stop and report explicitly**: deploy failed, or the shared preprod slot was taken by another branch (name it if the CI shows it). Never start a suite against an unverified SHA.

## Phase 5 — Reseed (optional)

1. If the chosen execution route **already reseeds** (many E2E workflows do), say so and **do not reseed twice**.
2. Otherwise ask, then re-prove the target (guardrail 3) and run the project's native seed command. Prefer the project's documented mode (a full `--reset` is often required rather than an idempotent seed — accumulated state drifts and causes false failures).
3. Report what the seed destroys and recreates, so the user knows what state the suites will find.

## Phase 6 — Suite menu + execution

1. **Build the menu from detection**, never from a hardcoded list. Offer multi-select plus an "everything" entry. Mark **costly** suites (deep/expensive gating, load tests) — they are **excluded from "everything"** and each require their own confirmation, with their real cost stated (shared VPS, real transcodes, minutes of load).
2. **Schedule by mutation class:** mutating suites strictly serial; read-only suites in parallel via subagents; **load tests alone** (concurrent traffic invalidates their numbers, and they invalidate everyone else's).
3. **A failure stops nothing.** Record it, keep going, report at the end (Phase 8). Only a guardrail breach or a lost SHA gate aborts the run.

## Phase 7 — Follow-up (5-minute tick)

**This phase always runs — every mode, every option combination.** No flag reduces or disables it: any run that launches at least one suite is followed on a 5-minute tick until every suite finishes. Waiting silently on a command and hoping it returns is not following.

At each tick, report: the suite in flight, elapsed time, current pass/fail/skip counters if the harness exposes them, and **the served SHA re-checked**. If the SHA changed mid-run, the slot was stolen: mark the affected results **invalid** (not "failed"), say which suites are compromised, and offer to re-run once the slot is back.

**Stall detection (default behavior).** The tick is a watchdog, not just a progress report. Record what each tick observed (counter values, the CI job's current step, log tail offset, run status). If **nothing observable has advanced for `stall_after_ticks` consecutive ticks** (default 3 = 15 min) — same counters, same step, log not growing — the suite is presumed **stalled**, and waiting longer is not the response:

1. **Investigate** via the native sources: `gh run view <id> --json status,jobs` (job hung? runner lost? queued behind another run?), the harness log tail (last line and its age), preprod reachability + served SHA (environment down or redeployed?).
2. **Name the cause** if visible (hung job, lost runner, dead preprod, deploy queue) and report it at the tick instead of another identical row.
3. **Act once, bounded**: a run the CI itself marked as hung/lost → cancel and retry it **once**; a dead preprod → this is an environment incident, stop the affected suite and report. If the retry stalls again, classify the suite **failed (infrastructure)** with the evidence — never leave the run hanging indefinitely and never report a stalled suite as still "running" past the threshold.
4. **Calibrate before flagging**: a suite whose config `typical_duration` is long and whose harness exposes no counters is not "stalled" just because it is quiet — for those, the threshold applies to the *sources* (log growth, job step changes), and if genuinely nothing is observable, say so once at the start and fall back to `typical_duration` + margin as the stall deadline.

In fix-loop mode, a suite that ends **failed (infrastructure)** after a stall is triaged as infra (see `references/fix-loop.md`) — it is not a product bug and spawns no fix agent; if the same suite stalls on consecutive iterations, that is a no-progress signal, not something to fix in code.

**Host resource watch (when the environment or the suites run on a reachable host).** A preprod that runs out of disk or RAM mid-suite produces failures that look like product bugs and can freeze the whole VPS. When the config declares a `resources:` block — or when detection establishes that the tests, the runner, or the preprod stack share the local machine — each tick also samples disk and RAM usage on that host. Above the thresholds (`resources.disk_max_pct`, default 85; `resources.ram_max_pct`, default 90):

1. Run the project's declared **safe clean commands** (`resources.clean` — declared per project because "safe" is project-specific: on a shared VPS, global docker prunes are typically forbidden while `docker builder prune -af` is fine). Never improvise a cleanup beyond that list.
2. Re-sample. Still above threshold → report it at the tick as an **environment risk** (with the numbers), and treat any suite failure that follows as candidate-infrastructure, not product, until resources recover.
3. Never let a cleanup touch test artifacts of the run in flight, DB backups within their `keep_last` rotation, or anything the project's guardrails protect.

Prefer the project's native progress source (`gh run view <id> --json status,jobs`, the harness log tail). Do not invent progress you can't observe.

## Phase 8 — Report

Present, then persist to `.claude/full-test/run-<TARGET_SHA>.md` (template in `references/reporting.md`):

- **Per-suite table:** passed / **failed** / skipped-by-design / **not covered (blind spot)** — these are four distinct outcomes and must never be collapsed. By-design skips (a gating flag off, a feature killswitch off) are **not** failures; say so, with the count and the reason, or they read as rot.
- **Failures:** the log excerpt that matters, not the whole log, plus artifact paths.
- **Context:** the SHA tested, whether it held throughout, what was reseeded, what was skipped and why.
- **Verdict** — explicit, and honest about what was *not* covered. A run where three suites were declined is not "green"; it is "green on what ran".
