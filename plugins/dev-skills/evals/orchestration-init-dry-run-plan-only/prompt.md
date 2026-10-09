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
# Demo
- Never commit to main.
Then show me what setting up the agent-orchestration rules and subagent types would do, as a dry run. Write nothing. Print `sha256sum AGENTS.md` right after creating the fixture and again as the very last command, so I can verify the file is unchanged.
