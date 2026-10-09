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
Then check whether my multi-agent rules are sound and tell me what is wrong. Do not fix anything. Print `sha256sum AGENTS.md` right after creating the fixture and again as the very last command, so I can verify the file is unchanged.
