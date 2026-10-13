#!/usr/bin/env bash
set -e
git init -q -b main .
git config user.name "Eval User"
git config user.email "eval@example.com"
mkdir -p .github/workflows scripts
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
cat > scripts/e2e.sh <<'EOT'
#!/usr/bin/env bash
# End-to-end tests against a URL: scripts/e2e.sh <url>
set -e
echo "running e2e against $1"
EOT
chmod +x scripts/e2e.sh
printf '# Demo app\n\nPreprod: https://preprod.example.test\nProduction: https://app.example.test\n' > README.md
git add .github/workflows/deploy.yml scripts/e2e.sh README.md
git commit -q -m "Initial commit" -- .github/workflows/deploy.yml scripts/e2e.sh README.md
git checkout -q -b feature/login
printf '\nWork in progress on the login page.\n' >> README.md
