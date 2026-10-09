---
name: agents-md
argument-hint: "[init|audit|sync] [--tier=1|2|3] [--lang=en|fr] [--dry-run] [--help]"
description: "Use to create, grade, or repair a project's agentic documentation system: the root AGENTS.md, a thin CLAUDE.md pointer, per-domain AGENTS.md files, an AGENTS/ knowledge folder with a maintained index, ADRs, and the mechanical guardrail scripts that keep the written rules real. Three modes: init builds the system from scratch at a size that fits the project (three tiers, proposed after measuring it); audit grades an existing system and reports dead references, false facts, contradictions, redundancy and instruction-budget overrun, writing nothing; sync applies those fixes in confirmed batches, never dropping a prohibition. Portable via per-run auto-detection plus a .claude/agents-md.yml config. Refuses to write what it has not verified: every documented command has been executed, every cited path exists, and anything unknown becomes a question or an explicitly empty slot."
---

# /agents-md

Build, grade, or repair the **agentic documentation system** of any repository: the file set that tells an AI agent how this project works, what it must never do, and where the detailed knowledge lives.

This skill is **portable across any project**. It measures the repository on every run (languages, real commands, domain boundaries, branch-to-environment mapping, existing tooling) and records the non-guessable specifics in a per-project `.claude/agents-md.yml`.

Its central promise is a negative one: **it never writes what it has not verified.** Not a command it did not run, not a path it did not stat, not a convention it inferred from a filename.

## Usage

```
/agents-md                  # interactive: detect the project, then propose init or audit
/agents-md init             # build the system from scratch (refuses if AGENTS.md already exists)
/agents-md audit            # grade the existing system, write nothing, report P0-P3
/agents-md sync             # audit, then apply fixes in confirmed batches
/agents-md --tier=1|2|3     # force the size tier instead of asking
/agents-md --lang=en|fr|... # force the documentation language instead of detecting
/agents-md --dry-run        # print the execution plan. Zero writes
/agents-md --help           # print this Usage block and stop
```

If invoked with `--help`/`-h` and nothing else, print the Usage block above verbatim and stop.

Arguments override questions. An argument never overrides a **guardrail**: `--tier=3` on a fifty-file repository still triggers the size warning, and `init` on a repository that already has an AGENTS.md still refuses.

## What this skill is for / non-goals

**For:** the documentation an *agent* reads to work correctly in this repository. Behaviour rules, absolute prohibitions, verified commands, layer boundaries, naming conventions, the index of detailed knowledge files, and the scripts that make the rules mechanically checkable.

**Not for:** product documentation, README files aimed at humans, API references, or onboarding guides. **Not for** translating existing documentation. **Not for** generating a knowledge graph (it detects one and documents its use if present). **Not for** wiring CI: it writes the guardrail scripts and hands you the block to paste, but it does not touch your pipeline.

## Governing principles

These override any convenience, in all three modes.

1. **Verified or absent.** Every command written into the documentation has been executed in this repository. Every path cited has been stat'd. Every branch named has been resolved. If a fact cannot be established, it becomes a question to the human or an explicitly empty slot, never a plausible guess. A confidently wrong AGENTS.md is worse than a short one: agents follow it.
2. **Generic content actively harms.** LLM-written agent instructions measurably degrade task success when they state the obvious. Never write "follow best practices", "write clean code", "handle errors properly". The convention worth documenting is the **counter-intuitive** one: the thing an agent would get wrong by reasoning from the code alone. See `references/content-rules.md`.
3. **The instruction budget is finite.** Frontier models follow roughly 150-200 instructions before adherence degrades, and the harness already spends about 50. Past that, a rule you add **replaces** one already there instead of joining it. Count, report, and refuse to pad.
4. **Behaviour stays, guardrails travel.** Behaviour rules apply on every turn regardless of the file being touched, so they live in the root AGENTS.md and are never externalised. Domain guardrails apply only when that domain is touched, so their detail belongs in the domain file, leaving the prohibition behind. See `references/structure.md`.
5. **Never drop a prohibition.** Compression rewrites a rule's justification, never its imperative. Any `sync` that touches guardrails ends with a mechanical non-regression check: count before, count after, and grep for every prohibition marker.
6. **Unknown is a finding, not a gap to fill.** In `audit`, an undetectable fact is reported as a blind spot. Never a green check, never an assumption dressed as a conclusion.

## Mode: init

Builds the system from scratch. **Refuses and switches to `audit` if a root AGENTS.md already exists** (say so plainly, do not overwrite).

**Phase 0 - measure.** Run the detection probes in `references/detection.md`. They are independent: fan them out. Produce a factual profile of the repository: languages, package managers, real commands, sub-projects, branch-to-environment mapping, commit conventions, existing quality tooling, dominant language of the existing prose.

**Phase 1 - size it.** Propose a tier from the measurement (see `references/structure.md`), with its per-session token cost, and confirm with the human. Never impose tier 3 on a small repository: an instruction file that is not earned is a permanent tax.

**Phase 2 - ask only the non-inferable.** Which ref deploys production. What must never happen (the prohibitions no code can reveal). Which structural decisions are already settled. Which language to write in, if detection was ambiguous or conflicts with a rule found in the repository. Keep it to four questions or fewer: everything else was measured in Phase 0.

**Phase 3 - write.** Generate the tier's file set from `templates/`, filled with measured facts. Generate the guardrail scripts the human accepted. Write `.claude/agents-md.yml`.

**Phase 4 - verify your own output.** Stat every path cited. Execute every command written. Confirm every cross-reference resolves to a file that exists and actually contains the section named. Fix or remove whatever fails. **This phase is not optional**: it is the difference between this skill and a template generator.

**Phase 5 - report.** What was written, what was deliberately left empty and why, what the human must fill in, and the measured instruction count against the budget.

## Mode: audit

Zero writes. Grades an existing system and reports findings ranked P0 to P3, each with the evidence that produced it. The full check grid, with the command that runs each check, is in `references/audit-checks.md`.

The seven families:

- **Dead references.** Every path, file, branch, workflow, script and section name cited in the documentation, resolved against the repository.
- **False facts.** Commands are *executed*, not read. A documented `sudo docker` on a host where docker runs unprivileged is a finding. A CI command pinned to a branch that no longer exists is a finding. A file said to contain a section that it does not is a finding.
- **Internal contradictions.** Rules that cancel each other, absolutes with no workable exception, a rule keyed to a named model where a role is meant, a rule whose enforcement mechanism is missing.
- **Redundancy.** Passages repeated across sections, and the reliable tell: a "see above" or "cf. section X" that follows a restatement of section X.
- **Instruction budget.** Count normative statements across every always-loaded file, compare against the 150-200 threshold, report the margin.
- **Balance.** Characters per section. A section that outweighs the project's own commands by several times is misallocated, whatever its merit.
- **Coverage gaps.** What the repository does that the documentation never mentions: test suites, CI guardrails, deployment paths, environment quirks.

Findings are reported most severe first, each stating the check that found it and the observed value. No finding without evidence.

## Mode: sync

Runs `audit`, then applies fixes in **confirmed batches**, most valuable first. Three operations, never mixed within a batch:

- **Correct.** False facts and dead references. Lowest risk, highest value, always offered first.
- **Compress.** Keep the imperative and the numeric threshold; move the justification, the history and the procedure out. A guardrail works by its imperative form, not by its explanation.
- **Externalise.** Move single-domain detail into that domain's file, leaving one imperative line plus a pointer.

**Before any compression or externalisation, verify the target already carries the detail.** Probe the destination file for the specific facts about to be removed. If the probe fails, the operation is not compression, it is deletion: skip it and report why.

**After every batch that touched guardrails**, run the non-regression check: guardrail count before and after must match unless a merge was explicitly approved, and every prohibition marker must still be present. Report both numbers.

## Reference files

Load on demand, not upfront:

| File | When |
|---|---|
| `references/detection.md` | Phase 0 of any mode |
| `references/structure.md` | Choosing a tier, deciding where a rule belongs |
| `references/content-rules.md` | Writing any documentation content |
| `references/audit-checks.md` | Modes audit and sync |
| `references/guardrail-scripts.md` | Generating or wiring the scripts |
| `references/config-schema.md` | Reading or writing `.claude/agents-md.yml` |

`templates/` holds the file skeletons; `scripts/` holds the guardrail checkers, copied into the target project on request.

## Language

The documentation is written in **English by default**, whatever the repository's own language, because English is measurably cheaper to tokenise and the audience is a model.

**If the repository states a conflicting language rule** (a guardrail imposing another language for documentation), do not silently override it: report the conflict, quote the rule and its location, and ask. A skill that quietly violates a project's own written rule is a bug, not a feature.
