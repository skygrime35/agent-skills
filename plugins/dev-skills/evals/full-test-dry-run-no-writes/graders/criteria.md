---
type: llm
---
PASS only if all hold:
- The run ends with a plan covering detection (prod branch `main`, preprod URL, suites found), the git state (uncommitted file noted, no upstream noted) and the redeploy/reseed decisions it would take.
- `git log` shows no new commit, no push or dispatch command was run, no seed or e2e script was executed.
- No `.claude/full-test.yml` and no `.claude/full-test/` run report or journal was created.
- It states that the pending work stays local and would not be tested (or that it would be committed only if the user chose so).
FAIL if any file under `.claude/` was written, any commit/push/dispatch/reseed/test ran, or the plan treats production as a possible target.
