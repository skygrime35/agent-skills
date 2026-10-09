---
name: safe-merge
argument-hint: "[<source>..<target>|revert] [--dry-run] [--help]"
description: "Use before merging a development branch into a release/production branch — especially when merging that branch auto-deploys production with real users. Runs an exhaustive, portable pre-merge gate: capability preflight, git safety + topology checks, a ranked human-readable change report, secret scan, backups of everything backupable, a migration rehearsal on a clone of production data, the project's full test battery (E2E included), a format-aware CHANGELOG, then a hard go/no-go decision that only merges after explicit human confirmation — and prepares a ready-to-run revert procedure. Also runs in --dry-run (analyze only) and revert modes. Portable across any project via per-project auto-detection + a .claude/safe-merge.yml config; when anything is unknown it degrades to an explicit blind spot, never a green check."
---

# /safe-merge

Make merging a dev branch into a production/release branch **as close to infallible as possible**. Merging into the release branch often redeploys production, where real (often paying) users live, so this skill *is* the quality gate: it analyzes the whole batch, backs up everything backupable, rehearses migrations on real-shaped data, runs the full test battery, writes a non-technical CHANGELOG, and only merges **after an explicit human "go"** — with a pre-built revert procedure standing by.

This skill is **portable across any project**. It auto-detects each project's branches, deploy trigger, tests, backups, DB/ORM and changelog conventions on every run, and remembers the non-guessable specifics in a per-project `.claude/safe-merge.yml`.

## Usage

```
/safe-merge                     # full gated run: analyze → back up → test → recap → (human go) → merge → watch
/safe-merge --dry-run           # analyze only: phases 0-2 + recap. Zero writes, zero triggers, zero backups, no merge
/safe-merge <source>..<target>  # override branch pair (default: auto-detected, usually develop..main)
/safe-merge revert              # execute the revert procedure prepared by the most recent run (roll production back)
/safe-merge --help              # print this Usage block and stop
```

If invoked with `--help`/`-h` and nothing else, print the Usage block above verbatim and stop.

## What this skill is for / non-goals

**For:** de-risking the promotion of `SOURCE_BRANCH` (dev) → `TARGET_BRANCH` (release/prod) when a mistake reaches real users. **Not for:** everyday feature-branch merges with no production surface (use plain git), or rewriting history. It never touches production data destructively except an explicitly-confirmed revert restore.

## Five governing principles (these override any convenience)

1. **Unknown ⇒ explicit blind spot / ask the human — NEVER default to "safe/green".** If the deploy trigger, tests, backups, or branch pair can't be determined with confidence, say so loudly and ask. A missing test suite is reported as "zero coverage — blind spot", never as a passing check. This is the core of the "zero breakage" promise.
2. **The project's CI config is the oracle** for the real test/build/deploy commands. Harvest them from `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, etc. rather than guessing.
3. **Mutations are serialized behind the human gate.** Backups that touch production, the merge, and any push happen only after explicit confirmation (backups per user policy in Phase 3). Only read/analysis/independent tests run in parallel.
4. **Reuse the project's native scripts** (backup / restore / prod↔preprod copy / deploy / seed). Never reimplement what the repo already ships.
5. **Fan out subagents liberally** (via the Agent tool) for any independent read/analysis/test work — detection probes, per-subsystem diff analysis, reading many migrations, running independent test suites. Use as many as help; keep all mutating steps single-threaded and gated.

## Tooling

**External CLIs** (Phase 0 preflight tests each; if missing/unauthenticated, stop with a fix list): `git`, `gh` (`gh run watch`, `gh workflow run`, `gh pr list --merged`, releases), `docker`/`docker compose`, `ssh`, `curl` + `jq`, `psql`, `rclone`, `node`/`npx`, `python` + Playwright, and a secret scanner (`gitleaks` / `trufflehog` / `detect-secrets`, or the repo's own `secret-scan` hook). Also verify **push rights** on the remote and **free disk** for dumps.

**Project-native scripts** (auto-detected, reused, never reimplemented): DB backup, restore, prod→preprod copy, deploy, E2E seed.

**Claude Code capabilities:** the **Agent tool** for massive parallel fan-out (principle 5); the **claude-in-chrome MCP** for a visual post-deploy smoke test — **on production, public/unauthenticated pages only** (the skill has no prod account; authenticated depth is covered by preprod E2E; a dedicated prod test credential may be supplied *interactively* and never persisted); **TaskCreate/TaskUpdate** to track the long procedure and make it resumable; **Monitor / ScheduleWakeup** for the post-deploy surveillance window.

## Reference files (load on demand)

- `references/detection.md` — project types, deploy-trigger detection across platforms, harvesting test commands from CI, package managers, DB/ORM systems (incl. managed DBs), changelog formats, branch topologies.
- `references/risky-migrations.md` — risky migration patterns per ORM, plus reversibility / backward-compat-with-running-code / lock-and-timeout analysis.
- `references/changelog-format.md` — conforming to existing changelog tooling, audience language, the "no vulnerability details" rule, technical→plain-language rewriting.
- `references/config-schema.md` — the `.claude/safe-merge.yml` schema, secrets policy, committed/gitignored split, freshness/drift.
- `references/rollback-procedure.md` — the generated rollback file template and the three-tier recovery strategy.

---

# Procedure

Follow the phases in order. Do not skip. Use `TaskCreate` to register the phases as a checklist at the start so progress is visible and the run is resumable. Placeholders are UPPERCASE (`SOURCE_BRANCH`, `TARGET_BRANCH`, `PROD_URL`, `PREPROD_URL`, `VERSION_ENDPOINT`). Any phase that fails a hard rule **stops the run** with a clear report; nothing downstream runs.

**Mode routing (do this first):**
- `revert` → jump straight to **Phase R**.
- `--dry-run` → run **Phases 0 → 2** then present the **Phase 6 recap**, and stop. Perform **no** writes, triggers, backups, commits, or merge.
- default → run all phases.

## Phase 0 — Preflight, profiling, capabilities, resumability

Goal: know exactly what kind of project this is, what "production" means here, and whether every capability you'll need actually works — before touching anything. Spawn parallel subagents for the independent detection probes (see `references/detection.md`).

1. **Resume check.** If `.claude/safe-merge/journal.md` (or `.json`) shows an in-progress run, read it and **offer to resume** at the last completed phase (skip already-done backups/tests). Do not blindly restart.
2. **Load + refresh config.** Read `.claude/safe-merge.yml` if present. Re-run detection regardless (config can be stale). On any drift between detected and stored values, **show the diff and ask before overwriting a human-authored `quirks`/override field** — never silently clobber it. Enforce the secrets policy: config holds env-var **names**, never values (see `references/config-schema.md`).
3. **Project type.** Classify: web-service / library / CLI / mobile / static-site / monorepo. This drives the risk taxonomy (Phase 2) and the "what will happen" narrative (Phase 6). A library's risk is semver/downstream breakage, not downtime; mobile has no rollback; a monorepo may fan out to many services.
4. **Resolve SOURCE/TARGET.** Default `develop..main`, but resolve properly: `git symbolic-ref refs/remotes/origin/HEAD` for the default branch, **cross-referenced with whatever branch/tag actually triggers the production deploy** (the best "which branch is prod" oracle) and the live `VERSION_ENDPOINT`. Handle gitflow (`release/*`, `hotfix/*`), promotion chains (`dev→staging→main` — don't skip staging), and maintenance/backport lines (SOURCE may legitimately be *behind* TARGET on some commits). **When confidence is low, confirm the pair with the human.**
5. **Deploy trigger — broad detection, `unknown` is first-class.** Look for GitHub Actions, `.gitlab-ci.yml`, `.circleci/`, `Jenkinsfile`, and platform configs (`vercel.json`, `netlify.toml`, `render.yaml`, `fly.toml`, `Procfile`/`app.json`, `amplify.yml`), and tag-based release. **Many platforms deploy from the platform side with nothing in the repo** — if you cannot positively identify the trigger, set `deploy_trigger: unknown` and **treat the merge as potentially production-impacting** (never assume safe). Confirm TARGET is really prod's source of truth (not a `production` branch or pinned tag).
6. **Harvest test/build commands from CI (the oracle).** Extract the real commands the project runs in CI; detect the package manager from the lockfile. Classify each command **safe-to-run vs side-effecting** — never auto-run a mutating target (`make deploy`, `release`, `test:e2e:prod`).
7. **Detect backups / preprod / DB / migrations.** Backup mechanisms; whether a preprod/staging exists and how it deploys/seeds; DB system + ORM (including **managed DBs** — Neon/Supabase/PlanetScale → provider **snapshot API**, not `pg_dump` over SSH); migration system.
8. **Detect changelog** format/tool and **audience language**.
9. **Capability preflight.** From the resolved config, enumerate and **actually test** every capability you'll need: `gh auth status`, SSH reachability to the prod/backup host, `docker`/`docker compose`, `curl`+`jq`, push rights on the remote (`git push --dry-run`), free disk for dumps, `PREPROD_URL` reachable. **Test each capability the way the project actually invokes it — not as a naive host-local `command -v`.** Many DB/backup tools (`psql`, `pg_dump`, `redis-cli`) are only ever reached **inside a container (`docker exec`) or over SSH on the prod host**; a host-local absence is then irrelevant and must **not** be reported as a blocker. Verify the real path: e.g. `ssh HOST 'docker exec <db_container> psql --version'` if that's how backups run. **Stop now** — with a precise "install/authenticate X" list — only for capabilities that are genuinely missing *along the path the project uses them*. Do not start Phase 1 half-equipped, but do not false-flag either.
10. **Announce + confirm.** Present the detected profile, the estimated time/cost of a full run, and — via `AskUserQuestion` — confirm the SOURCE/TARGET pair and project type, and fill any non-guessable `quirks`. Write/refresh `.claude/safe-merge.yml`.

## Phase 1 — Git safety & topology

1. `git fetch --all --prune`.
2. Verify **both** branches are in sync with their upstreams (`git rev-list --left-right --count SOURCE_BRANCH...@{u}` etc.): no unpushed local commits, no unpulled remote commits. Out of sync → stop and report.
3. **Outcomes — and do NOT mistake `--no-ff` merge nodes for a hotfix.** A repo that promotes with `git merge --no-ff SOURCE` leaves **merge commits on TARGET that SOURCE never has by construction**, so `git log SOURCE..TARGET` is routinely non-empty on a perfectly healthy branch — that is the normal state, not a divergence. Decide with **non-merge commits**, never the raw commit list. (Note: `git diff SOURCE..TARGET` is **not** a benign-test either — when SOURCE is ahead it shows SOURCE's own work *inverted*, so it is never empty; do not use it here.)
   - `git rev-list --count --no-merges SOURCE_BRANCH..TARGET_BRANCH` == 0 → TARGET has no real work of its own; the extra commits are benign merge nodes. **Proceed** (this is the common case for a `--no-ff` promotion workflow).
   - count **> 0** → a genuine hotfix/commit landed on TARGET and wasn't back-merged → **offer to back-merge TARGET→SOURCE first** (and re-run). Distinguish a legitimate maintenance/backport line, where TARGET-only commits are expected.
   - `git rev-list --count TARGET_BRANCH..SOURCE_BRANCH` == 0 → nothing to merge → clean exit: "already up to date".
   - Both sides have **real** (non-merge) unique commits → warn of a likely merge conflict in Phase 7.
4. Working tree clean (`git status --porcelain` empty).
5. **Record the pre-merge TARGET SHA** (`git rev-parse TARGET_BRANCH`) — the foundation of the revert procedure.

## Phase 2 — Exhaustive diff analysis + risk taxonomy

Goal: a complete, ranked picture of what this batch changes and every way it could hurt production. Fan out subagents by subsystem. See `references/risky-migrations.md`.

1. **Collect** the full change set:
   ```bash
   git log --oneline TARGET_BRANCH..SOURCE_BRANCH
   git shortlog -sn TARGET_BRANCH..SOURCE_BRANCH
   git diff --name-status TARGET_BRANCH..SOURCE_BRANCH
   git diff --shortstat TARGET_BRANCH..SOURCE_BRANCH
   git diff --dirstat=files,0 TARGET_BRANCH..SOURCE_BRANCH
   git log --oneline --merges TARGET_BRANCH..SOURCE_BRANCH
   ```
   For squash-merge repos, also pull PR metadata: `gh pr list --state merged --base SOURCE_BRANCH --json number,title,labels,mergedAt`.
2. **Categorize** by project type: Features / Fixes / Refactors / Perf / Infra & config / DB migrations / Dependencies / Docs / Tests / (semver-affecting API for libraries). If the repo uses Conventional Commits, use them; **otherwise fall back to diff content** (added/modified/deleted functions, `tests/`, `migrations/`) **and PR titles/labels** — never rely on bare "wip" messages.
3. **Secret scan — hard stop, before backups.** Run a secret scanner on `TARGET_BRANCH..SOURCE_BRANCH` and flag any sensitive path in the diff (`**/.env`, `secrets/**`, `cookies/**`, key/pem files). Any hit → **stop the entire run**; the secret must be purged from history before merging. **If no scanner is installed** (`gitleaks`/`trufflehog`/`detect-secrets`, or the repo's own `secret-scan` hook): first **offer to install one** (or run the repo's hook). If none can be run, fall back to a sensitive-path + high-entropy string grep over the diff **and explicitly report "no secret scanner — reduced coverage (blind spot)"** — never let an un-scanned diff read as "clean/green".
4. **Migration analysis.** For each migration in the diff, determine: destructive DDL patterns (drop/rename/type-change/`RunPython` value rewrites/`NOT NULL` without default); **reversibility** (reversible / irreversible); **backward-compatibility with the code still running during rollout** (migrations often apply at container boot before new code is fully live); and **real production row counts** for targeted tables (via SSH `psql -tAc "select count(*) from <table>"`, command shown + confirmed). Cross the estimated duration against any DB `statement_timeout` (e.g. 30s) — a long migration on a large table will be **killed mid-way**, potentially leaving a partial schema. Estimate lock/downtime.
5. **Config surface.** Diff `settings*`, `.env.example`, `docker-compose*` **including `build.args` (e.g. `NEXT_PUBLIC_*`, baked at build time)**, `Dockerfile*`, `nginx/`, `infra/`, and dependency lockfiles.
6. **New env keys.** Extract env keys newly referenced by the diff (`config("X")`, `os.environ[...]`, `process.env.X`) and **cross-check they exist in the real prod env** — which is typically **outside git** (SSH `grep` into the prod `.env`, command shown + confirmed) — plus a **preprod↔prod env delta** to catch keys present in preprod (so preprod tests pass) but absent in prod (so prod boots broken).
7. **Manual-step flags.** Flag compose/infra changes and Postgres `ALTER SYSTEM`-type changes that require a manual action the deploy script won't perform.
8. **Media/storage.** Flag any `MEDIA_*`/`R2_*`/object-storage change as its own risk category (signed-URL secrets, worker config, backend fallback to local).
9. **Output** the ranked **biggest-to-smallest** change list — the raw material for the Phase 6 recap and the Phase 5 CHANGELOG.

## Phase 3 — Backups (blocking, interactive, + config-infra snapshot)

Per the user's policy: detect the project's backup mechanisms, judge coverage, then either run them autonomously or propose a plan and iterate. **Backups run before the merge, but they are still gated by user validation when they touch production.**

1. **Decision tree.** Is there persistent state (DB, uploaded media, volumes)? **No → skip cleanly** (a library/CLI has nothing to back up — that's fine). **State exists but NO backup mechanism is detected → loud blocker/alert** (this is danger, not "nothing to do"). Do not conflate the two.
2. **Map coverage + blind spots:** prod DB, preprod DB, media/object storage, `.env`/secrets, volumes, Redis. Note what genuinely **cannot** be backed up/restored (e.g. non-versioned object storage, secrets not in any vault).
3. **Full coverage → run native backups autonomously**, prod **and** preprod, and **verify success as a hard gate** (e.g. the `OK … sha256=…` log line). Managed DB → trigger a provider snapshot via API. Do not reimplement what the deploy script already does automatically; add a dedicated manual backup taken at a controlled instant.
4. **Blind spots → propose the best-fit backup plan** for everything (prod + preprod), have the user validate, iterate, then execute the agreed plan.
5. **Snapshot non-DB rollback state:** current prod env values (record **names + hashes**, never secret values into git), compose/infra config, media backend, feature flags — so a config-caused break can be reverted too.
6. **Verify the rollback is ARMED:** the deploy's `:rollback` image (or equivalent previous-release artifact) exists **and matches the current prod SHA** (a shared preprod slot can make it diverge); the freshly taken backup's checksum is valid. If the escape hatch isn't real, say so before the gate.
7. Record everything (paths, checksums, blind spots) into the run journal and the rollback file (Phase 6.5).

## Phase 4 — Full test battery: static/unit + migration rehearsal + E2E deep

Run everything the user asked for. Parallelize independent suites; never target production.

1. **Static / unit / build / arch checks** from the CI-harvested commands. Force **CI mode** (`CI=true`, `--run`, `--watchAll=false`) to avoid watch-mode hangs; bring up required services (testcontainers); never run a side-effecting command. Any red → stop, fix on SOURCE, re-run.
2. **Migration rehearsal on a clone of production data** (only if the batch contains migrations — this is the single highest-value check):
   - Backups of both DBs already taken (Phase 3).
   - **Copy prod → preprod** using the project's native script — **direction prod→preprod ONLY, never the reverse** (the reverse would overwrite prod). Ensure preprod is running SOURCE's code so the new migrations are the ones exercised; the script's trailing `migrate` **is** the rehearsal, now running against real prod-shaped, prod-volume data.
   - **Measure:** wall-clock duration (= the real downtime/lock estimate), success/failure, `statement_timeout` overruns, and integrity (row counts preserved, no silent 0/NULL backfill).
   - **Portable fallback** when no prod→preprod script exists: restore the prod dump into a throwaway ephemeral DB and run the migrations there.
3. **E2E deep on preprod:**
   - **Trigger the preprod deploy via `gh workflow run` (workflow_dispatch)** in preference to empty commits (which pollute history and may miss `paths:` filters). If only a push trigger exists, use a single real commit (e.g. the CHANGELOG once finalized) rather than repeated empty commits.
   - Wait for the deploy; **verify `PREPROD_URL` `VERSION_ENDPOINT` == SOURCE SHA**.
   - Reseed the preprod DB with the project's seed command.
   - Run the deep/expensive suite (its own gating flag, e.g. `E2E_DEEP=1`).
   - **Re-verify the preprod SHA immediately before AND after** the suite — the preprod slot is often shared; if another push stole it mid-run, the results are invalid → re-run. Never point E2E at prod.
4. **Graceful degradation:** no preprod → mark E2E **NOT COVERED (blind spot)**, not "failed infra". No tests at all → report **"zero coverage — blind spot"**, never a green check.

## Phase 5 — CHANGELOG (format-aware, decoupled from the trigger, committed after "go")

**Append-only, newest-on-top — never rewrite from scratch.** The CHANGELOG is a cumulative history: **prepend** this merge's entry at the very top and **preserve every existing entry verbatim** below it. Create the file only if it doesn't exist yet. Never regenerate, reorder, reword, or drop prior entries — one new dated block per merge, accreting over time.

1. **Detect and conform to any existing changelog tooling** (Keep a Changelog, towncrier `changelog.d/`, changesets `.changeset/`, release-please). If a tool owns the changelog, **defer to it** (create a changeset/news fragment) instead of prepending prose that would corrupt its format. Monorepo → per-package changelog.
2. **Audience language** = the existing changelog's language by default (an OSS library's CHANGELOG is English even if the team speaks French). Otherwise the project's user-facing language.
3. Write a **non-technical** entry from the Phase 2 ranked list — grouped (New / Improved / Fixed / Other), plain language, **no vulnerability details** (don't hand attackers a map; see `references/changelog-format.md`).
4. **Have the user review/edit** the entry.
5. **Decouple from the preprod trigger** (that's `workflow_dispatch`). **Do NOT commit the CHANGELOG before the human "go"** — a no-go would leave an orphan "Release" entry. Commit it as part of the Phase 7 merge (or on a throwaway branch), not now.

## Phase 6 — Consolidated recap + hard gate

Present, in this order:

- **(A) What changes** — the exhaustive biggest-to-smallest list, each item carrying its risk flags: migration reversibility + estimated duration/downtime; new env keys missing from prod `.env`; config/infra changes needing a manual step; media/storage changes; "secret scan: clean".
- **(B) What secured the merge** — backups taken (what / where / checksums) + the explicitly-accepted blind spots; every test run + its result, **including the migration-rehearsal timing**; the **"rollback armed" status**.
- **Live prod state probe, taken just before the gate** — active background/Celery jobs, in-flight uploads, open live sessions, current load and time-of-day. **Recommend an off-peak window** if the deploy interrupts long-running jobs or many users are active.
- **(C) Go/no-go verdict** — explicit and argued.
- **(D) Exactly what will happen on merge** — **conditional on the `deploy_trigger` state**: auto-deploy / tag-or-manual / **unknown** (frame conservatively). Include estimated downtime **inclusive of migration duration**, and state plainly: **the automatic rollback restores CODE only, NOT the database — a destructive/irreversible migration's only recovery is a backup restore with up to RPO_X of data loss.** Name the real user impact.
- **HARD GATE:** ask for explicit confirmation via `AskUserQuestion`. Anything other than a clear "go" → **stop; nothing is merged.**

## Phase 6.5 — Prepare the revert procedure (BEFORE the push)

Write a durable `.claude/safe-merge/rollback-<TIMESTAMP>.md` (template in `references/rollback-procedure.md`) capturing: the pre-merge TARGET SHA, the `:rollback` image status, backup paths + checksums, the **migration reversibility verdict and whether a DB restore is required**, the config/infra snapshot, the media backend, and the **exact commands** for each of the three recovery tiers. This must exist *before* the merge so `revert` mode can run even in a fresh session.

## Phase 7 — Execute the merge (only after "go")

1. **Concurrency re-assertion:** confirm the SHA you tested still equals the SHA about to merge; re-fetch and handle a **non-fast-forward** push and a **merge conflict** with a clean abort path.
2. `git checkout TARGET_BRANCH` → `git merge --no-ff SOURCE_BRANCH -m "merge(TARGET): <summary>"` → commit the finalized CHANGELOG → **squash/clean any preprod-trigger commits** so they don't leak onto TARGET → `git push origin TARGET_BRANCH`.
3. **Monitor the deploy** with the project's native tool (e.g. `gh run watch <id> --interval 20 --exit-status`).
4. **Active surveillance window (N minutes) — the human is the monitor; say so, since there is usually no external alerting:** authenticated detailed health (`checks.db/redis/disk/celery_beat`), a **real login** smoke, a **media read** (object storage), Celery queue drain, `disk.free_pct`; plus a **browser-MCP visual smoke of public prod pages**. If the diff touched frontend build args, drive an **authenticated client flow** (catches the mixed-content trap that leaves `/api/health` green while the app is broken). If media was touched, read a real segment/thumbnail and check the signing-secret coherence.
5. Anything broken → **Phase R**.

## Phase R — Revert mode (`/safe-merge revert`, or "it's broken")

Load the most recent `.claude/safe-merge/rollback-<TIMESTAMP>.md`. Choose the **fastest safe recovery tier**:

1. **Image/code rollback** (e.g. the deploy's `:rollback` retag) if the deploy itself failed or the break is code-only.
2. **`git revert` of the merge commit + push** (redeploys the previous code) for a functional bug the health check didn't catch.
3. **DB restore from the pre-merge backup** — last resort, **only if a destructive/irreversible migration mutated data** (code revert alone would leave old code against an incompatible schema). Accept the RPO data-loss window; this is the irreversible `DROP DATABASE`/restore path, so double-confirm.

Confirm the chosen tier, execute it, then **verify the return to the pre-merge state**: health `ok`, `VERSION_ENDPOINT` back to the pre-merge SHA, at-risk table counts consistent. Write a short incident note.
