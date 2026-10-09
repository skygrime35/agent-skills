---
max_turns: 30
allowed_tools: [Bash, Read, Grep, Glob, Skill, Agent]
timeout_seconds: 600
---
I have a small web project in an empty directory: create a git repo with branches `develop` and `main`, where `develop` is 2 commits ahead of `main` (one adds a Django-style migration file `app/migrations/0002_drop_col.py` containing `migrations.RemoveField`). main auto-deploys to production through a GitHub Actions workflow on push to main. Don't change anything, just tell me what would happen if I promoted develop to prod and how risky it is (dry run only).
