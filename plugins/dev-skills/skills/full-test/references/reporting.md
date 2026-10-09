# Reporting

How to classify outcomes and what to write. The report is the deliverable — a run whose results are misread was a wasted run.

## The four outcomes (never collapse them)

| Outcome | Meaning | What the user should do |
|---|---|---|
| **Passed** | ran to completion, green | nothing |
| **Failed** | ran, and something is wrong | investigate — this is the signal |
| **Skipped by design** | the harness deliberately declined: a gating flag is off, a feature killswitch is off, the environment can't support it | **nothing** — this is normal |
| **Not covered (blind spot)** | no suite exists, or it couldn't run: missing capability, declined by the user, unproven target | decide whether the gap matters |

Collapsing these is the classic reporting failure, and each collapse has a specific cost:

- **Skip reported as failure** → the user hunts a bug that doesn't exist. Some suites skip *dozens* of steps by design; report the count **with its reason** ("~53 skipped: deep gating off + feature killswitches off — by design") or a healthy run reads as rot.
- **Blind spot reported as pass** → the user believes something was verified that never ran. This is the one that gets people hurt, and it's why a declined suite is never simply omitted.
- **Blind spot reported as failure** → infrastructure noise drowns the real signal.
- **Invalid reported as failure** → see below.

**Invalid** is a fifth state, and it is not a failure: if the served SHA changed mid-run (a stolen shared slot), the suite tested *someone else's code*. You learned nothing. Say "invalid — the slot was taken by `<branch>` at tick 3", never "failed".

## Stating the verdict

Be honest about scope. A run where three suites were declined is **not green** — it is "green on what ran". Write the verdict so that sentence is impossible to misread:

> **Verdict: green on what ran.** 4 suites passed, 0 failed, ~53 steps skipped by design. **Not covered:** deep E2E (declined — costly), load tests (declined). The deep suite is the one that exercises real transcoding, so the transcode path is unverified by this run.

Name what the blind spot *means*, not just that it exists. "Load tests not covered" is a fact; "no evidence about behaviour under concurrent load" is the information.

## Failures

Include **the log excerpt that matters**, not the log. Aim for the assertion and its immediate context, plus the artifact path for anyone who wants the rest. If several failures share one cause (an expired fixture version, an environment flag), say so once and group them — five symptoms of one cause reported as five failures is five times the work for the reader.

## Run report template

Persist to `.claude/full-test/run-<TARGET_SHA>.md`:

```markdown
# /full-test — run on <SHA> (<branch>)

**Verdict:** <green on what ran | failures found | invalid — slot stolen>

## Context
- SHA tested: `<sha>` — held throughout? <yes | no: taken by `<branch>` at <tick>>
- Preprod: <url> · redeploy: <dispatch | empty commit | push of pending work | skipped, already up to date>
- Pending work: <none | committed and pushed: <sha> | left local and NOT tested>
- Reseed: <done via <route> | already done by <suite> | declined | not proven → skipped>

## Suites

| Suite | Outcome | Detail |
|---|---|---|
| e2e-python | passed | 112 steps, 53 skipped by design (deep off + killswitches off) |
| smoke-seo | passed | |
| e2e-python-deep | not covered | declined (costly) — real transcode path unverified |
| load-k6 | not covered | declined |

## Failures
<per failure: suite, step, the excerpt that matters, artifact path>

## Blind spots
<what this run did NOT tell you, and why it matters>

## Artifacts
<paths / CI run URLs>
```

## Live ticks (Phase 7)

Every 5 minutes, report only what you can **observe**: the suite in flight, elapsed time, counters if the harness exposes them, and the re-checked served SHA. Never invent progress — a percentage you inferred is worse than "running, 12 min elapsed, no counters exposed by this harness", because the first is believed.

The tick is also a **watchdog** (default in every mode): when nothing observable has advanced for `stall_after_ticks` consecutive ticks, the tick row is replaced by a stall report — what stopped moving, since when, the probable cause from the native sources, and the action taken (cancel + one retry, or failed-infrastructure). A suite past the stall threshold is never still reported as "running".

Sources: `gh run view <id> --json status,jobs`, the harness log tail, the harness's own summary line. If the harness exposes nothing until it finishes, say that once at the start rather than emitting empty ticks.

## fix-loop tick table

In fix-loop mode, each 5-minute tick prints one recap row (same observability rule — only what you can observe):

```markdown
| Iter | Suite in flight | Tests total | Done | ✅ | ❌ | Skips | Elapsed | ETA | Served SHA |
|---|---|---|---|---|---|---|---|---|---|
| 3/20 | e2e-python (12/38 phases) | 165 | 71 | 68 | 3 | 12 | 22 min | ~34 min | `a1b2c3d` ✓ |
```

- **ETA** is an estimate and is labeled as one: extrapolate from the observed pace of *this* suite this run, falling back to the config's `typical_duration`. No counters exposed → `—`, never an invented percentage.
- **Skips** here are by-design skips observed so far; they are context, not alarm.
- **Served SHA** re-checked every tick; `✓` = still this iteration's HEAD. A mismatch flips the iteration to **invalid** on the spot (stolen slot — the iteration re-runs and does not count toward any limit).

## fix-loop final report

Persist to `.claude/full-test/fix-loop-<date>/report.md`:

```markdown
# /full-test fix-loop — <branch>, started <date>

**Verdict:** <0 failures in N iterations — X skips remain awaiting user info | stopped: no progress after N iterations | stopped: iteration cap>

## Iterations

| Iter | SHA | Failures found | Fixed (class) | Commit |
|---|---|---|---|---|
| 1 | `abc1234` | 5 | 3 product, 1 test-hardening, 1 → needs-user | `def5678` |
| 2 | `def5678` | 1 | 1 product (escalated to opus-deep) | `9abcdef` |
| 3 | `9abcdef` | 0 | — | — |

## Bugs fixed
<per fix: failure, root cause, fix summary, agent type used, commit SHA>

## Tests hardened against slowness
<per test: what was flaky/slow, what changed (timeouts, polling, retries) — assertions untouched>

## Skips endgame
<per prerequisite group: what was missing, the question asked, the answer (or "no answer — still skipped"), tests unlocked, their outcome after the targeted re-loop>

## Remaining skips / blind spots
<what is still not verified and why it matters>

## Backups
<per iteration: dump path — rotation per keep_last>
```

The four-outcome discipline holds throughout: a needs-user item is never reported as passed or silently dropped, and an unanswered skip stays a skip — the report never upgrades it.
