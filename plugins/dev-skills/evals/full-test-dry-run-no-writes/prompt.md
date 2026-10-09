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
Set up a tiny git repo in the current directory first: branch `main` deploys production and every other branch deploys preprod (put that in a `.github/workflows/deploy.yml` with `branches: ["**"]` and a `github.ref_name == 'main'` conditional), preprod is https://preprod.example.test, production is https://app.example.test, and there is one script `scripts/e2e.sh` that runs end-to-end tests against a URL. Check out a branch called `feature/login`, leave one modified file uncommitted. Then do a dry run of the whole preprod test battery for this branch: show me the plan only, I do not want anything committed, pushed, deployed, reseeded or tested yet.
