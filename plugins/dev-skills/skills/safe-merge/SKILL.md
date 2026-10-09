---
name: safe-merge
argument-hint: "[<source>..<target>|revert] [--dry-run] [--help]"
description: "Runs the pre-merge gate before promoting a development branch into a release/production branch (often auto-deployed to real users): change report, secret scan, backups, migration rehearsal on prod-shaped data, full tests, CHANGELOG, then a human go/no-go before any merge, plus a prepared revert. Supports --dry-run and revert. Unknowns become blind spots, never green checks."
when_to_use: "Merge to main, promote to prod, release, ship develop, revert a release, roll back a deploy, pre-release checks, dry-run a merge."
---

# /safe-merge

Quality gate for promoting `SOURCE_BRANCH` (dev) into `TARGET_BRANCH` (release/prod) when a mistake reaches real users. Not for feature-branch merges without a production surface (use plain git), nor for rewriting history. Project specifics are auto-detected each run and the non-guessable ones remembered in `.claude/safe-merge.yml`.

## Usage

```
/safe-merge                     # full gated run: analyze → prepare (backups, rehearsal, tests) → recap → (human go) → merge → watch
/safe-merge --dry-run           # analyze only: phases 0-2 + recap. Zero writes, zero triggers, zero backups, no merge
/safe-merge <source>..<target>  # override branch pair (default: auto-detected, usually develop..main)
/safe-merge revert              # execute the revert procedure prepared by the most recent run (roll production back)
/safe-merge --help | -h         # print this Usage block and stop
```

With `--help`/`-h` and nothing else, print the Usage block verbatim and stop.

## Governing principles (they override any convenience)

1. **Unknown means blind spot, never green.** If the deploy trigger, tests, backups, secret scanner or branch pair cannot be determined with confidence, record it as an explicit blind spot and carry it into the recap. A missing test suite is "zero coverage", never a pass. Ask the human only when no safe default exists.
2. **The project's CI config is the oracle** for the real test/build/deploy commands (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, ...). Harvest, do not guess.
3. **Two authorization levels.**
   - *Preparation authorization*: one confirmation in Phase 0, shown with the detected profile. It pre-authorizes only prod **reads**, prod **backups** and **preprod-only** mutations (prod→preprod copy, preprod redeploy/reseed, preprod test runs, a preprod-trigger push to SOURCE when no `workflow_dispatch` exists).
   - *Phase 6 go* (plus the tier-3 double confirm in Phase R): required for the merge, any push to TARGET or to a prod-deploying branch/tag, any prod write, and any DB restore. Nothing in these categories happens before it.
   - Anything outside both lists needs its own explicit confirmation. Mutations run single-threaded; only reads, analysis and independent tests run in parallel.
4. **Reuse the project's native scripts** (backup / restore / prod→preprod copy / deploy / seed). Never reimplement what the repo ships.
5. **Fan out subagents** for independent read, analysis and test work. Follow the project's orchestration section if present; otherwise: `haiku-standard` for detection probes, per-subsystem diff reads and independent suites; `opus-standard` for migration and risk analysis; fall back to the Agent tool `model` parameter if a type is missing. Cap at about 8 concurrent agents and batch huge diffs (about 50 files or 3000 changed lines per agent). Mutating steps stay single-threaded.

## Tooling and fallbacks

- **CLIs** (probed in Phase 0): `git`, `gh`, `docker`/`docker compose`, `ssh`, `curl` + `jq`, `psql`, `rclone`, `node`/`npx`, `python` + Playwright, a secret scanner (`gitleaks`/`trufflehog`/`detect-secrets` or the repo's `secret-scan` hook), push rights, free disk for dumps.
- **Degradations (always reported in the recap):** no `TaskCreate`/`TaskUpdate` → keep the phase checklist in the journal; no `AskUserQuestion` → ask in plain text and wait; no `ScheduleWakeup`/`Monitor` → poll with `run_in_background` and bounded `sleep`/`curl` loops; no claude-in-chrome MCP → `curl` smoke only and report "no visual smoke (blind spot)".
- Prod browser smoke covers **public, unauthenticated pages only**. A prod test credential may be supplied interactively, never persisted.

## Configuration (resolution order: command argument > `.claude/safe-merge.yml` > plugin option > recommended default)

| Key | Default | Effect |
|---|---|---|
| `${user_config.safe_merge_backups_auto_run}` | `true` | `true`: run fully covered native backups without further asking. `false`: Phase 3 builds a backup plan and executes it only once validated (shown in the Phase 0 confirmation). |
| `${user_config.safe_merge_offpeak_preference}` | `recommend` | `recommend`: advise an off-peak window in the recap. `require`: treat in-flight prod jobs or peak hours as a no-go unless the human overrides at the gate. `ignore`: skip the advice. |
| `${user_config.safe_merge_changelog_review}` | `true` | `true`: the human reviews the CHANGELOG entry (done inside the Phase 6 recap, not as a separate stop). `false`: commit it as drafted after the go. |
| `${user_config.safe_merge_surveillance_minutes}` | `15` | Length of the Phase 7 surveillance window. |
| `${user_config.safe_merge_smoke_depth}` | `standard` | `basic`: health + version only. `standard`: plus login/media/queue checks from `health_checks`. `deep`: plus authenticated client flows when the diff touches build args or media. |

# Procedure

Run the phases in order. Register them with `TaskCreate` and update them as you go. Placeholders are UPPERCASE (`SOURCE_BRANCH`, `TARGET_BRANCH`, `PROD_URL`, `PREPROD_URL`, `VERSION_ENDPOINT`). A phase failing a hard rule **stops the run** with a clear report.

**Mode routing:**
- `revert` → **Phase R**.
- `--dry-run` → Phases 0 → 2 (Phase 0 without the authorization question), then the Phase 6 recap, and stop. No writes, triggers, backups, commits or merge.
- Bare invocation → full run; print the auto-selected mode instead of asking.

## Phase 0 — Preflight, profiling, preparation authorization

Detection details: [references/detection.md](references/detection.md). Config and journal formats: [references/config-schema.md](references/config-schema.md). Spawn parallel probes for the independent detections.

1. **Resume.** If `.claude/safe-merge/journal.md` shows an in-progress run updated in the last 24 h (so backups and test results are still fresh) and SOURCE/TARGET SHAs are unchanged, resume at the last completed phase and say so. Otherwise start over and archive the old journal.
2. **Config.** Read `.claude/safe-merge.yml` if present and re-run detection regardless. Structural drift: update and report. Drift on a human-authored `quirks`/override field: keep the stored value and report the difference. Config holds env-var **names**, never values.
3. **Project type** (web-service / library / CLI / mobile / static-site / monorepo); it drives the Phase 2 risk taxonomy and the Phase 6 narrative.
4. **Resolve SOURCE/TARGET** per detection.md §2. Low confidence on the pair is a blocking case: ask.
5. **Deploy trigger**, broad detection (detection.md §3); `unknown` is a first-class state and the merge is then treated as production-impacting. Confirm TARGET is prod's real source of truth.
6. **Harvest test/build commands from CI**, detect the package manager, classify each command safe-to-run vs side-effecting (never auto-run a side-effecting one).
7. **Backups / preprod / DB / migrations / changelog format and language / `health_checks`** (the project's post-deploy checks, see config-schema.md).
8. **Capability preflight.** Test each capability along the path the project actually uses it (e.g. `ssh HOST 'docker exec <db_container> psql --version'`, not a host-local `command -v`); a host-local absence is irrelevant when the tool only runs in a container or on the prod host. Stop with a precise "install/authenticate X" list only for capabilities genuinely missing on their real path.
9. **Preparation authorization (the single early stop).** Present the detected profile, the planned preparation actions (backups, prod→preprod copy, preprod redeploy/reseed, test runs), the estimated time, and ask once to authorize preparation. When detection confidence is high there is no other early confirmation; low confidence on the branch pair or project type is asked in the same prompt. Write/refresh `.claude/safe-merge.yml` and start the journal. Without the authorization, run read-only phases only and stop before Phase 3.

## Phase 1 — Git safety and topology

1. `git fetch --all --prune`.
2. Both branches in sync with their upstreams (`git rev-list --left-right --count SOURCE_BRANCH...@{u}`): no unpushed or unpulled commits. Out of sync → stop and report.
3. Outcomes. A repo promoting with `git merge --no-ff` leaves merge commits on TARGET that SOURCE lacks, so `git log SOURCE..TARGET` is routinely non-empty and `git diff SOURCE..TARGET` is never a benign test. Decide on **non-merge commits**:
   - `git rev-list --count --no-merges SOURCE_BRANCH..TARGET_BRANCH` == 0 → proceed.
   - \> 0 → real work on TARGET was not back-merged: offer to back-merge TARGET→SOURCE first and re-run (expected on maintenance/backport lines).
   - `git rev-list --count TARGET_BRANCH..SOURCE_BRANCH` == 0 → "already up to date", clean exit.
   - Real unique commits on both sides → warn of a likely conflict in Phase 7.
4. Working tree clean (`git status --porcelain` empty).
5. Record the pre-merge TARGET SHA (`git rev-parse TARGET_BRANCH`) for the revert procedure.

## Phase 2 — Diff analysis and risk taxonomy

Fan out per subsystem (principle 5). Reference: [references/risky-migrations.md](references/risky-migrations.md).

1. **Collect** the change set:
   ```bash
   git log --oneline TARGET_BRANCH..SOURCE_BRANCH
   git shortlog -sn TARGET_BRANCH..SOURCE_BRANCH
   git diff --name-status TARGET_BRANCH..SOURCE_BRANCH
   git diff --shortstat TARGET_BRANCH..SOURCE_BRANCH
   git diff --dirstat=files,0 TARGET_BRANCH..SOURCE_BRANCH
   git log --oneline --merges TARGET_BRANCH..SOURCE_BRANCH
   ```
   Squash-merge repos: add `gh pr list --state merged --base SOURCE_BRANCH --json number,title,labels,mergedAt`.
2. **Categorize** by project type (Features / Fixes / Refactors / Perf / Infra & config / DB migrations / Dependencies / Docs / Tests / semver-affecting API for libraries). Use Conventional Commits if present, otherwise diff content and PR titles/labels, never bare "wip" messages.
3. **Secret scan — hard stop, before any backup.** Scan `TARGET_BRANCH..SOURCE_BRANCH` and flag sensitive paths (`**/.env`, `secrets/**`, `cookies/**`, key/pem files). Any hit stops the run: purge it from history first. No scanner available → offer to install one or run the repo's hook; failing that, grep sensitive paths and high-entropy strings and report "no secret scanner — reduced coverage (blind spot)".
4. **Migration analysis** on the four axes of risky-migrations.md. Production row counts are read-only queries (command shown; covered by the preparation authorization). Cross the estimated duration with `statement_timeout`.
5. **Config surface.** Diff `settings*`, `.env.example`, `docker-compose*` (including `build.args` baked at build time), `Dockerfile*`, `nginx/`, `infra/`, lockfiles.
6. **New env keys.** Extract keys newly referenced by the diff and cross-check them against the real prod env (usually outside git; read-only, command shown) and against the preprod↔prod env delta.
7. **Manual-step flags.** Compose/infra or database-server settings changes (e.g. a Postgres `ALTER SYSTEM`) that the deploy script will not apply.
8. **Media/storage.** Any object-storage or media-backend setting change is its own risk category.
9. **Output** the change list ranked biggest to smallest.

## Phase 3 — Backups (blocking; needs the Phase 0 preparation authorization)

1. **Decision tree.** No persistent state → skip cleanly. State exists but no backup mechanism detected → loud blocker (danger, not "nothing to do").
2. **Map coverage and blind spots:** prod DB, preprod DB, media/object storage, `.env`/secrets, volumes, cache/queue stores. Note what cannot be backed up or restored.
3. **Run.** Full native coverage and `safe_merge_backups_auto_run` true → run the native backups for prod and preprod (managed DB → provider snapshot API) and verify success as a hard gate (e.g. the log's checksum line). Otherwise propose the best-fit plan, iterate until validated, then execute. Add a dedicated backup at a controlled instant even if the deploy script also backs up.
4. **Snapshot non-DB rollback state:** prod env var **names + hashes** (never values into git), compose/infra config, media backend, feature flags.
5. **Verify the rollback is armed:** the previous-release artifact (e.g. a `:rollback` image) exists and matches the current prod SHA, and the new backup's checksum is valid. If not, say so before the gate.
6. Record paths, checksums and blind spots in the journal and the rollback file.

## Phase 4 — Test battery (preparation authorization; never target production)

Parallelize independent suites.

1. **Static / unit / build / arch** from the CI-harvested commands. Force CI mode (`CI=true`, `--run`, `--watchAll=false`), start required services, never run a side-effecting command. Any red → stop, fix on SOURCE, re-run.
2. **Migration rehearsal on a clone of production data** (only if the batch has migrations; the highest-value check):
   - Backups of both DBs exist (Phase 3).
   - Copy prod → preprod with the project's native script — **direction prod→preprod only, never the reverse**. Preprod must run SOURCE's code so the new migrations are the ones exercised; the script's trailing `migrate` is the rehearsal.
   - Measure wall-clock duration (the downtime/lock estimate), success, `statement_timeout` overruns, integrity (row counts preserved, no silent 0/NULL backfill).
   - No copy script → restore the prod dump into a throwaway ephemeral DB and migrate there.
3. **E2E deep on preprod.**
   - If `.claude/full-test.yml` exists, **delegate to `/full-test`** (it redeploys, waits for the SHA, reseeds, runs the suites) and consume its per-suite report. Otherwise:
   - Trigger the preprod deploy with `gh workflow run` (`workflow_dispatch`); this avoids empty commits and `paths:` filters. If only a push trigger exists, push one real commit (e.g. the finalized CHANGELOG) to SOURCE, never repeated empty commits.
   - Wait for the deploy; verify `PREPROD_URL` `VERSION_ENDPOINT` == SOURCE SHA. Reseed preprod with the project's seed command. Run the deep suite (its own gating flag, e.g. `E2E_DEEP=1`).
   - Re-verify the preprod SHA immediately before and after the suite; the slot is often shared, and a stolen slot invalidates the results (re-run). Never point E2E at prod.
4. No preprod → E2E is "NOT COVERED (blind spot)". No tests at all → "zero coverage".

## Phase 5 — CHANGELOG (prepared now, committed only after the go)

Rules, tooling detection, language and entry structure: [references/changelog-format.md](references/changelog-format.md) (append-only, newest on top; defer to any tool that owns the changelog).

1. Write a non-technical entry from the Phase 2 ranked list, with no vulnerability details.
2. Keep it as a draft file or in the journal; **do not commit it before the Phase 6 go** (a no-go would leave an orphan release entry). It is committed in Phase 7.
3. Review: with `${user_config.safe_merge_changelog_review}` true the draft is shown inside the Phase 6 recap and the human's edits applied at the go.

## Phase 6 — Recap and hard gate

Present in this order:

- **(A) What changes** — the ranked list with risk flags: migration reversibility and estimated duration/downtime; new env keys missing from prod; manual steps; media/storage changes; secret-scan status.
- **(B) What secured the merge** — backups (what/where/checksums); every test result including migration-rehearsal timing; "rollback armed" status; every accepted blind spot; any degraded tool (see fallbacks); the CHANGELOG draft.
- **Live prod state probe** taken just before the gate — active background jobs, in-flight uploads, live sessions, load, time of day — applying `${user_config.safe_merge_offpeak_preference}`.
- **(C) Go/no-go verdict**, explicit and argued.
- **(D) What will happen on merge**, conditional on `deploy_trigger` (auto-deploy / tag-or-manual / unknown, framed conservatively), with estimated downtime including migration duration, and stated plainly: **the automatic rollback restores CODE only, NOT the database; a destructive/irreversible migration's only recovery is a backup restore with up to RPO_X of data loss.** Name the real user impact.
- **HARD GATE:** ask for explicit confirmation (`AskUserQuestion`, or plain text). Anything other than a clear "go" → stop; nothing is merged.

## Phase 6.5 — Prepare the revert procedure (before the push)

Write `.claude/safe-merge/rollback-<TIMESTAMP>.md` from [references/rollback-procedure.md](references/rollback-procedure.md): pre-merge TARGET SHA, rollback-artifact status, backup paths and checksums, migration reversibility verdict and `db_restore_required`, config snapshot, exact commands for each recovery tier. It must exist before the merge so `revert` works in a fresh session.

## Phase 7 — Execute the merge (only after "go")

1. Re-assert that the SHA tested still equals the SHA about to merge; re-fetch; handle a non-fast-forward push or a conflict with a clean abort path.
2. `git checkout TARGET_BRANCH` → `git merge --no-ff SOURCE_BRANCH -m "merge(<target-branch>): <summary>"` (substitute the real target branch name and a one-line summary) → commit the finalized CHANGELOG → `git push origin TARGET_BRANCH`. **Never rewrite pushed history.** Preprod-trigger commits are avoided by using `workflow_dispatch`; if one was pushed to SOURCE it stays; only unpushed local commits may be cleaned.
3. Monitor the deploy with the project's native tool (e.g. `gh run watch <id> --interval 20 --exit-status`).
4. **Surveillance window** of `${user_config.safe_merge_surveillance_minutes}` minutes. The human is the monitor (there is usually no external alerting): say so. Run the project's `health_checks` (config-schema.md), then per `${user_config.safe_merge_smoke_depth}`: a real login, a media read, queue drain, disk headroom, and a browser-MCP smoke of public prod pages. If the diff touched frontend build args, drive an authenticated client flow (a green health endpoint can hide a broken app, e.g. a mixed-content failure). If media was touched, read a real asset and check signing-secret coherence.
5. Anything broken → **Phase R**.

## Phase R — Revert (`/safe-merge revert`, or "it's broken")

Load the most recent `.claude/safe-merge/rollback-<TIMESTAMP>.md` and choose the **lowest tier that fully restores service** (details: [references/rollback-procedure.md](references/rollback-procedure.md)):

1. **Image/code rollback** if the deploy failed or the break is code-only.
2. **`git revert` of the merge commit + push** for a functional bug the health check missed.
3. **DB restore from the pre-merge backup** — last resort, only if a destructive/irreversible migration mutated data. Irreversible with RPO data loss: **double-confirm**.

Confirm the chosen tier, execute it (the revert push and any restore are prod writes: the revert request plus the confirmation here is the gate), then verify the return to the pre-merge state: health ok, `VERSION_ENDPOINT` back to the pre-merge SHA, at-risk table counts consistent. Write a short incident note.
