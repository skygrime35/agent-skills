#!/usr/bin/env bash
set -e
git init -q -b main .
git config user.name "Eval User"
git config user.email "eval@example.com"
cat > AGENTS.md <<'EOT'
## Orchestration
- Delegate every multi-file task to `ghost-standard` via the Agent tool.
- Run agents in parallel when requests are unrelated.
- Never use `git stash`, `git add -A`, `git checkout` or `git reset` on a shared tree.
EOT
git add AGENTS.md
git commit -q -m "Add AGENTS.md" -- AGENTS.md
