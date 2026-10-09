# Detection reference

How Phase 0 auto-detects a project's shape. Prefer **positive evidence**; when evidence is absent or contradictory, record `unknown` and surface it as a blind spot — **never assume the benign case**. Spawn parallel subagents for independent probes.

## 1. Project type

| Type | Signals |
|---|---|
| web-service | server framework (Django/Rails/Express/Next/Laravel/Phoenix…), a Dockerfile/compose, a deploy pipeline, a DB |
| library | published package manifest (`[project]` in pyproject, `"main"/"exports"` + `publishConfig` in package.json, `Cargo.toml [lib]`, `setup.py`), semver tags, no deploy |
| CLI | entry-point/bin manifest, no server, no DB |
| mobile | `android/`+`ios/`, `pubspec.yaml`, `*.xcodeproj`, React Native / Flutter config |
| static-site | SSG config (Astro/Hugo/Eleventy/Gatsby), `netlify.toml`/`vercel.json`, no server DB |
| monorepo | `pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`, Bazel `WORKSPACE`, multiple `packages/*`/`apps/*` each with its own manifest |

The type sets the **risk taxonomy** (Phase 2) and the **"what will happen"** narrative (Phase 6): a library's risk is semver + downstream breakage (not downtime); mobile has **no rollback** (users keep old installed versions hitting your API); a monorepo may fan out to many independently-deployed services.

## 2. Branch resolution (SOURCE → TARGET)

- Default branch (TARGET candidate): `git symbolic-ref refs/remotes/origin/HEAD` → strip `origin/`.
- **Best "which branch is prod" oracle:** the branch/tag that actually triggers the production deploy (see §3). Cross-check against the default branch and the live version endpoint.
- Common SOURCE names: `develop`, `dev`, `staging`, `next`. Common TARGET: `main`, `master`, `production`, `release`.
- **Topologies to handle explicitly:**
  - *Gitflow*: `develop` → `main`, with `release/*` and `hotfix/*`. If invoked from `release/x`, the SOURCE is that release branch, not `develop`.
  - *Promotion chain* `dev → staging → main`: never skip a stage — merging `dev→main` directly is wrong.
  - *Maintenance/backport lines* (`main` = v2, `1.x` = maintenance): SOURCE may legitimately be **behind** TARGET on some commits; don't read this as "divergence to investigate".
- **When confidence is low, confirm the pair with the human** (Phase 0 step 10). Never merge into a branch you're unsure is the real release branch.

## 3. Deploy-trigger detection (broad; `unknown` is first-class)

Search, in rough order of specificity:

| Source | What to read |
|---|---|
| GitHub Actions | `.github/workflows/*.y*ml` — `on: push: branches:` → which branch deploys; `on: workflow_dispatch`; `on: push: tags:`; jobs calling deploy scripts; `runs-on` (self-hosted?) |
| GitLab CI | `.gitlab-ci.yml` — `rules:`/`only:` on branches/tags, `environment: production` |
| CircleCI | `.circleci/config.yml` — workflow filters |
| Jenkins | `Jenkinsfile` — `when { branch }` |
| Vercel | `vercel.json` (+ Git integration is often **dashboard-side, invisible in repo**) |
| Netlify | `netlify.toml` `[context.production]` |
| Render | `render.yaml` |
| Fly.io | `fly.toml` (deploy usually via `fly deploy`, may be manual/CI) |
| Heroku | `Procfile` + `app.json` (pipeline promotion often dashboard-side) |
| AWS Amplify | `amplify.yml` |
| Tag/release | publish-on-tag workflows, `release-please`, `semantic-release` |

**Critical rule:** many platforms deploy from their own side with **nothing committed in the repo**. If you can't positively identify the trigger, set `deploy_trigger: unknown` and treat the merge as **potentially production-impacting**. Also confirm the endpoint the deploy exposes (`/api/version`, `/health`, a build SHA header) so Phase 4/7 can assert what's actually running.

Deploy-trigger states to record: `auto-branch` (push to TARGET deploys) · `auto-tag` (tag/release deploys — the merge itself may be inert; the *tag push* is the gated action) · `manual` (a human/CI button) · `unknown`.

## 4. Test/build command harvesting — CI is the oracle

Do **not** guess test commands. Read them from where the project actually runs them:

1. **CI config** (same files as §3): the `run:` steps are the canonical test/lint/build/typecheck commands. This is the most reliable, portable source.
2. **Task runners:** `package.json` `scripts`, `Makefile`, `justfile`, `tox.ini`/`noxfile.py`, `Taskfile.yml`, `composer.json` scripts, `mix.exs` aliases, `Rakefile`, `build.gradle`, `Cargo.toml`.
3. **Package manager** from the lockfile: `package-lock.json`→npm, `pnpm-lock.yaml`→pnpm, `yarn.lock`→yarn, `bun.lockb`→bun, `poetry.lock`→poetry, `uv.lock`→uv, `Pipfile.lock`→pipenv. Using the wrong one breaks installs.

**Classify every discovered command `safe-to-run` vs `side-effecting`.** Anything matching deploy/publish/release/prod/migrate-prod/`push`/`rm`/`drop` is side-effecting — **never auto-run it**. Add CI-mode flags to avoid hangs: `CI=true`, Vitest/Jest `--run`/`--watchAll=false`, `--ci`, non-interactive/`--yes`. Note commands that need services (testcontainers, a live DB) so a "bare" run doesn't produce a false red.

## 5. DB / ORM / migration system

| Stack | Migration signal | Backup path |
|---|---|---|
| Django | `**/migrations/*.py`, `manage.py migrate` | `pg_dump` (often via SSH/Docker) |
| Rails | `db/migrate/*.rb`, `schema.rb` | `pg_dump`/`mysqldump` |
| Alembic | `alembic/versions/*.py` | dump |
| Prisma | `prisma/migrations/`, `schema.prisma` | often **managed DB snapshot API** |
| TypeORM/Sequelize/Knex/Drizzle | `migrations/*.ts`, `drizzle/` | dump or managed |
| Ecto (Elixir) | `priv/repo/migrations/*.exs` | `pg_dump` |
| Flyway/Liquibase | `db/migration/V*.sql`, `changelog.xml` | dump |
| golang-migrate/Diesel/EF Core/Laravel | `migrations/*.sql`, `Migrations/*.cs`, `database/migrations/*.php` | dump |

**Managed databases** (Neon, Supabase, PlanetScale, RDS, Cloud SQL): backups are **provider snapshots via API/CLI**, not `pg_dump` over SSH. Detect from the connection host / provider config and record the snapshot command in `quirks`.

## 6. Changelog format

Detect before writing (Phase 5): existing `CHANGELOG.md` header style (**Keep a Changelog** = `## [x.y.z]` + Added/Changed/Fixed), **towncrier** (`changelog.d/` or `newsfragments/` + `[tool.towncrier]`), **changesets** (`.changeset/*.md`), **release-please** (`release-please-config.json`, bot-managed). If a tool owns the changelog, **defer to it**. Audience language = the existing changelog's language.

## 7. Preprod / staging

Detect a staging environment and its deploy + seed path: a `preprod`/`staging` branch or env, a second compose file, a `PREPROD_URL`, a seed management command. Record how to trigger its deploy (ideally `workflow_dispatch`) and how to reseed. If none exists, E2E-on-preprod is **NOT COVERED** (blind spot), not a failure.
