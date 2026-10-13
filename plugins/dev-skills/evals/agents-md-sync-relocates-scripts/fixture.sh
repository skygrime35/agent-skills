#!/usr/bin/env bash
set -e
git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
mkdir -p scripts cmd
echo 'package main' > cmd/main.go
for f in check_no_todo check_monolith check_no_stub check_forbidden_chars; do printf '#!/usr/bin/env python3\n"""%s"""\n' "$f" > scripts/$f.py; done
cat > AGENTS.md <<'EOT'
# Crawler
- Production branch is `main`; never commit to it directly.
- Build with `go build ./...`.
EOT
git add -A && git commit -q -m init
