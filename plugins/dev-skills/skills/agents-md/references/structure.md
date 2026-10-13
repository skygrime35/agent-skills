# Sizing the system, and deciding where a rule belongs

Contents:
- The three tiers
- Where a rule belongs
- Root AGENTS.md section order
- The behaviour section
- INDEX.md
- Knowledge graph
- Instruction budget

## The three tiers

Measure first, propose, confirm. Never impose a tier: an instruction file that is not earned is a permanent tax on every session.

### Tier 1 - single concern

**Signals:** one language, no sub-project with its own dependency manifest, under roughly 10k LOC, single deployment target.

```
AGENTS.md     everything: behaviour, guardrails, verified commands, layout
CLAUDE.md     thin pointer (only if the project uses Claude Code)
```

Target: 60 to 120 lines in AGENTS.md. If it grows past 200, propose tier 2.

### Tier 2 - one project, several concerns

**Signals:** several languages or a build pipeline, 10k to 100k LOC, distinct test and deploy procedures, a handful of hard-won operational facts.

```
AGENTS.md          transverse: behaviour, guardrails, vital commands
CLAUDE.md          pointer
AGENTS/
  INDEX.md         table of contents: which file holds what, when to load it
  ARCHITECTURE.md  current state, not history
  COMMANDS.md      the full verified command reference
  TESTING.md       suites, how to run them, what is gated behind what
```

Add a file only when a specific body of knowledge exists to put in it. An empty `DEPLOYMENT.md` is worse than no file: it makes the index lie.

### Tier 3 - multi-domain

**Signals:** distinct domains with their own manifests and conventions (backend/frontend/services), over roughly 100k LOC, several environments, architectural decisions worth recording.

```
AGENTS.md                 transverse only
CLAUDE.md                 pointer
<domain>/AGENTS.md        one per detected domain, its conventions only
AGENTS/
  INDEX.md
  ARCHITECTURE.md  COMMANDS.md  TESTING.md  DEPLOYMENT.md
  GLOSSARY.md             only if the project has real domain vocabulary
  adr/README.md           MADR format, plus ADR 0001 recording the doc system itself
  postmortems/README.md   only if incidents are actually written up
TODO.md                   debt register, sectioned by domain
DOCS/                     product docs, on request only
```

## Where a rule belongs

Two questions, in order.

**1. Does it apply on every turn, or only when a domain is touched?**

Every turn means behaviour: task decomposition, when to ask, delegation, reporting, git and branch discipline. **Root file, never externalised.** An on-demand behaviour rule is read too late or never.

Domain-scoped means guardrail: this ORM constraint, that billing invariant, this deployment rule. **Prohibition in the root file, detail in the domain file.**

**2. Is it a prohibition, or an explanation?**

The prohibition and its numeric thresholds stay. The justification, the incident that produced it, and the step-by-step procedure go to the domain file. See rule 5 in `content-rules.md`.

## Root AGENTS.md section order

Ordered by how often an agent needs it, most frequent first.

1. **Header** - one line on what the project is, plus pointers to the domain files.
2. **Agent behaviour** - the numbered rules. Largest section by design at tier 3, and the one that must never be externalised.
3. **Project** - stack with version pins, current architecture state. No history.
4. **Absolute guardrails** - flat list of prohibitions, one line each, pointer for detail.
5. **Naming conventions** - only the ones a model would not guess.
6. **Layers / boundaries** - the import rules, if the project has any.
7. **Commits** - format and scopes, if enforced.
8. **Vital commands** - the handful used constantly, all verified. Pointer to the full reference.
9. **Doc synchronisation rule** - when documentation must be updated relative to code.

## The behaviour section: what to generate

Generate these in every tier, adapted to the project. They encode failures observed in the field, not preferences.

- **Think before coding.** Surface assumptions, present competing readings of an ambiguous request rather than picking one silently.
- **Simplicity first.** Minimum code that solves the stated problem. No anticipated flexibility.
- **Surgical changes.** Touch only what the request implies. Every modified line must trace to the request.
- **Verifiable objectives.** Turn tasks into checkable success criteria.
- **Branch discipline.** Establish the current branch before the first modification. Never modify the production branch without an explicit request. Never switch branches without approval: it changes what every session sharing the directory sees.
- **Staging discipline.** Stage only files you modified yourself: it prevents one session committing another's in-flight work into an unrelated commit.
- **Concurrency isolation: one-line stub only.** The branch-discipline block carries a single rule (one git worktree per parallel agent) marked `agents-md:isolation-stub`, pointing to `/orchestration`, which owns parallelism and isolation and replaces the stub with its full doctrine. Never expand it here. When multiple agents are possible, the init report recommends running `/orchestration`.
- **Output density** (optional; included only when `.claude/agents-md.yml` or the plan opts in, never asked). Engineering-report prose: result first, no preamble, no closing summary. If generated, it must carry the bound: density applies to prose, never to the work, and never licenses skipping clarifying questions or hiding a risk.
- **Delegation** (only where subagents exist). With a threshold: below the cost of a delegation round trip, do it inline.

## INDEX.md

The index earns its place only if it says **when to load each file**, not just what each file is. A list of filenames is what `ls` already gives.

```markdown
| File | Load when | Holds |
|---|---|---|
| ARCHITECTURE.md | Changing structure, adding a module | Current layer map, boundaries, why they are where they are |
| COMMANDS.md | Any command not in the root file | Full verified reference, per environment |
```

Update it in the same commit as any file it lists. An index that lies is worse than no index: it sends agents to files that do not hold what was promised.

## Knowledge graph, if present

Detect (`graphify-out/`, `.graph.json`, similar). If found, document in the root file: how to query it, that it **locates but does not adjudicate** (read the real code before concluding), and the freshness check comparing its build commit to HEAD. A stale graph costs more than a plain grep, through false leads.

Never generate one. Never treat it as a source of truth.

## Instruction budget

Canonical figure (as of 2026-10), the single copy: frontier models follow roughly 150-200 instructions before adherence degrades, and the harness already spends about 50. Past that, a rule added **replaces** one already there. Other skills and files cite this section instead of restating the figure; refresh the date here when it is re-checked.

**Counting method (defined once, here).** Audits cite this paragraph and never restate it.

- **Unit:** in a normative section, every list item and every table body row is one statement (a rule list needs no modal word), plus every prose sentence carrying a modal. A unit counts once however many modals it holds. Non-normative sections (heading matching stack, architecture, structure, commands, references, index, or the FR equivalents; subsections inherit) skip the every-item rule: only a unit with an explicit modal counts there, so a stated prohibition is never lost.
- **Markers:** use the list of the document's language. EN: `must`, `never`, `always`, `required`, `forbidden`, `shall`, `do not`. FR: `doit`, `doivent`, `jamais`, `toujours`, `obligatoire`, `interdit`, `ne pas`, `ne jamais`, `aucun`, `il faut`. Matching is case- and accent-insensitive.
- **Prohibitions** (the non-regression count) = statements containing `never` / `must not` / `forbidden` / `do not` (FR: `jamais` / `interdit` / `ne pas` / `aucun`).
- **Canonical counter:** `${CLAUDE_SKILL_DIR}/scripts/count_rules.py FILE... [--section-heading TEXT]... [--lang auto|en|fr] [--skip-heading REGEX]... [--no-skip]` (stdlib, read-only, JSON; exit 0, or 2 on usage error). Per file and per section (own units only, with a `skipped` flag): `statements`, `prohibitions`. Top level: `totals` {statements, prohibitions} over all files (also `total_statements`, `total_prohibitions`); with `--section-heading`, each file lists `selected` per pattern (a parent includes its subsections) and the top level adds `selected_totals`, which sums every selected section once (a section matched by two patterns, or as a child of a matched parent, is not counted twice). Cite `totals` for the budget and `selected_totals` for a guardrail-section figure. Fences, comments, front matter, headings and table header rows are skipped. Limit: a prose sentence stating a rule without a modal ("No unrequested features.") is not counted, so the figure stays a lower bound; `--skip-heading` replaces the default non-normative heading patterns, `--no-skip` disables them. `/orchestration` reuses it as `${CLAUDE_SKILL_DIR}/../agents-md/scripts/count_rules.py` (its own `${CLAUDE_SKILL_DIR}`) instead of counting by hand; marker greps stay as a cross-check.
- **Files:** every always-loaded file: the root doc, the thin pointer (CLAUDE.md), and every file they pull in with an `@import` (followed recursively). On-demand files (`AGENTS/*.md`, domain files not imported) are not counted.
- **Harness share:** about 50, counted separately and added to the total only to compare against the budget above; never mixed into per-file figures.
- **Report:** the total, the per-file figures, the harness share, the margin to the budget, and an explicit uncertainty of about +/-10% (the count is a heuristic, not a parse). Name the sections that would be cut first.
