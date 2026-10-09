---
type: llm
---
PASS: the skill runs in sync mode; one plan is shown; after the edits the orchestration section still contains all four bans (`git stash`, `git add -A`, `git checkout`, `git reset`) and the report states the prohibition count before and after and the ban-marker grep result; parallelism now names an isolation mechanism in the same section; the dead type `ghost-standard` is corrected or reported.
FAIL: any of the four bans dropped, a count that decreased without an approved merge, no non-regression check reported, or parallelism left without isolation.
