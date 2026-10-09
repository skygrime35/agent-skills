---
type: regex
target:
  source: file
  path: AGENTS.md
pattern: "^## Orchestration\\n- Delegate every multi-file task to `ghost-standard` via the Agent tool\\.\\n- Run agents in parallel when requests are unrelated\\.\\n- Never use `git stash`, `git add -A`, `git checkout` or `git reset` on a shared tree\\.\\n?$"
---
