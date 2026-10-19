---
max_turns: 25
allowed_tools:
  - Bash
  - Read
  - Write
  - Edit
  - Skill
  - Agent
timeout_seconds: 600
---
This repo deploys production from `main` (https://app.example.test) and preprod from every other branch (https://preprod.example.test). I'm on `feature/login`. I want an autonomous manual acceptance test of this branch, where you run every step yourself in a browser and give me a report, but for now just do a dry run: show me the scope, the features you found, the ordered test plan and which browser driver you would use. Do not write, commit, prepare or change anything.
