---
max_turns: 30
allowed_tools:
  - Bash
  - Read
  - Write
  - Edit
  - Skill
timeout_seconds: 600
---
Set up a tiny fixture first: create a git repo in the current directory with a file AGENTS.md containing exactly these lines:
## Orchestration
- Delegate every multi-file task to `ghost-standard` via the Agent tool.
- Run agents in parallel when requests are unrelated.
- Never use `git stash`, `git add -A`, `git checkout` or `git reset` on a shared tree.
Fix my multi-agent rules so they are consistent, and make them shorter if you can. Apply the fixes after showing me the plan; I confirm the plan.
