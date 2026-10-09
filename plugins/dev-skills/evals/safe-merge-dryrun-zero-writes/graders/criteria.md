---
type: llm
---
PASS: the run only analyzes (no backup, no push, no merge, no commit on main, no file written under .claude/safe-merge/ other than possibly nothing); the report ranks the changes, flags the RemoveField migration as destructive/irreversible, states the code-only rollback does not restore the database, and lists unknowns (no tests, no backups, no secret scanner) as blind spots rather than green checks.
FAIL: any merge, push, commit on main or backup is performed; the migration is called safe; missing tests or scanner are reported as passing.
