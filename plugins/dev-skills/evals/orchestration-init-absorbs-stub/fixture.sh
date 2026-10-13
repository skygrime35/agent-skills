#!/usr/bin/env bash
set -e
git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
mkdir -p src && echo 'print("ok")' > src/app.py
cat > AGENTS.md <<'EOT'
# Shop

## Agent behaviour

### 1. Branch discipline

Before the first modification of a task: `git branch --show-current`, then `git status --short`.

**Never modify `main` directly** without an explicit request.

**Parallel agents never edit the same working tree**: one git worktree per agent. <!-- agents-md:isolation-stub. Minimal rule: run /orchestration to complete it (it replaces this line with the full parallelism doctrine). -->

## Commands

- Run: `python3 src/app.py`
EOT
git add -A && git commit -q -m init
