# `.claude/full-test.yml` schema

## Contents

- Secrets policy
- Layout
- Field notes
- Freshness / drift

Per-project config, owned by this skill alone: it never reads another skill's config. Single exception: the project's orchestration section in its base doc (CLAUDE.md / AGENTS.md) is read for agent-type policy; `.claude/orchestration.yml` is not. **Auto-detection refreshes the structural fields on every run; human-authored `quirks`/overrides are never overwritten**: keep the stored value and report the drift diff. Its purpose: capture the singular, non-guessable specifics of a project, and make the guardrails checkable.

## Secrets policy (non-negotiable)

- **Never store secret values.** Env-var **names** only (`E2E_SEED_PASSWORD`, not its value).
- No tokens, passwords, private keys, or `.env` contents. If the project itself hardcodes a test password somewhere, that's the project's choice — do not copy it in here.
- Structural, shareable fields → committed. Machine-specific paths, hosts, IPs → the `local:` block (or a gitignored `*.local.yml`).
- On write, **lint the committed portion** and reject anything shaped like a token or credential.

## Layout

```yaml
# --- committed: structural, shareable ---
version: 1
detected_at: { sha: <HEAD sha at detection> }

# The guardrail data. Everything here is compared against before any write or test.
prod:
  branch: main                   # THE prod-deploying ref. Never assume; detect or ask.
  url: https://example.com       # forbidden as a test target
  ref_pattern: null              # set if prod deploys from a tag pattern instead (e.g. "v*")

preprod:
  url: https://preprod.example.com
  rule: "any branch other than `main`"     # how a branch reaches preprod, in words
  shared_slot: true                        # true → a concurrent push can steal it mid-run
  cancel_in_progress: true                 # true → your deploy can be cancelled by another push
  allowed_test_hosts: [preprod.example.com, localhost, 127.0.0.1]

version_endpoint:
  path: /api/health/
  field: version                 # JSON field carrying the running SHA
  compare: prefix                # served == full_sha[:len(served)] — NEVER == `git rev-parse --short HEAD`
  authenticated: false           # true → needs a bearer token (name it in local.env_var_names)

follow:                            # Phase 7 watchdog — always on, every mode
  tick_minutes: 5                  # progress report + SHA re-check interval
  stall_after_ticks: 3             # nothing observable advanced for N consecutive ticks → investigate, act (cancel+retry once, then failed-infrastructure)

resources:                         # Phase 7 host resource watch — sampled at each tick when host is reachable
  host: local                      # local | the ssh host that runs preprod/the suites
  disk_max_pct: 85                 # above → run clean commands, re-sample, else report environment risk
  ram_max_pct: 90
  clean:                           # SAFE commands only, project-specific — the skill never improvises beyond this list
    - "docker builder prune -af"
    - "docker image prune -f"
  never: "no global prunes on shared hosts; never delete run artifacts or backups within keep_last"

deploy:
  workflow: deploy.yml
  dispatchable: true             # true → `gh workflow run` beats an empty commit
  wait: "gh run watch <id> --interval 20 --exit-status"
  gate: "poll version_endpoint until served SHA == TARGET_SHA (bounded timeout)"
  typical_duration: "~4 min"

backup:                            # DB backup — required by fix-loop before every reseed, every iteration
  command: "<the project's native dump/backup command, verbatim>"
  route: ssh-docker-exec           # local | ssh-docker-exec | workflow
  target_proof: "<same proof requirement as reseed.target_proof>"
  destination: "<where the dump lands, e.g. /var/backups/myapp-preprod/>"
  keep_last: 5                     # loop-dump rotation; older dumps deleted

fix_loop:
  max_iterations: 20               # integer or none — total iteration cap
  no_progress_limit: 5             # integer or none — identical failure signature N consecutive iterations
  local_checks:                    # fast pre-push validation, run after every fix batch
    - "<lint command>"
    - "<fast unit-test command>"
  retry_failed_once: true          # re-run a failed suite once before triage (flaky/slowness filter)
  watchdog:                        # mandatory self-resume cron (CronCreate) — cannot be disabled, only tuned
    interval_minutes: 10           # tick period of the watchdog cron
    stall_after_cron_ticks: 2      # no heartbeat change for N consecutive 10-min cron ticks ⇒ presumed stalled ⇒ resume (distinct from follow.stall_after_ticks)
    max_resumes: 5                 # total auto-resumes per loop; beyond ⇒ abort with report, human needed
  agents:                          # difficulty → subagent type; fallback matrix, the project's orchestration section wins if present
    trivial: haiku-standard        # haiku-quick for purely mechanical edits
    standard: sonnet-standard
    complex: opus-standard
    critical: opus-standard        # opus-deep only on explicit user request or after opus-standard failed on the same failure (see references/fix-loop.md)

reseed:
  command: "<the project's native seed command, verbatim>"
  route: ssh-docker-exec         # local | ssh-docker-exec | workflow
  target_proof: "runs on the preprod host, against compose project `myapp-preprod`"
  mode_note: "full --reset required; the idempotent seed lets state accumulate"
  scope: "only deletes users under @test.local — cannot touch real accounts"
  already_done_by: [e2e-python]  # suites that reseed themselves → don't double-reseed
  env_var_names: [E2E_SEED_PASSWORD]

# Every suite that targets the DEPLOYED preprod. Built by detection; the Phase 6 menu.
suites:
  - id: e2e-python
    label: "E2E Playwright Python"
    route: workflow              # workflow | local | ssh
    command: 'gh workflow run "E2E Python" --ref <branch>'
    local_fallback: "bash scripts/tests/test.sh <PREPROD_URL>"
    mutates: true                # → serialized
    reseeds_itself: true
    cost: moderate               # light | moderate | costly
    gating: null
    logs: "scripts/tests/logs/"
    own_guard: "test.sh + config.py refuse non-preprod URLs — never bypass"
  - id: e2e-python-deep
    label: "E2E Playwright Python — deep"
    route: workflow
    command: 'gh workflow run "E2E Python" --ref <branch>   # + E2E_DEEP=1'
    mutates: true
    cost: costly                 # → excluded from "everything", own confirmation
    gating: "E2E_DEEP=1"
    note: "real transcodes; saturates a shared VPS"

# --- local: machine-specific / sensitive (gitignore this block or a *.local.yml) ---
local:
  preprod_ssh_host: "ubuntu@<ip>"
  prod_ssh_host: "ubuntu@<ip>"           # recorded ONLY so the skill can recognise and avoid it
  runner_path: "/home/<user>/<project>"
  env_var_names: [E2E_SEED_PASSWORD, METRICS_TOKEN]   # NAMES only, never values

# --- human-authored: the non-guessable specifics (never auto-overwritten) ---
quirks:
  - "preprod is a single shared slot; a bot push can steal it mid-run"
  - "E2E_DEEP off ⇒ N SKIP by-design — not failures. Realistic target: 0 FAIL"
```

## Field notes

**`prod.branch` is the load-bearing field.** G1 compares against it before every write. If detection can't establish it, the config must not be written with a guess — leave it null and let Phase 0 hard-stop until a human fills it in. A wrong value here is the one bug in this skill that reaches production.

**`preprod.allowed_test_hosts` is an allowlist, deliberately.** A denylist of prod hosts says yes to everything you forgot.

**`version_endpoint.compare: prefix`** is not a style preference. Short-SHA length is repo-dependent (`core.abbrev=auto`), so the same commit can serve 7 characters from a CI checkout and abbreviate to 8 in a full local clone. Any comparison that isn't a prefix match fails on every run *and* misreports the cause as "the deploy never landed".

**`suites[].mutates`** drives Phase 6 scheduling. When unsure, mark `true`: serializing a read-only suite costs minutes; parallelizing a mutating one corrupts a run and the corruption looks like a product bug.

**`suites[].cost: costly`** is a contract: excluded from "everything", own confirmation, real cost stated.

**`backup.target_proof`** obeys the same G3 logic as the reseed: no proof ⇒ no backup ⇒ **no reseed** ⇒ blind spot. A failed backup also blocks the reseed — the safety net must exist before the destructive step runs.

**`fix_loop.agents`** names subagent types that must be among those the Agent tool offers. When one is missing, fix-loop falls back to the Agent tool's `model` parameter with the effort stated in the prompt; it never silently downgrades the difficulty class.

**`fix_loop.max_iterations` / `no_progress_limit`** each accept `none` to disable that limit independently. Both at `none` = unbounded loop, valid only as an explicit user choice.

**`reseed.target_proof`** must be a sentence a human can check. "It's the preprod command" is not proof; "runs on a host that has no prod containers" is. If you cannot write this sentence honestly, the reseed does not run (guardrail G3).

**`prod_ssh_host` in `local:`** is recorded so the skill can *recognise* prod and refuse it — not so it can reach it. No command in this skill targets it.

## Freshness / drift

- Each run, diff detected vs stored. **Structural drift** (a suite added, a URL changed) → update and report it. **Drift touching `quirks` or a guardrail field** (`prod.branch`, `preprod.url`, `allowed_test_hosts`) → keep the stored value, report the diff, and use the stored value for the guards. A guardrail that silently rewrites itself is not a guardrail.
- Recommend committing the structural block and gitignoring `local:`, so several machines don't fight over paths and hosts.
