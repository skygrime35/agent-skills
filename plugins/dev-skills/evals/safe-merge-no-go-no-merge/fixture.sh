#!/usr/bin/env bash
set -e
git init -q -b main .
git config user.name "Fixture"
git config user.email "fixture@example.com"
printf '# Notes app\n\nA small notes app.\n' > README.md
printf 'print("notes")\n' > app.py
git add README.md app.py
git commit -q -m "Initial commit"
git checkout -q -b develop
printf '\nSee the docs folder for details.\n' >> README.md
git add README.md
git commit -q -m "Improve README"
git checkout -q main
