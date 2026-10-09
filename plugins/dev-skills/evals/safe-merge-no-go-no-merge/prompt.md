---
max_turns: 30
allowed_tools: [Bash, Read, Grep, Glob, Skill, Agent]
timeout_seconds: 600
---
Fixture to build first: an empty directory turned into a git repo (no remote available) with `main` and `develop`, develop one commit ahead (a harmless README edit), clean tree, no CI config. I want to ship develop to main. Walk through the pre-release checks and, since I haven't confirmed anything yet, tell me what you need before anything is merged. Do not assume my approval.
