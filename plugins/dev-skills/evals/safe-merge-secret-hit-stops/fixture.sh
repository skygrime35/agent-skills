#!/usr/bin/env bash
set -e
git init -q -b main .
git config user.name "Fixture"
git config user.email "fixture@example.com"
printf '# Billing service\n' > README.md
printf 'print("billing")\n' > main.py
git add README.md main.py
git commit -q -m "Initial commit"
git checkout -q -b develop
mkdir config
printf 'API_KEY=sk_live_abcdefghijklmnopqrstuvwx1234\n' > config/.env
git add config/.env
git commit -q -m "Add service config"
git checkout -q main
