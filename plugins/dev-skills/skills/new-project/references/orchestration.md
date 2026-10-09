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

1. **Decompose along module boundaries** so file sets are disjoint; two agents must never write the same files (worktree isolation when overlap is unavoidable). Trivial scope: a one-package table run by the main loop.
2. **Wave 0 = scaffold + shared contracts**, single agent, never parallel.
3. **Waves are dependency layers**: a wave's packages run in parallel; the next wave starts once the previous one is integrated (compiles, lints, committed atomically).
4. Lint fixes fan out per package to cheap agents; test failures go back to the owning package at its assigned type.
5. A dependency the table missed: update the table in `SPECS.md` with a journal line.
6. Labels: a few words describing the task (`"Auth pages"`), no model prefix.

The table is part of the Checkpoint 1 screen and is vetoable like any other spec item.
