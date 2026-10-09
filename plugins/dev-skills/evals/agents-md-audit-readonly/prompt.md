---
max_turns: 25
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
- Run tests with `sudo docker compose run web pytest`.
- See `docs/MISSING.md` for architecture.
- Never commit to main.
Then review my agent documentation for stale or wrong content and tell me what is broken. Do not fix anything.
