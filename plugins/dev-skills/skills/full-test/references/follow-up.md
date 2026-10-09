# Follow-up: stall detection and host resource watch

Detail of SKILL.md Phase 7. The 5-minute tick is a progress report **and** a watchdog; it always runs when at least one suite is launched.

Two different stall counters exist, do not confuse them: `follow.stall_after_ticks` (this file: 5-minute tick, default 3) and `fix_loop.watchdog.stall_after_cron_ticks` (the fix-loop cron, 10-minute tick, default 2; see `fix-loop.md`).

## Stall detection

Record what each tick observed (counter values, the CI job's current step, log tail offset, run status). If **nothing observable has advanced for `stall_after_ticks` consecutive ticks** (default 3 = 15 min), the suite is presumed **stalled**; waiting longer is not the response:

1. **Investigate** via native sources: `gh run view <id> --json status,jobs` (hung job, lost runner, queued behind another run), the harness log tail (last line and its age), preprod reachability + served SHA.
2. **Name the cause** if visible and report it instead of another identical row.
3. **Act once, bounded:** a run the CI marked hung/lost -> cancel and retry **once**; a dead preprod -> environment incident, stop the affected suite and report. If the retry stalls again, classify the suite **failed (infrastructure)** with the evidence. Never leave the run hanging and never report a stalled suite as "running" past the threshold.
4. **Calibrate before flagging:** a long `typical_duration` with a harness that exposes no counters is not stalled merely because it is quiet. The threshold then applies to the sources (log growth, job step changes); if nothing is observable, say so once at the start and use `typical_duration` + margin as the deadline.

In fix-loop, a suite that ends failed (infrastructure) after a stall is triaged as infra: no fix agent. The same suite stalling on consecutive iterations is a no-progress signal, not a code problem.

## Host resource watch

When the config declares `resources:`, or detection shows the tests, runner or preprod stack share a reachable host, each tick samples disk and RAM there. Above `resources.disk_max_pct` (default 85) or `resources.ram_max_pct` (default 90):

1. Run only the declared safe clean commands (`resources.clean`; "safe" is project-specific). Never improvise a cleanup beyond that list.
2. Re-sample. Still above -> report an **environment risk** with the numbers; treat later suite failures as candidate-infrastructure until resources recover.
3. A cleanup never touches artifacts of the run in flight, DB backups within `keep_last`, or anything a project guardrail protects.

Do not invent progress you cannot observe; prefer the project's native progress source.
