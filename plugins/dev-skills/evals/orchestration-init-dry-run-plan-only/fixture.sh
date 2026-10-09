#!/usr/bin/env bash
set -e
git init -q -b main .
git config user.name "Eval User"
git config user.email "eval@example.com"
cat > AGENTS.md <<'EOT'
# Demo
- Never commit to main.
EOT
git add AGENTS.md
git commit -q -m "Add AGENTS.md" -- AGENTS.md
