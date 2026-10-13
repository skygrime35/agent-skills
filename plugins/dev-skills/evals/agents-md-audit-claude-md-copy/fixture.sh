#!/usr/bin/env bash
set -e
git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
mkdir -p src && echo 'print("ok")' > src/app.py
cat > AGENTS.md <<'EOT'
# Shop
- Production branch is `main`; never commit to it directly.
- Run the app with `python3 src/app.py`.
- Never log customer emails.
EOT
cat > CLAUDE.md <<'EOT'
# Shop

@AGENTS.md

Rules for this project:
- Production branch is `main`; never commit to it directly.
- Run the app with `python3 src/app.py`.
- Never log customer emails.
- Always answer in English.
EOT
git add -A && git commit -q -m init
