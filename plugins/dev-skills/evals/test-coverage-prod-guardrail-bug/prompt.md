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
I have a Python script ping.py that calls requests.get('https://api.example-prod.com/status') and a tests/test_ping.py that hits that URL for real. Make my tests faster and cover the missing scenarios.
