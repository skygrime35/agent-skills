# Implementation orchestration: planned in the spec, validated at Checkpoint 1, executed in Phase 3

The implementation is planned as an orchestration table in `SPECS.md`, shown inside the Checkpoint 1 plan, then executed as written. Follow the **orchestration skill's matrix** and, if the project already has one, **the project's orchestration section**; this file only defines the table format. If a dedicated agent type is missing (detected in Phase 0), apply `${user_config.new_project_agents_fallback}`: `model-parameter` = the Agent tool's `model` parameter, `main-loop` = run the package inline.

## Agent types by role

- `haiku-standard`: default for briefed implementation (boilerplate, config, fixtures, standard features with a clear brief).
- `haiku-quick`: mechanical, located edits, search, extraction.
- `sonnet-standard`: design still unsettled after briefing.
- `opus-standard`: real reasoning (data model, auth, anything touching money or sensitive data).
- `opus-deep`: only on the user's explicit request or after `opus-standard` failed on the same package.

## The orchestration table (goes into SPECS.md)

| # | Work package | Files / area | Agent type | Depends on | Wave |
|---|--------------|--------------|------------|------------|------|
| 0 | Scaffold + shared contracts (types, schema, API shapes) | repo root | main loop or sonnet-standard | none | 0 |
| 1 | ... | ... | ... | ... | 1 |

Rules:

1. **Decompose along module boundaries** so file sets are disjoint. **Isolation is the condition of parallelism, not an optional precaution**: agents run concurrently only on disjoint enumerated file sets or in isolated git worktrees (worktrees when overlap is unavoidable); without one of them, the packages run one at a time. Two agents must never write the same files. Trivial scope: a one-package table run by the main loop.
2. **Wave 0 = scaffold + shared contracts**, single agent, never parallel.
3. **Waves are dependency layers**: a wave's packages run in parallel; the next wave starts once the previous one is integrated (compiles, lints, committed atomically).
4. Lint fixes fan out per package to cheap agents; test failures go back to the owning package at its assigned type.
5. A dependency the table missed: update the table in `SPECS.md` with a journal line.
6. Session labels: a few words describing the task (`"Auth pages"`), no model prefix while the statusline badge configuration is present (`~/.claude/subagent-statusline.sh`). When it is absent (repo cloned elsewhere), the label falls back to `<model>(<effort>): <task>` (for example `haiku(medium): Auth pages`) so the model and effort stay visible.
7. **Never assign below the tier a task genuinely needs.** Misassigning down wastes a whole loop: the under-powered agent fails or returns unusable work, then the package is re-briefed and re-run at the right tier. Pick the cheapest tier that is adequate, not the cheapest tier that might be.

The table is part of the Checkpoint 1 screen and is vetoable like any other spec item.
