#!/usr/bin/env bash
# Legacy layout: an older agents-md copied its checkers into scripts/ without the
# version marker. The copies are the canonical scripts minus the marker line.
set -e
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../skills/agents-md/scripts" 2>/dev/null && pwd || true)"
git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
mkdir -p scripts cmd
echo 'package main' > cmd/main.go
for f in check_no_todo check_monolith check_no_stub check_forbidden_chars; do
  if [ -f "$SRC/$f.py" ]; then
    grep -v '^# dev-skills: ' "$SRC/$f.py" > scripts/$f.py
  else
    echo "fixture: canonical script $f.py not found next to the eval" >&2; exit 1
  fi
done
cat > AGENTS.md <<'EOT'
# Crawler
- Production branch is `main`; never commit to it directly.
- Build with `go build ./...`.
EOT
git add -A && git commit -q -m init
