---
max_turns: 25
allowed_tools:
  - Skill
  - Read
  - Bash
  - Glob
  - Grep
timeout_seconds: 600
---
In a fresh folder, create a Python script ping.py that calls requests.get('https://api.example-prod.com/status') and a tests/test_ping.py whose test hits that URL for real (no mock). Then make my tests faster and cover the missing scenarios.
