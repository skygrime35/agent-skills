#!/usr/bin/env bash
set -e
git init -q -b main
git config user.name "Eval User"
git config user.email "eval@example.com"
echo "# workspace" > README.md
git add README.md
git commit -q -m "init"
