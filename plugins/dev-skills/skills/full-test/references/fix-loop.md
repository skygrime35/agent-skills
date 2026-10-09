# fix-loop mode

## Contents

- The iteration cycle
- Failure triage
- Fix orchestration
- Stop conditions
- Skips endgame
- Watchdog
- Journal & resume

The autonomous loop: redeploy → backup + reseed → test → triage → fix (orchestrated agents) → commit + push → repeat, **until zero failures**, then the skips endgame. This file is authoritative for the loop mechanics; the SKILL.md phases stay authoritative for everything they already define (detection, guardrails, SHA gate, suite scheduling, outcome classification).

Two things distinguish this mode and both are deliberate:

- **Full-auto git.** Commits and pushes happen without approval questions. This lifts *approvals*, never *guards*: G1 is re-asserted before every push and a hit stops the whole loop (`guardrails.md`).
- **The skill fixes code.** Outside fix-loop it never does. Inside, the main session is the **orchestrator** — it triages, delegates, integrates, and never fixes anything itself; subagents do the fixing.

## The iteration cycle

Each iteration `n` runs:

1. **Redeploy** — Phase 3 without the question. Iteration 1: stage pending work file by file (never `git add -A`), commit in the project's convention; if the tree is clean and everything is pushed, prefer `gh workflow run` when dispatchable, else an empty commit. Iterations ≥ 2: commit the fixes produced by the previous iteration. `git push` (with `-u origin <branch>` when there is no upstream). **G1 re-asserted immediately before the push.**
2. **SHA gate** — Phase 4 unchanged. The iteration does not start testing until the served SHA == this iteration's HEAD.
3. **Backup** — run the project's native backup command (`backup:` in the config) **before the reseed, every iteration**. The backup target needs the same class of proof as the reseed target (guardrails G3 logic): no proof ⇒ no backup ⇒ **no reseed** ⇒ blind spot, and the suites run against existing state. A backup that *fails* (command error, no space, unreachable host) also blocks the reseed — a reseed whose safety net just failed is not the same reseed. Rotate dumps per `backup.keep_last`.
4. **Reseed** — Phase 5 unchanged (skip if the execution route reseeds by itself).
5. **Run suites** — Phase 6 scheduling unchanged (mutating serial, read-only parallel, load tests alone). The selection was made at iteration 1 and is reused verbatim.
6. **Follow** — Phase 7 with the recap table every 5 minutes (template in `references/reporting.md`). The served SHA is re-checked each tick; a stolen slot marks results **invalid**, and an invalid iteration is **re-run, not counted** — not as progress, not as no-progress, not against `max_iterations`… except when the slot is stolen repeatedly (see stop conditions). The host resource watch (`follow-up.md`) runs at each tick too — a threshold breach that the safe clean commands cannot resolve marks subsequent failures candidate-infrastructure, and a full disk on the loop's host is an environment incident, not a fix target.
7. **Triage** every failure (below). Zero failures → skips endgame. Otherwise:
8. **Fix** via orchestrated agents (below), **validate locally**, then loop to step 1.

Journal every step (see "Journal & resume") — including the **heartbeat** the watchdog reads (see "Watchdog"). The watchdog is armed before step 1 of iteration 1 and disarmed only on the loop's final exit.

## Failure triage — before any fix

No agent is spawned until every failure is classified. Misclassification is the expensive mistake: fixing product code for an infra hiccup wastes an iteration; retrying a real bug hides it.

| Class | Evidence | Action |
|---|---|---|
| **Slowness / flaky / infra** | timeout-shaped failure, passes on re-run, network blips, 502s during suite | Re-run the failed suite (or the failed tests, if the harness can target them) **once** before classifying (`fix_loop.retry_failed_once`). If it passes on retry, or the failure is timing-shaped: **harden the test** — see below. |
| **Product bug** | reproducible, assertion about behaviour, consistent across retry | Fix the **code**, never the test. |
| **Test bug** | wrong assertion, dead selector, stale fixture, test assumes state the reseed doesn't create | Fix the **test**. |
| **Needs human info/action** | missing credential, third-party account, DNS, a business decision | Do **not** attempt. Move to the "needs-user" basket, handled in the skips endgame. It leaves the failure count for loop purposes but is reported honestly, never as passed. |

**Hardening against slowness is a first-class fix, not a cop-out.** The user's preprods are slower and less stable than prod, and the contract is: *when slowness is the only problem, the tests must still eventually pass.* Legitimate hardening: generous timeouts sized to observed preprod latency, polling waits instead of fixed sleeps, harness-level retry annotations on network-dependent steps, explicit readiness checks before assertions. The test still asserts the same behaviour — it just waits like a patient human instead of a stopwatch.

**Absolute prohibition:** the G4 extension for fix agents in `guardrails.md` applies verbatim. A test that cannot pass without X goes to the needs-user basket; the orchestrator checks each agent diff before committing.

## Fix orchestration

The main session is the orchestrator. For each triaged, fixable failure group (group failures that share one root cause — five symptoms of one cause get **one** agent):

1. **Classify difficulty** → pick the agent type from the matrix (config `fix_loop.agents`, defaults below). Follow the project's orchestration section (in its base doc) first; use the matrix below as the fallback. Use the agent types the Agent tool offers; when a mapped type is not offered, fall back to the Agent tool's `model` parameter with equivalent effort stated in the prompt.

   | Difficulty | Looks like | Default agent type |
   |---|---|---|
   | **trivial** | one known file, mechanical (dead selector, timeout constant, typo) | `haiku-quick` (purely mechanical) or `haiku-standard` |
   | **standard** | localized bug, cause identified by the logs, ≤ a few files | `sonnet-standard` |
   | **complex** | cause needs investigation, multi-file, race conditions, state drift | `opus-standard` |
   | **critical** | architectural, cross-cutting, data-integrity | `opus-standard`; `opus-deep` only on explicit user request or after `opus-standard` failed on the same failure |

   A failure whose fix already failed once escalates one row on the next iteration.

2. **Brief each agent** with: the log excerpt that matters (not the whole log), artifact paths, the exact repro command, the triage class ("this is a product bug — fix the code, not the test" / "harden this test against slowness — same assertions, patient waits"), the G4 extension verbatim, and a bounded scope (the files/modules it may touch). Agents fix **locally only**: no commit, no push, no deploy, no reseed, and on the shared working tree **never** `git stash`, `git add -A`, `git checkout` or `git reset`; the orchestrator owns git and the environment.
3. **Parallelize to the maximum that stays safe.** Independent fixes (disjoint files/modules) launch in **one message, multiple Agent calls**. Fixes that touch the same files: serialize, or isolate in worktrees and let the orchestrator merge. When unsure whether two fixes collide, assume they do — a merge conflict mid-loop costs more than a serialized agent.
4. **Integrate**: read each agent's diff, check it against the G4 extension (no deleted/skipped tests, no weakened assertions), then run the project's fast **local checks** (`fix_loop.local_checks`: lint + the unit tests touched) so the loop never burns a full deploy wait on a syntax error. A local-check failure goes back to the same agent once; twice → escalate difficulty.
5. **Commit** — one commit per iteration, message in the project's convention listing the fixes. Then loop.

## Stop conditions

Compute the **failure signature** after each iteration: the sorted set of `(suite id, test id)` pairs that failed (invalid results excluded). Persist it in the journal.

- **Success** — zero failures (by-design skips and needs-user items do not count as failures) → skips endgame.
- **No progress** — the signature is *identical* for `no_progress_limit` **consecutive** iterations (default **5**; any change in the set — one fixed, one new — resets the counter) → stop, report, ask the user: continue as-is, change approach, or abandon those failures to the needs-user basket.
- **Iteration cap** — `max_iterations` total iterations (default **20**, invalid re-runs not counted) → stop, report, same question.
- Each limit is independently configurable via flag or config, including `none`. Both `none` = unbounded loop — legitimate, but only as the user's explicit choice; say what that means when it starts.
- **Immediate abort**, regardless of limits: any guardrail hit (G1 on a push, G2 on a target, unproven reseed attempted), the shared slot stolen on **3 consecutive** attempts of the same iteration (someone is actively using the preprod — stop fighting them, report whose branch holds it), or the preprod unreachable across a full tick cycle.

## Skips endgame

Runs once the loop reaches zero failures (or the user chose to proceed after a limit stop):

1. **Enumerate** every by-design skip and every needs-user item, **grouped by missing prerequisite** (one missing credential often gates a dozen tests — that is one question, not twelve).
2. **Interview in one salvo** — AskUserQuestion / grouped questions, everything collectable at once, stating per group: what is missing, which tests it unlocks, and what the user must do or provide. Secrets policy holds: env-var **names** and where to put values, never values in config or journal.
3. **Apply** what came back: config updates, gating flags, env-var names, user-performed actions confirmed.
4. **Relaunch a fix-loop targeted at the newly un-gated tests** (restrict `--suites`/gating to what changed — no need to re-run the whole battery that just passed). Fresh limits apply. Un-gated tests that now *fail* are just failures: triage, fix, loop.
5. **What remains without info stays skipped** — documented in the final report with the question that was asked and the answer that is still missing. Iterate the endgame as long as the user brings new information; the report never upgrades an unanswered skip to anything else.

## Watchdog — the loop must never silently stop

The fix-loop's failure mode in practice is not a wrong fix, it is **stopping without saying so**: a turn that ends on a question nobody answers, a subagent that dies, a tick that never comes back, a step that waits forever. A loop that stops is not autonomous. So every fix-loop runs under a **watchdog**: a session cron (the same mechanism as `/loop`) that fires **every 10 minutes**, compares the journal to what it saw last time, and **resumes the loop itself** when it has stalled. Start it **before iteration 1**, delete it at the very end — it is part of the loop, not an option.

**Start (mandatory, right after Phases 0–2, before the loop's first step).** Without `CronCreate`/`CronList`/`CronDelete`, skip the cron: run every long step with `run_in_background` + `Monitor` or polling, keep the heartbeat, and report "no self-resume watchdog" as a blind spot in the final report.

1. Write the heartbeat block into `journal.md` (see "Journal & resume"): `heartbeat_at` (ISO timestamp), `iteration`, `step` (1–8 from the cycle), `step_detail` (a short observable: the suite running, the agent count spawned, the SHA being gated…), `watchdog_status: running`.
2. Call `CronCreate` with `cron: "*/10 * * * *"` (`watchdog.interval_minutes` in config), `recurring: true`, and this prompt — with `<DIR>` substituted by the loop directory and `${CLAUDE_SKILL_DIR}` by this skill's absolute directory (the cron session does not expand it):

   > /full-test fix-loop watchdog (journal: `<DIR>/journal.md`). Read the journal and its `watchdog` section. Compare `heartbeat_at`, `iteration`, `step`, `step_detail` with the previous tick recorded in `watchdog.last_seen`. If `watchdog_status` is `finished` or `aborted`: delete this cron (CronDelete with the id stored in the journal) and stop. If something advanced: record the new state in `watchdog.last_seen`, print one line `watchdog: OK - iteration N, step S, <detail>` and stop. If **nothing** advanced for `watchdog.stall_after_cron_ticks` consecutive ticks: the loop is presumed stalled. Apply the "Stall response" procedure in `${CLAUDE_SKILL_DIR}/references/fix-loop.md` (resume at the recorded iteration and step, never restart from zero, never bypass G1-G4), increment `watchdog.resumes`, and journal what you did.

3. Record the returned job id in `journal.md` (`watchdog.cron_id`) so a resumed session can find and delete it, and tell the user once: *"watchdog armed: every 10 min, auto-resume on stall, expires after 7 days"* (CronCreate's hard cap — a loop that outlives it must re-arm on resume).

**Heartbeat (every step, every iteration).** Each of the 8 cycle steps, on entry and on exit, updates `heartbeat_at` / `step` / `step_detail`. Each 5-minute Phase 7 tick updates `heartbeat_at` too. A step that cannot leave a heartbeat behind is a step that will look stalled — so it must.

**Keep the REPL free.** The cron only fires while the session is **idle** (between turns). A foreground command that waits forever therefore hides the stall from the watchdog. Hard rules inside fix-loop: every foreground `Bash` gets an explicit `timeout` (never the default when the command can wait on the network); anything expected to run longer than ~2 minutes (a suite, a dispatch wait, a SHA gate) runs with `run_in_background` or via `Monitor`, and the loop *returns* to wait for the notification rather than sleeping in the foreground; **never** end a turn on an open question in fix-loop unless it is the skips endgame (a question is a legitimate stop only there — otherwise decide, journal the decision, continue).

**Stall response** (what the watchdog does when `stall_after_cron_ticks` ticks — default **2** = 20 min — saw no change):

1. **Diagnose from the journal first**: which step, since when, what was the last observable. Read the last `iteration-<n>.md` and the tick table.
2. **Is it actually alive?** A suite step (5–6): check the native progress source (CI run status, log tail) — a suite that is slow but observably moving is not a stall; update the heartbeat and stand down. A fix step (8): check the spawned agents (running / done / dead). A deploy or gate step (1–2): re-check the served SHA and the push.
3. **Resume at the recorded iteration and step**, exactly as the Phase 0 resume path would: a gated deploy is not redone, committed fixes are not re-spawned, a finished suite is not re-run. Dead agents are re-spawned **once** with the same brief; a hung CI run is cancelled and retried **once** (Phase 7 rule); an unanswered internal question is answered by the loop's own defaults and journaled.
4. **Bounded**: `watchdog.max_resumes` (default **5**) total resumes per loop. Beyond it, or if the same step stalls on 3 consecutive resumes, set `watchdog_status: aborted`, write the final report with the stall as an infrastructure/blind-spot finding, delete the cron, and tell the user — a loop that cannot make progress with help is a loop that needs a human, and saying so is the autonomous behaviour.
5. **Guardrails are untouched**: the watchdog is the loop resuming itself, with the loop's mandate — G1–G4 apply exactly as before. It never pushes something the loop would not have pushed, never touches prod, never reseeds without proof.

**Stop (mandatory, in every exit path — success, stop condition, immediate abort, user abandon):** set `watchdog_status: finished|aborted` in the journal **then** `CronDelete(watchdog.cron_id)`. On a resumed loop (Phase 0), re-arm the watchdog if `CronList` no longer shows it (a new session has no crons) and store the new id.

## Journal & resume

Everything lives under `.claude/full-test/fix-loop-<YYYY-MM-DD-HHMM>/`:

- `journal.md` — loop state: current iteration, phase within the cycle, suite selection, failure signatures per iteration, limits and their counters, backup paths, commit SHAs pushed, and the **`watchdog` block**: `heartbeat_at`, `step`, `step_detail`, `watchdog_status` (`running|finished|aborted`), `cron_id`, `last_seen` (what the last tick observed), `resumes`, `stall_after_cron_ticks`, `max_resumes`.
- `iteration-<n>.md` — per-iteration report (template in `references/reporting.md`).
- `report.md` — the final loop report.

The Phase 0 resume check recognizes an in-progress fix-loop journal and offers to resume at the recorded iteration and step — a deploy already gated does not redeploy; fixes already committed are not re-spawned. Register the loop with TaskCreate/TaskUpdate (one task per iteration cycle step is too fine; one per iteration is right) so a long loop stays visible.
