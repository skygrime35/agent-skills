---
name: agents-md
argument-hint: "[init|audit|sync] [--tier=1|2|3] [--lang=<code>] [--dry-run] [--help]"
description: "Creates, grades or repairs a project's agent documentation: root AGENTS.md, thin CLAUDE.md pointer, per-domain AGENTS.md, AGENTS/ index, ADRs and guardrail scripts. Modes: init (tiered build), audit (read-only P0-P3 report: dead references, false facts, contradictions, budget overrun), sync (confirmed fixes, no prohibition dropped). Never writes unverified commands or paths."
when_to_use: "AGENTS.md, CLAUDE.md, agent docs, instruction budget, audit my agent docs, set up agent instructions, fix stale agent documentation."
---

# /agents-md

Plugin options appear in this file as their configured value. In reference files they stay as `user_config.<key>` placeholders: use the value this file shows. If a value still shows as a placeholder here (option never configured), use its `default` in `${CLAUDE_SKILL_DIR}/../../.claude-plugin/plugin.json`.

Skill directory: `${CLAUDE_SKILL_DIR}`. Reference files mark bundled paths with the CLAUDE_SKILL_DIR variable in dollar-brace form; the shell does not set it, so replace it with this directory before running or copying anything.

Builds, grades or repairs the file set that tells an AI agent how a repository works, what it must never do, and where detailed knowledge lives. Portable: every run measures the repository; non-guessable specifics go in `.claude/agents-md.yml`. Central promise: **it never writes what it has not verified** (no unexecuted command, no unstat'd path, no inferred convention).

## Usage

```
/agents-md                  # bare: detect, then auto-pick init (no AGENTS.md) or audit (exists); print the choice
/agents-md init             # build from scratch (refuses if AGENTS.md already exists)
/agents-md audit            # grade the existing system, write nothing, report P0-P3
/agents-md sync             # audit, then apply fixes in batches after one plan confirmation
/agents-md --tier=1|2|3     # force the size tier
/agents-md --lang=<code>    # force the documentation language
/agents-md --dry-run        # init and sync: print the plan, zero writes
/agents-md --help           # print this Usage block and stop
```

With `--help`/`-h` and nothing else, print the Usage block verbatim and stop.

Resolution order for every policy: argument > `.claude/agents-md.yml` > plugin option `${user_config.<KEY>}` > recommended default. An argument never overrides a **guardrail**: `init` on a repository that already has an AGENTS.md still refuses (switch to `audit`).

## Scope

**For:** documentation an *agent* reads: behaviour rules, absolute prohibitions, verified commands, layer boundaries, non-guessable naming, the knowledge index, and the scripts that make rules checkable. **Not for:** product docs, human READMEs, API references, onboarding guides, translating docs, generating a knowledge graph (detected and documented if present), or wiring CI (it hands over the block; see `${CLAUDE_SKILL_DIR}/references/guardrail-scripts.md`).

## Governing principles

These override convenience, in all three modes.

1. **Verified or absent, unknown is a finding.** Every written command has been executed here; every cited path stat'd; every branch resolved. A fact that cannot be established becomes a question, an explicitly empty slot, or (in `audit`) a reported blind spot, never a plausible guess or a green check. A confidently wrong AGENTS.md is worse than a short one: agents follow it.
2. **Generic content harms.** Never write "follow best practices" or "handle errors properly". Document the counter-intuitive convention an agent would get wrong from the code alone. See `${CLAUDE_SKILL_DIR}/references/content-rules.md`.
3. **The instruction budget is finite.** Count, report, refuse to pad; a rule added displaces one already there. Canonical figure: `${CLAUDE_SKILL_DIR}/references/structure.md` (Instruction budget).
4. **Behaviour stays, guardrails travel.** Behaviour rules live in the root AGENTS.md, never externalised. Domain guardrails keep the prohibition in the root and the detail in the domain file. See `${CLAUDE_SKILL_DIR}/references/structure.md`.
5. **Never drop a prohibition.** Compression rewrites a justification, never an imperative. Any `sync` touching guardrails ends with a mechanical non-regression check: count before and after, grep every prohibition marker.

## Mode: init

Builds the system from scratch. **Refuses and switches to `audit` if a root AGENTS.md already exists** (say so plainly, do not overwrite).

**Phase 0 - measure.** Run the detection probes in `references/detection.md`. They are independent: fan them out. Produce a factual profile of the repository: languages, package managers, real commands, sub-projects, branch-to-environment mapping, commit conventions, existing quality tooling, dominant language of the existing prose.

**Phase 1 - size it.** Resolve the tier: `--tier` > `.claude/agents-md.yml` > `${user_config.agents_md_tier_policy}` > the tier measured from the repository (see `${CLAUDE_SKILL_DIR}/references/structure.md`). Report the per-session token cost. With `auto`, never pick tier 3 for a small repository: an instruction file that is not earned is a permanent tax. A forced `--tier=3` on a small repository prints a warning with that cost and proceeds.

**Phase 2 - resolve policies, ask nothing by default.** Resolve each policy in the same order (argument > project config > plugin option > recommended default): doc language (`${user_config.agents_md_doc_language}`), guardrail scripts (`${user_config.agents_md_install_guardrail_scripts}`, opt-out), commit convention (`${user_config.agents_md_commit_convention_policy}`: detect, enforce or skip). Ask only a blocking question: the production ref when it is undetectable, or a documentation-language rule found in the repository that conflicts with the resolved language. The prohibitions no code can reveal are never invented: unknown ones stay an explicitly empty slot, listed in the report. Then present ONE plan confirmation (tier, file set, scripts, language) before the first write, and list every empty prohibition slot explicitly by name and location in that same confirmation, inviting the human to fill them in their reply to it. No extra question round: the reply either fills a slot (written verbatim, as an imperative) or leaves it empty, and an unfilled slot is reported as empty.

**Phase 3 - write.** After the plan is confirmed, generate the tier's file set from `${CLAUDE_SKILL_DIR}/templates/`, filled with measured facts. Copy the guardrail scripts if enabled: `cp ${CLAUDE_SKILL_DIR}/scripts/check_*.py <target>/scripts/`. Write `.claude/agents-md.yml`. With `--dry-run`, print the plan and stop: zero writes.

**Phase 4 - verify your own output.** Stat every path cited. Execute every command written. Confirm every cross-reference resolves to a file that exists and actually contains the section named. Fix or remove whatever fails. **This phase is not optional**: it is the difference between this skill and a template generator.

**Phase 5 - report.** What was written, what was deliberately left empty and why, what the human must fill in, and the measured instruction count against the budget.

## Mode: audit

Zero writes. Grades an existing system and reports findings ranked P0 to P3, each with the evidence that produced it. The full check grid, with the command that runs each check, is in `references/audit-checks.md`.

The seven families:

- **Dead references.** Every path, file, branch, workflow, script and section name cited in the documentation, resolved against the repository.
- **False facts.** Commands are *executed*, not read. A documented `sudo docker` on a host where docker runs unprivileged is a finding. A CI command pinned to a branch that no longer exists is a finding. A file said to contain a section that it does not is a finding.
- **Internal contradictions.** Rules that cancel each other, absolutes with no workable exception, a rule keyed to a named model where a role is meant, a rule whose enforcement mechanism is missing.
- **Redundancy.** Passages repeated across sections, and the reliable tell: a "see above" or "cf. section X" that follows a restatement of section X.
- **Instruction budget.** Count normative statements across every always-loaded file, compare against the instruction budget in `${CLAUDE_SKILL_DIR}/references/structure.md`, report the margin.
- **Balance.** Characters per section. A section that outweighs the project's own commands by several times is misallocated, whatever its merit.
- **Coverage gaps.** What the repository does that the documentation never mentions: test suites, CI guardrails, deployment paths, environment quirks.

Findings are reported most severe first, each stating the check that found it and the observed value. No finding without evidence.

Audit report format, mandatory:

- **Group the report under explicit `P0`, `P1`, `P2`, `P3` headings** (omit an empty level or write "none"); every finding sits under one and states its check and observed value. Rubric: P0 = an agent following the doc breaks things or is misled on a safety rule; P1 = dead reference or false fact (missing file, command that cannot work); P2 = contradiction, redundancy, budget or balance problem; P3 = coverage gap, missing pointer, cosmetic. An unranked prose list is a failed audit.
- **Read-only means read-only.** Create no file (no `.claude/agents-md.yml`, no report or scratch file in the repository), edit no documentation file; the report goes in the reply only.
- **Never run `sudo` or any privileged or state-changing command to verify a documented command.** Use safe checks (`command -v`, `--version`, a stat). If it cannot be established (docker absent, daemon unreachable, sandbox restriction), list it under "Not checked" as an unverified command with its P-rank. A `sudo` prefix that cannot be justified is itself a finding: report the documented command (with its `sudo`) as a P1 false-or-unverified fact, stating plainly whether it is false or unverified and why.
- **End the report with a "Prohibitions preserved" line** stating the prohibition count and quoting each one verbatim; also state that no file was modified (verify with `git status --short` and a checksum taken before and after, and say so).
- **Prohibitions are quoted, never rewritten or judged away.** Quote each prohibition (for example "Never commit to main") unchanged. Do not report a prohibition as a defect merely because it is strict; report only a real contradiction or a missing enforcement mechanism, as P3.

## Mode: sync

Runs `audit`, then presents ONE plan confirmation listing the batches, and applies fixes batch by batch, most valuable first (`--dry-run`: print the batches, zero writes). Three operations, never mixed within a batch:

- **Correct.** False facts and dead references. Lowest risk, highest value, always offered first.
- **Compress.** Keep the imperative and the numeric threshold; move the justification, the history and the procedure out. A guardrail works by its imperative form, not by its explanation.
- **Externalise.** Move single-domain detail into that domain's file, leaving one imperative line plus a pointer.

**Before any compression or externalisation, verify the target already carries the detail.** Probe the destination file for the specific facts about to be removed. If the probe fails, the operation is not compression, it is deletion: skip it and report why.

**After every batch that touched guardrails**, run the non-regression check: guardrail count before and after must match unless a merge was explicitly approved, and every prohibition marker must still be present. Report both numbers.

## Reference files

Load on demand, not upfront:

| File | When |
|---|---|
| `${CLAUDE_SKILL_DIR}/references/detection.md` | Phase 0 of any mode |
| `${CLAUDE_SKILL_DIR}/references/structure.md` | Choosing a tier, deciding where a rule belongs |
| `${CLAUDE_SKILL_DIR}/references/content-rules.md` | Writing any documentation content |
| `${CLAUDE_SKILL_DIR}/references/audit-checks.md` | Modes audit and sync |
| `${CLAUDE_SKILL_DIR}/references/guardrail-scripts.md` | Generating or wiring the scripts |
| `${CLAUDE_SKILL_DIR}/references/config-schema.md` | Reading or writing `.claude/agents-md.yml` |

`${CLAUDE_SKILL_DIR}/templates/` holds the file skeletons; `${CLAUDE_SKILL_DIR}/scripts/` holds the guardrail checkers, copied into the target project. In `templates/adr-0001.md.tmpl`, fill `{{BUDGET_FIGURE}}` from the canonical budget in `structure.md`.

## Language

The documentation language is `${user_config.agents_md_doc_language}` (default English: cheaper to tokenise, the audience is a model), overridden by `--lang` or `.claude/agents-md.yml`. Reports to the user follow the user's language.

**If the repository states a conflicting language rule** (a guardrail imposing another language for documentation), do not silently override it: report the conflict, quote the rule and its location, and ask (this is a blocking case). A skill that quietly violates a project's own written rule is a bug, not a feature.
