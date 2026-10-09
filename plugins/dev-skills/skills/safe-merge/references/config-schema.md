# `.claude/safe-merge.yml` schema

Per-project config. **Auto-detection refreshes the structural fields on every run; the human-authored `quirks`/overrides are never silently overwritten** (show a drift diff and ask). Its main purpose: capture the singular, non-guessable specifics of a project.

## Secrets policy (non-negotiable)

- **Never store secret values.** Reference env-var **names** only (`METRICS_TOKEN`, not its value).
- No tokens, passwords, private keys, or `.env` contents.
- Structural, shareable fields → committed. Machine-specific paths and any sensitive host detail → the `local`/gitignored block (or an env var), never the committed part.
- On write, **lint the committed portion** and reject anything shaped like a token/key/credential.

## Layout

```yaml
# --- committed: structural, shareable ---
version: 1
detected_at: { sha: <TARGET sha at detection>, note: "stamp after the run; scripts can't call Date.now" }

project_type: web-service        # web-service | library | cli | mobile | static-site | monorepo
branches:
  source: develop
  target: main
  confidence: high               # low → skill must confirm with the human each run

deploy:
  trigger: auto-branch           # auto-branch | auto-tag | manual | unknown
  detail: "push to main → GitHub Actions self-hosted runner → scripts/deploy.sh prod"
  prod_url: https://example.com
  preprod_url: https://preprod.example.com
  version_endpoint: /api/version # what to poll to confirm the running SHA
  auto_rollback: "deploy.sh retags :rollback→:latest on health-check/migrate --check failure (CODE only, not DB)"

tests:                           # harvested from CI (the oracle); mark side-effecting ones
  static: ["docker compose exec -T backend pytest -q --no-cov", "cd frontend && npx next build"]
  e2e_flow:
    trigger: "gh workflow run deploy.yml --ref develop"   # prefer workflow_dispatch over empty commits
    wait: "gh run watch <id> --interval 20 --exit-status"
    seed: "docker compose exec backend python manage.py seed_e2e_users"
    run:  "E2E_DEEP=1 bash scripts/tests/test.sh <PREPROD_URL>"

backups:
  prod: "ssh <host>; bash scripts/reviewmaster-backup.sh prod"      # host in `local:` block
  preprod: "ssh <host>; bash scripts/reviewmaster-backup.sh preprod"
  verify: "tail -5 <backup.log> ends with 'OK ... sha256=...'"
  restore: "scripts/restore-from-backup.sh <env> <dump>"
  prod_to_preprod_copy: "scripts/copy-prod-to-preprod.sh"           # prod→preprod ONLY
  blind_spots: ["object storage not versioned", ".env not backed up", "Redis not backed up"]

db:
  system: postgres
  orm: django
  migration_glob: "**/migrations/*.py"
  statement_timeout_ms: 30000    # migrations exceeding this on real volume get killed

changelog: { file: CHANGELOG.md, format: keep-a-changelog, language: fr }

# --- local: machine-specific / sensitive (gitignore this block or a *.local.yml) ---
local:
  ssh_host: "ubuntu@<ip>"        # not committed
  runner_path: "/home/.../scripts"
  env_var_names: [METRICS_TOKEN, MEDIA_SIGNING_SECRET]   # NAMES only, never values

# --- human-authored: the non-guessable specifics (never auto-overwritten) ---
quirks:
  - "Postgres UID must stay 70:999, never 999 (broke preprod once)"
  - "preprod is a single shared deploy slot — another push can steal it mid-E2E"
  - "media object storage is not versioned; deleted objects are unrecoverable"
  - "deploy health-check hits /api/version (not /api/health) → functional bugs don't auto-rollback"
```

## Freshness / drift

- Stamp `detected_at.sha` after a run (scripts have no clock; use the git SHA as the stamp).
- On each run, diff detected structural values vs stored. Structural drift → update automatically but **report it**. Drift touching a `quirks`/override → show the diff and **ask before changing**.
- Recommend committing the structural block and gitignoring the `local` block (e.g. `.claude/safe-merge.local.yml`), so multiple machines don't fight over machine-specific paths.
