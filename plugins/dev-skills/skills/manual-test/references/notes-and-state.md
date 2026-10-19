# Notes, state and resume

Working files live in `RUN_DIR` = `.claude/manual-test/<RUN_ID>/`. They are not committed during the run (Phase 1 excludes the folder locally). Archive in Phase 6 is the only committed output.

## `notes.md`

Appended immediately when a remark appears (never batched at the end). Header with run id, scope, target, SHA tested, tester devices. One table:

| # | Step / feature | Observed | Expected | Lead (file/area hint) | Status |
|---|---|---|---|---|---|

- `#`: sequential `N-01`, `N-02`... never reused.
- `Observed`: what the tester reported, verbatim where short, evidence reference (screenshot name or "sent in chat").
- `Expected`: the step's expected result or the tester's stated expectation.
- `Lead`: a hint for the fixer (suspect file, route, component, flag) from the diff or your read-only look. Never a fix.
- `Status`: `open`, `to decide` (needs a human choice), `agent suggestion, to confirm`, `fixed`, `re-tested ok`, `re-tested ko`, `wontfix` (with reason), `idea` (backlog, not a defect).
- Type is stated in the Observed cell prefix: `[bug]`, `[ux]`, `[text]`, `[idea]`, `[off-scope]`. `[off-scope]` marks a remark unrelated to the change set under test (an old checkbox, an old dialog): it is kept, never dropped, and grouped apart at decision time.
- A remark reported in a specific context (device, role, second window) that the agent cannot reproduce elsewhere, or that "the code says works", stays `open` as `retest in the original context`; never closed as "not reproduced".

Below the table, a **Decisions** section: dated lines (`YYYY-MM-DD HH:MM - N-03: <question> -> <answer>`), one per product decision the tester takes mid-run (answers to clarification questions, rule changes). Decisions are not table rows.

Then a **Results** section lists every step with `passed`, `passed (verified by agent)`, `failed`, `skipped by tester`, `blocked`, `not answered`, `not tested (reason)`, `validated as a side effect of step <n>`.

## `state.json`

Rewritten after every step (atomic write). Contains no secrets. Step ids are the single global numbering (`step-format.md`); `plan[].verified` records that the group passed the per-group code verification (`analysis.md`); `values` records the form value set submitted per step.

```json
{
  "version": 1,
  "run_id": "20261016-1500",
  "started_at": "...", "updated_at": "...",
  "scope": {"form": "develop..main", "from": "<sha>", "to": "<sha>"},
  "target": {"kind": "preprod", "url": "...", "served_sha": "..."},
  "devices": ["desktop", "android"],
  "plan": [{"feature": "...", "risk": "high", "device": "desktop", "verified": true, "verified_sha": "<sha>", "steps": [{"id": "3", "title": "...", "result": "pending"}]}],
  "current": "3",
  "results": {"1": {"result": "passed", "at": "..."}, "2": {"result": "validated as a side effect of step 1"}, "4": {"result": "skipped by tester", "reason": "no second device"}},
  "values": {"3": {"variant": "must fail", "fields": {"email": "not-an-email"}}},
  "accounts": [{"identifier": "manual-test-...-admin@example.test", "credentials_from": "created by the skill, password given in chat only"}],
  "prepared": [{"what": "order manual-test-...", "where": "preprod", "undo": "..."}],
  "phase": 3,
  "fix_round": 0
}
```

## Resume

On launch, look for `.claude/manual-test/*/state.json` with `phase < 6` and `updated_at` under 7 days: offer to resume (or resume directly with `--resume`). Resume checklist: reread `notes.md`; re-check the served SHA (changed => say so, affected results are suspect); verify `prepared[]` objects still exist, re-prepare if gone; announce "Resuming at step <current>"; continue. Older runs: report them and start fresh; never delete without asking.
