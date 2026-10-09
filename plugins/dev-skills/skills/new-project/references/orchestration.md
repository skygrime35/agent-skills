# Implementation orchestration — planned in the spec, validated at Checkpoint 1, executed in Phase 3

The implementation is not improvised at Phase 3: it is **planned as an orchestration table** in `SPECS.md`, shown at Checkpoint 1 inside the plan, then executed as written. Doctrine mirrors DebriefLab's `AGENTS.md` §5–§7.

## Doctrine

- **Token economy first.** Never a costly model for a simple task. Capability (and cost) order: **Fable > Opus > Sonnet > Haiku**. Each work package goes to the **least-cost model capable of doing it correctly**: Haiku for the simple/mechanical, Sonnet for the ordinary, Opus for the complex/critical, Fable only for what exceeds Opus. The orchestrator (the main loop talking to the user) never does itself what a cheaper agent would do as well — it decomposes, prompts, integrates, reviews.
- **Effort is a second axis** (within Sonnet and Opus), via the dedicated agent types in `~/.claude/agents/` — machine-local convention: `sonnet-quick` (effort low, mechanical), `sonnet-standard` (medium, ordinary delegation), `opus-standard` (Opus, medium effort, non-trivial reasoning), `opus-deep` (xhigh, complex and critical). Haiku and Fable have a single effort. **Fallback** when these types are absent (detected in Phase 0): the Agent tool's `model` parameter + session-default effort.
- **Parallelize the independent — under mandatory isolation.** Launch independent packages as parallel waves; two agents must **never write the same files**. Isolation = disjoint file sets by module boundary, or worktree isolation when overlap is unavoidable. This is the *condition* of parallelism, not an optional precaution.
- **Labels**: a few words describing the task (`"Auth pages"`, `"Recipe data layer"`), **without** model/effort prefix — the agents panel badges them via the machine-local statusline config. If that config is absent, fall back to `model(effort): task`.

## The orchestration table (goes into SPECS.md)

| # | Work package | Files / area | Agent (model · effort) | Depends on | Wave |
|---|--------------|--------------|------------------------|------------|------|
| 0 | Scaffold + shared contracts (types, schema, API shapes) | repo root | main loop or sonnet-standard | — | 0 |
| 1 | … | … | … | … | 1 |

Rules for building it:

1. **Decompose along module boundaries** so file sets are disjoint — the decomposition serves the isolation rule, not just readability. **Trivial scope** (a single small module) ⇒ a one-package table executed by the main loop; the machinery scales down rather than becoming ceremony.
2. **Wave 0 = scaffold + shared contracts** (types, DB schema, API shapes, design tokens): the things every other package depends on. Single agent, never parallel.
3. Assign tiers honestly: boilerplate/config/fixtures → Haiku or `sonnet-quick`; standard features → `sonnet-standard`; cross-cutting or correctness-critical work (data model, auth, anything touching money) → `opus-standard` / `opus-deep`. Don't drop below the tier a task genuinely needs — misassigning *up* wastes tokens, misassigning *down* wastes a whole loop.
4. **Waves are dependency layers**: everything inside a wave runs in parallel; a wave starts when the previous one is integrated (compiles, lints, commits atomically).
5. Phase 4 quality loops follow the same logic: lint fixes fan out per package to cheap agents; test failures are triaged back to the owning package at its assigned tier.
6. If execution reveals a dependency the table missed, **update the table in `SPECS.md`** (with a journal line) rather than silently improvising — the table stays the truth of how the project was built.

## Checkpoint 1 presentation

The table is part of the plan screen: the user sees at a glance how many agents, on which models, at which efforts, in which waves — and can veto the economics (e.g. "use opus-deep for the sync engine") exactly like any other spec item.
