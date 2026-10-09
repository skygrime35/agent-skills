#!/usr/bin/env bash
set -e
git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
echo '# Existing rules' > AGENTS.md
echo '{ "name": "demo" }' > package.json
git add AGENTS.md package.json
git commit -q -m "Initial commit"
