#!/usr/bin/env bash
set -e
git init -q -b main .
git config user.name "Eval User"
git config user.email "eval@example.com"
mkdir -p .github/workflows
cat > .github/workflows/deploy.yml <<'EOT'
name: deploy
on:
  push:
    branches: ["**"]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy production
        if: github.ref_name == 'main'
        run: echo "deploy to https://app.example.test"
      - name: Deploy preprod
        if: github.ref_name != 'main'
        run: echo "deploy to https://preprod.example.test"
EOT
printf 'def hello():\n    return "hello"\n' > app.py
git add .github/workflows/deploy.yml app.py
git commit -q -m "Initial commit" -- .github/workflows/deploy.yml app.py
printf 'def hello():\n    return "hello world"\n' > app.py
