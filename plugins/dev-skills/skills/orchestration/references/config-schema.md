# `.claude/orchestration.yml` schema

Contents: Plugin options | Secrets policy | Layout | Field rules

Per-project config, owned by this skill alone (it never writes another skill's config; it *reads* `.claude/agents-md.yml` when present). **Detection refreshes the structural fields on every run; human-authored `quirks` and recorded `policy` decisions are never silently overwritten** (keep them, show the drift diff in the report).

## Plugin options (machine-wide defaults)

Machine-wide defaults are plugin options, changed with `/config`, not a file. Each `policy:` field below has an option `orchestration_<field>` (`agents.location` is `orchestration_agents_location`; `orchestration_report_language` has no policy field). Resolution order for every policy answer: argument, project `policy:`, plugin option, the recommended option (interview.md, Autopilot). A project's recorded policy wins over the options; to bring a project back to the options, delete the field from its config.

## Secrets policy (non-negotiable)

- **Never store secret values.** Environment variable **names** only.
- No tokens, passwords, private keys, or `.env` contents.
- Machine-specific facts (installed agent types, available models, statusline presence) go under `local:` (or a gitignored `orchestration.local.yml`); the rest is committed.
- Before writing, lint the committed portion and reject anything shaped like a credential.

## Layout

```yaml
version: 1
detected_at:
  sha: <HEAD sha at detection>
  date: <ISO date>

base_doc:                        # where the doctrine lives (probe D1/D2)
  file: AGENTS.md
  pointer: CLAUDE.md             # null if no pointer pattern
  section_heading: "### 5. Orchestration multi-agents"
  section_span: {start: 42, end: 95}
  language: fr
  evidence: "CLAUDE.md contains @AGENTS.md"

agents_md:                       # the sibling skill this one must never contradict
  config: .claude/agents-md.yml  # null if absent (blind spot, budget computed locally)
  budget:
    total: 138                   # normative statements across always-loaded files
    orchestration_share: 22      # this skill's section alone
    threshold: see-agents-md-skill

agents:                          # subagent type definitions
  location: global               # global | project, human decision at init (Q0.1)
  path: ~/.claude/agents/
  fallback_documented: true      # doctrine carries the machine-absent fallback
  types:
    - {name: haiku-quick,     model: haiku,  effort: low,    maxTurns: 130,  color: green,  verified: true}
    - {name: haiku-standard,  model: haiku,  effort: medium, maxTurns: 160,  color: cyan,   verified: true}
    - {name: sonnet-standard, model: sonnet, effort: medium, maxTurns: 180,  color: blue,   verified: true}
    - {name: opus-standard,   model: opus,   effort: medium, maxTurns: 220, color: yellow, verified: true}
    - {name: opus-deep,       model: opus,   effort: high,   maxTurns: 250, color: red,    verified: true}
  overrides:                     # built-in replacements (Q1.4)
    - {name: Explore, model: haiku, effort: medium, verified: true}

doctrine:
  blocks: [ladder, escalation, delegation, briefing, parallelism-isolation, ask-before-dispatch, session-naming, reporting]
  prohibition_markers: ["git stash", "git add -A", "git checkout", "git reset", "jamais", "obligatoire"]
  prohibitions: 6                # non-regression baseline for sync

checks:
  - {name: check_agent_refs, path: scripts/check_agent_refs.py, wired: false}

policy:                          # recorded interview answers. A recorded decision is never re-asked.
  cost_posture: cheapest-capable           # cheapest-capable | balanced | capability-first (Q1.2)
  deep_gate: explicit-or-after-failure     # explicit-or-after-failure | orchestrator-judgment (Q1.5)
  builtin_overrides: [explore, subagent-model-env]   # subset of these two (Q1.4)
  matrix: five-types                       # five-types | three-types | none (Q1.3)
  delegation_threshold: exploration-iteration-or-multi-file
  delegation_rationale: true               # Q2.2
  delegation_fallback: do-it-yourself-and-say-so
  report_style: high-density               # high-density | free (Q2.4)
  shared_tree_bans: ["git stash", "git add -A", "git checkout", "git reset"]   # Q3.3
  cite_incident: true                      # Q3.4
  check_script_path: auto                  # auto | <path> (Q4.4)
  parallelism: default-on                  # default-on | on-request | never
  isolation: escalating                    # escalating | worktrees-always | disjoint-only
  ask_before_dispatch: freely
  session_naming: badge-with-fallback      # badge-with-fallback | prefix | auto (decided by probe D6)
  language_resolution: null                # populated only on conflict, with date

quirks: []                       # HUMAN-AUTHORED. Never rewritten by detection.

local:                           # machine-specific, gitignore candidate
  models_available: [fable, opus, sonnet, haiku]
  models_verified_at: 2026-10-07 # date references/models.md was last checked against the official pages (D11)
  subagent_model_env: sonnet     # CLAUDE_CODE_SUBAGENT_MODEL as found in settings.json; null if unset
  statusline: true               # ~/.claude/subagent-statusline.sh exists
  global_types_present: [haiku-quick, haiku-standard, sonnet-standard, opus-standard, opus-deep, Explore]
  delegation_capable: true       # harness exposes the Agent tool; unknown => blind spot
```

## Field rules

**`base_doc.section_span`**: the only lines this skill may ever edit. Refreshed on every run; if the heading moved or vanished, that is a finding, not a silent re-anchor.

**`agents.types[].verified`**: `true` only when the file was stat'd and its frontmatter parsed during this run. An entry with `verified: false` must carry a `note` saying why. A type that failed to parse is never cited by the doctrine as if it worked.

**`doctrine.prohibitions`** and **`prohibition_markers`**: the non-regression baseline. Any sync batch touching the doctrine recounts and re-greps against these; a drop without an explicitly approved merge aborts the batch.

**`checks[].wired`**: `false` until the human confirms the CI or pre-commit block was added. The skill proposes, it never wires.

**`policy`**: interview answers become fields here. On the next run they are facts, not questions. Changing a policy is done by answering differently in a `sync` run, which shows the old value first.

**`agents.types[].maxTurns`**: the turn cap written into the file. Recalibrated from probe D12 when measured runs routinely hit it (too low) or sit far under it (no protection).

**`agents.overrides`**: built-in agents replaced by a same-named file (Q1.4). Checked like any type: stat'd, parsed, model available.

**`policy.deep_gate`**: when `{TOP}-deep` may run. Any type raised to xhigh or max is recorded in `quirks` with the reason; otherwise it is finding O8.1.

**`policy.language_resolution`**: populated whenever the base doc's language, a project language rule, and `--lang` disagree. Never resolve silently; record the human's decision and the date.

**`quirks`**: the only human-authored block. On drift, keep it and report the diff. Overwriting it destroys exactly the knowledge that is hardest to reacquire.

**`local`**: everything in it describes THIS machine, not the project. A repo cloned elsewhere gets a fresh `local:` from detection, which is precisely why the doctrine must carry its fallbacks (`fallback_documented: true`).
