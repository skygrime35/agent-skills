# `.claude/agents-md.yml` schema

Contents:
- Secrets policy
- Layout
- Field rules

Per-project config, owned by this skill alone (it never reads another skill's config). **Detection refreshes the structural fields on every run; human-authored `quirks` and overrides are never silently overwritten** (keep them and report the drift diff).

## Secrets policy (non-negotiable)

- **Never store secret values.** Environment variable **names** only.
- No tokens, passwords, private keys, or `.env` contents.
- Machine-specific paths, hosts and IPs go under `local:` (or a gitignored `*.local.yml`); the rest is committed.
- Before writing, lint the committed portion and reject anything shaped like a credential.

## Layout

```yaml
version: 1                       # schema version; bump rules in Field rules
policy:                          # run policies; command argument > this file > plugin option > recommended default
  language: en                   # doc language
  tier: auto                     # auto | 1 | 2 | 3
  install_guardrail_scripts: true
  guardrail_scripts_path: .claude/agents-md/   # this field > plugin option user_config.agents_md_guardrail_scripts_path > .claude/agents-md/
  commit_convention: detect      # detect | enforce | skip
archives:                        # dated records exempt from dead-reference fixes
  paths: [errors/, adr/, postmortems/]
  policy: tolerate               # tolerate | annotate | fix
ci_replay_excludes: [release, nightly]   # workflow jobs deliberately absent from the doc's local CI-replay list
detected_at:
  sha: <HEAD sha at detection>
  date: <ISO date>

tier: 3                          # 1 | 2 | 3, confirmed by the human
language:
  written: en                    # what the docs are written in
  detected: fr                   # what the repo's own prose uses
  conflict: "AGENTS.md guardrail requires French for all documentation"
  resolution: "repository rule applied (French) on 2026-07-29"   # null if no conflict

structure:                       # every file this skill generated or now owns
  root: AGENTS.md
  pointer: CLAUDE.md
  index: AGENTS/INDEX.md
  domains:
    - {path: backend, file: backend/AGENTS.md, manifest: backend/pyproject.toml}
    - {path: frontend, file: frontend/AGENTS.md, manifest: frontend/package.json}
  knowledge: [AGENTS/ARCHITECTURE.md, AGENTS/COMMANDS.md, AGENTS/TESTING.md]
  adr: AGENTS/adr/
  debt_register: TODO.md

commands:                        # ONLY entries actually executed during a run
  test:      {cmd: "docker compose exec backend pytest -v", verified: true,  source: ci.yml}
  lint:      {cmd: "ruff check apps/billing",          verified: true,  source: ci.yml}
  typecheck: {cmd: "mypy apps/a apps/b config",              verified: true,  source: ci.yml}
  build:     {cmd: "npx next build",                         verified: false, note: "slow, not run"}
  privilege: {docker_needs_sudo: false, proof: "docker ps exits 0 unprivileged"}

environments:
  prod_branch: main
  preprod_rule: "any branch other than main"
  platform: github-actions
  evidence: ".github/workflows/deploy.yml job `deploy`, runs-on conditional on github.ref_name"

commit_convention:
  enforced: true
  format: conventional
  scopes: [billing, users, ui, infra]

guardrail_scripts:               # what was installed and whether it is wired
  - {name: check_no_todo,        path: .claude/agents-md/check_no_todo.py,        wired: false, marker_version: "1.4.0"}   # version stamped at copy time
  - {name: check_monolith,       path: .claude/agents-md/check_monolith.py,       wired: false,
     thresholds: {file: 400, function: 75, class: 200, component: 150}}
  - {name: check_forbidden_chars, path: .claude/agents-md/check_forbidden_chars.py, wired: false,
     scope: [frontend/src], chars: ["—", "–"]}

budget:                          # measured at last run
  instructions: 138
  threshold: "frontier models follow roughly 150-200 instructions before adherence degrades; the harness already spends about 50 (as of 2026-10)"   # copied from the skill's structure.md "Instruction budget" section; refresh when re-checked
  always_loaded_chars: 24391

knowledge_graph:                 # detected, never generated
  present: true
  path: graphify-out/
  built_at_commit: 1a2b3c4d
  drift_commits: 250             # vs HEAD at detection
  usable: false                  # drift too large to trust

quirks:                          # HUMAN-AUTHORED. Never rewritten by detection.
  - "Preprod runs pytest inside the live container: a cache.clear() flushes the real Redis."

local:                           # machine-specific, gitignore candidate
  env_var_names: [EXAMPLE_API_KEY_NAME]
```

## Field rules

**`version`**: a bump means the layout changed. On read of an older version, migrate in memory, show the diff in the plan confirmation, and write the new version only with the batch; never drop unknown or human-authored fields.

**`commands`**: an entry with `verified: false` must carry a `note` saying why. A command that failed is never written into the documentation as if it worked.

**`language.conflict`**: populated whenever the repository states a documentation language rule that differs from the default. Never resolve it silently; `resolution` records the rule applied and when.

**`guardrail_scripts[].marker_version`**: plugin version in the copy's `dev-skills: agents-md <version>` marker, refreshed on every copy or replacement.

**`guardrail_scripts[].wired`**: `false` until the human confirms the CI block was added. The skill proposes, it never wires.

**`budget`**: recomputed on every audit and sync. A rise past the threshold is reported, not accepted.

**`archives`**: `policy` resolves as `--archives` argument > this field > plugin option `user_config.agents_md_archives_policy` > `tolerate`. `tolerate`: dead references inside `paths` are one P3 info finding with the count. `annotate`: `sync` rewrites only the reference, as "`new` (formerly `old`)", never the record body. `fix`: `sync` replaces the reference. Human-authored: never rewritten by detection.

**`ci_replay_excludes`**: job ids (or workflow names) that P3.4 skips when comparing the documented CI-replay list with the workflows. Human-authored; keep on drift.

**`quirks`**: the only human-authored block. On drift, keep it and report the diff. Overwriting it destroys exactly the knowledge that is hardest to reacquire.

**`knowledge_graph.usable`**: `false` when drift makes it more expensive than a plain grep. Report it, and point at the refresh command.
