---
name: agents-md
argument-hint: "[init|audit|sync] [--tier=1|2|3] [--lang=<code>] [--archives=tolerate|annotate|fix] [--dry-run] [--help]"
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
/agents-md --archives=<policy>  # dead references inside dated records: tolerate (default), annotate, fix
/agents-md --dry-run        # init and sync: print the plan, zero writes
/agents-md --help           # print this Usage block and stop
```

With `--help`/`-h` and nothing else, print the Usage block verbatim and stop.

Guardrail scripts destination: `${user_config.agents_md_guardrail_scripts_path}` (default `.claude/agents-md/`), written `<scripts_path>` below. Resolution: `guardrail_scripts_path` in `.claude/agents-md.yml` > plugin option > `.claude/agents-md/`. No other exception: the default is the same in every project. Every copied checker carries the ownership marker `# dev-skills: agents-md <plugin version>`; copy, stamp, compare and replace rules: `${CLAUDE_SKILL_DIR}/references/guardrail-scripts.md`. The destination must not be git-ignored: `.gitignore` procedure in `${CLAUDE_SKILL_DIR}/references/detection.md` (section 12).

Resolution order for every policy: argument > `.claude/agents-md.yml` > plugin option `${user_config.<KEY>}` > recommended default. The archives policy (dead references inside dated records such as `errors/`, `adr/`, `postmortems/`) resolves as `--archives` > `archives.policy` in the project config > `${user_config.agents_md_archives_policy}` > `tolerate`; see P1.2 and `sync` below. An argument never overrides a **guardrail**: `init` on a repository that already has an AGENTS.md still refuses (switch to `audit`).

## Scope

**For:** documentation an *agent* reads: behaviour rules, absolute prohibitions, verified commands, layer boundaries, non-guessable naming, the knowledge index, and the scripts that make rules checkable. **Not for:** product docs, human READMEs, API references, onboarding guides, translating docs, generating a knowledge graph (detected and documented if present), or wiring CI (it hands over the block; see `${CLAUDE_SKILL_DIR}/references/guardrail-scripts.md`).

## Governing principles

These override convenience, in all three modes.

1. **Verified or absent, unknown is a finding.** Every written command has been executed here; every cited path stat'd; every branch resolved. A fact that cannot be established becomes a question, an explicitly empty slot, or (in `audit`) a reported blind spot, never a plausible guess or a green check. A confidently wrong AGENTS.md is worse than a short one: agents follow it.
2. **Generic content harms.** Never write "follow best practices" or "handle errors properly". Document the counter-intuitive convention an agent would get wrong from the code alone. Avoid volatile state (current branch, task in progress, open PRs, drifting counts): write the command that reads it; you arbitrate the rare exception (content-rules §7). See `${CLAUDE_SKILL_DIR}/references/content-rules.md`.
3. **The instruction budget is finite.** Count, report, refuse to pad; a rule added displaces one already there. Canonical figure: `${CLAUDE_SKILL_DIR}/references/structure.md` (Instruction budget).
4. **Behaviour stays, guardrails travel.** Behaviour rules live in the root AGENTS.md, never externalised. Domain guardrails keep the prohibition in the root and the detail in the domain file. See `${CLAUDE_SKILL_DIR}/references/structure.md`.
5. **Never drop a prohibition.** Compression rewrites a justification, never an imperative. Any `sync` touching guardrails ends with a mechanical non-regression check: prohibition count before and after (`count_rules.py`), grep every prohibition marker.

## Mode: init

Builds the system from scratch. **Refuses and switches to `audit` if a root AGENTS.md already exists** (say so plainly, do not overwrite).

**Phase 0 - measure.** Run the detection probes in `references/detection.md` (including script triage, canonical-copy comparison and the `.gitignore` probes). They are independent: fan them out. Produce a factual profile of the repository: languages, package managers, real commands, sub-projects, branch-to-environment mapping, commit conventions, existing quality tooling, dominant language of the existing prose.

**Phase 1 - size it.** Resolve the tier: `--tier` > `.claude/agents-md.yml` > `${user_config.agents_md_tier_policy}` > the tier measured from the repository (see `${CLAUDE_SKILL_DIR}/references/structure.md`). Report the per-session token cost. With `auto`, never pick tier 3 for a small repository: an instruction file that is not earned is a permanent tax. A forced `--tier=3` on a small repository prints a warning with that cost and proceeds.

**Phase 2 - resolve policies, ask nothing by default.** Resolve each policy in the same order (argument > project config > plugin option > recommended default): doc language (`${user_config.agents_md_doc_language}`), guardrail scripts (`${user_config.agents_md_install_guardrail_scripts}`, opt-out; meaning: install each canonical checker where the project has no variant with the same purpose, never a duplicate), commit convention (`${user_config.agents_md_commit_convention_policy}`: detect, enforce or skip). Ask only a blocking question: the production ref when it is undetectable. A documentation-language rule found in the repository wins over the resolved language: apply it and print the conflict in the plan. The prohibitions no code can reveal are never invented: unknown ones stay an explicitly empty slot, listed in the report. Then present ONE plan confirmation (tier, file set, scripts with a status per checker `installed|variant|absent`, language) before the first write, and list every empty prohibition slot explicitly by name and location in that same confirmation, inviting the human to fill them in their reply to it. No extra question round: the reply either fills a slot (written verbatim, as an imperative) or leaves it empty, and an unfilled slot is reported as empty.

**Phase 3 - write.** After the plan is confirmed, generate the tier's file set from `${CLAUDE_SKILL_DIR}/templates/`, filled with measured facts. Copy each canonical checker that has no project variant (`${CLAUDE_SKILL_DIR}/references/guardrail-scripts.md`, "Install or variant"; record `installed`, `variant` or `absent` in `guardrail_scripts`), stamping the marker version (`${CLAUDE_SKILL_DIR}/references/guardrail-scripts.md`, "Copy and stamp"; `check_dead_paths.py` and `check_sections.py` are audit tools, not copied). Apply the triage moves and the `.gitignore` fixes planned. Write `.claude/agents-md.yml`. End with the final `.gitignore` probe (detection.md section 12): table printed, any mismatch fixed in the same run. With `--dry-run`, print the plan and stop: zero writes. Dry-run also applies when the user asks for "plan only", "show what you would generate" or "write nothing" without the flag. In dry-run: (a) the plan lists a command only if it was executed here with a safe check and succeeded; a command that could not be run (e.g. `npm` absent) is listed under "Not verified - will not be written" or as an explicitly empty slot, never as a command to document; (b) the plan states the tier with its justification, the file list, the scripts and their destination, the triage moves, the `.gitignore` edits, the language and every empty slot, and no more than one question (only a blocker); (c) before answering, run `ls` / `git status --short` on the target for `AGENTS.md`, `CLAUDE.md`, `AGENTS/`, `<scripts_path>/check_*.py` and `.claude/agents-md.yml`, and state in the answer that none of them exists (proof of zero writes).

**Phase 4 - verify your own output.** Stat every path cited. Execute every command written. Confirm every cross-reference resolves to a file that exists and actually contains the section named. Fix or remove whatever fails. **This phase is not optional**: it is the difference between this skill and a template generator.

**Phase 5 - report.** What was written, what was deliberately left empty and why, what the human must fill in, and the measured instruction count against the budget. When multiple agents are possible (several authors, agent tooling, worktrees), recommend running `/orchestration`, which owns parallelism and isolation; this skill writes only the one-line isolation stub of the template.

## Mode: audit

Zero writes. Grades an existing system and reports findings ranked P0 to P3, each with the evidence that produced it. The full check grid, with the command that runs each check, is in `references/audit-checks.md`.

The seven families, plus script triage, canonical-copy and `.gitignore` checks (findings in `references/audit-checks.md`):

- **Dead references.** Every path, file, branch, workflow, script and section name cited in the documentation, resolved against the repository.
- **False facts.** Commands are *executed*, not read. A documented `sudo docker` on a host where docker runs unprivileged is a finding. A CI command pinned to a branch that no longer exists is a finding. A file said to contain a section that it does not is a finding.
- **Internal contradictions.** Rules that cancel each other, absolutes with no workable exception, a rule keyed to a named model where a role is meant, a rule whose enforcement mechanism is missing.
- **Redundancy.** Passages repeated across sections (always-loaded files only), and a CLAUDE.md that carries more than the import and one pointer line (P2.6), and the reliable tell: a "see above" or "cf. section X" that follows a restatement of section X.
- **Instruction budget.** Count normative statements with `${CLAUDE_SKILL_DIR}/scripts/count_rules.py` across every always-loaded file, compare against the instruction budget in `${CLAUDE_SKILL_DIR}/references/structure.md`, report the margin.
- **Balance.** Characters per section. A section that outweighs the project's own commands by several times is misallocated, whatever its merit.
- **Coverage gaps.** What the repository does that the documentation never mentions: test suites, CI guardrails, deployment paths, environment quirks.

Findings are reported most severe first, each stating the check that found it and the observed value. No finding without evidence.

Audit report format, mandatory:

- **Group the report under explicit `P0`, `P1`, `P2`, `P3` headings** (omit an empty level or write "none"); every finding sits under one and states its check and observed value. Rubric: P0 = an agent following the doc breaks things or is misled on a safety rule; P1 = dead reference or false fact (missing file, command that cannot work); P2 = contradiction, redundancy, budget or balance problem; P3 = coverage gap, missing pointer, cosmetic. An unranked prose list is a failed audit.
- **Stable finding IDs, a fix line.** Number every finding `AM-NN` (`AM-01`, `AM-02`, ...): unique, in report order (most severe first), never renumbered afterwards. Each finding carries a `Fix:` line (the concrete correction, or the question to settle) and, when the fix is a real choice between alternatives, an `Options:` line with 2-3 options, the recommended one first. A later `sync` plan reuses the same `AM-NN` IDs unchanged.
- **`report-only` tag.** A finding that `sync` cannot fix (needs a human decision the doc cannot settle, or belongs to `/orchestration`) carries the tag `report-only` after its rank. A finding owned by `/orchestration` takes the owner's rank, never a higher one here (a hardcoded model lineup is P2, never P0).
- **Read-only means read-only.** Create no file (no `.claude/agents-md.yml`, no report or scratch file in the repository), edit no documentation file; the report goes in the reply only.
- **Never run `sudo` or any privileged or state-changing command to verify a documented command.** Use safe checks (`command -v`, `--version`, a stat). If it cannot be established (docker absent, daemon unreachable, sandbox restriction), list it under "Not checked" as an unverified command with its P-rank. A `sudo` prefix that cannot be justified is itself a finding: report the documented command (with its `sudo`) as a P1 false-or-unverified fact, stating plainly whether it is false or unverified and why.
- **End the report with a "Prohibitions preserved" line** stating the prohibition count and quoting each one verbatim; also state that no file was modified (verify with `git status --short` and a checksum taken before and after, and say so).
- **Prohibitions are quoted, never rewritten or judged away.** Quote each prohibition (for example "Never commit to main") unchanged. Do not report a prohibition as a defect merely because it is strict; report only a real contradiction or a missing enforcement mechanism, as P3.

## Mode: sync

Runs `audit`, **prints the audit findings first** (each with its `AM-NN` ID, P-rank, evidence and `Fix:` line), then presents ONE plan confirmation listing the batches, each referencing those IDs unchanged, and applies fixes batch by batch, most valuable first (`--dry-run`: print findings and batches, zero writes). A finding sync cannot fix (for example a P2 balance problem when behaviour rules must stay in the root, or a script owned by `/orchestration`) is tagged `report-only` in the audit and left out of the plan. When `.claude/agents-md.yml` is absent, the plan includes writing it from `${CLAUDE_SKILL_DIR}/templates/agents-md.yml.tmpl`, filled with measured values (schema: `config-schema.md`). Four operations, never mixed within a batch:

- **Correct.** False facts and dead references. Lowest risk, highest value, always offered first. Dead references inside archive paths follow the archives policy: `tolerate` leaves them, `annotate` rewrites only the reference as "`new` (formerly `old`)" and never the record body, `fix` replaces the reference.
- **Compress.** Keep the imperative and the numeric threshold; move the justification, the history and the procedure out. A guardrail works by its imperative form, not by its explanation.
- **Externalise.** Move single-domain detail into that domain's file, leaving one imperative line plus a pointer.
- **Triage scripts.** Move misplaced agentic scripts (a move keeps every lint/test scope and updates every reference, archives included), refresh outdated canonical copies, replace project variants only with proof, fix `.gitignore`. Procedures: `${CLAUDE_SKILL_DIR}/references/guardrail-scripts.md` (Script triage) and `${CLAUDE_SKILL_DIR}/references/detection.md` (sections 10-12). All moves and replacements sit in the single plan confirmation, no separate question. Ownership: this skill moves or replaces only its four checkers and project-written scripts that read only agentic docs; scripts owned by `/orchestration` are reported, never touched. Scripts with a project variant are not re-installed (guardrail-scripts.md, "Install or variant"). The `.gitignore` procedure is entirely this skill's, applied in one pass for every dev-skills path present or planned (detection.md section 12).

**Before any compression or externalisation, verify the target already carries the detail.** Probe the destination file for the specific facts about to be removed. If the probe fails, the operation is not compression, it is deletion: skip it and report why.

**After every batch that touched guardrails**, run the non-regression check: the prohibition count before and after must not drop unless a merge was explicitly approved, and every prohibition marker must still be present. Report the line with additions explicit: `prohibitions 10 -> 11 (+1 added: "<short quote>")`. A drop aborts the batch.

**At the end of any sync that wrote files**, run the final `.gitignore` probe (detection.md section 12): `git check-ignore -v` on every path that must be ignored and every written path that must be committed, print the table, fix any mismatch in the same run.

## Reference files

Load per mode, read nothing else (open a section by its heading, not the whole file when only a section is listed):

| Mode | Load |
|---|---|
| audit | `audit-checks.md`; `detection.md` sections 2, 4, 8, 10-12; `structure.md` (Instruction budget) |
| sync | the audit set, plus `guardrail-scripts.md`, `content-rules.md` sections 5-6, `config-schema.md` |
| init | `detection.md` (all), `structure.md`, `content-rules.md`, `guardrail-scripts.md`, `config-schema.md`, `templates/` |

All under `${CLAUDE_SKILL_DIR}/references/`. `detection.md`: probes (script triage, canonical copies, `.gitignore`). `structure.md`: tiers, where a rule belongs, instruction budget and counting method. `content-rules.md`: what to write. `audit-checks.md`: the check grid. `guardrail-scripts.md`: copy, stamp, triage, replace, wire. `config-schema.md`: `.claude/agents-md.yml`.

`${CLAUDE_SKILL_DIR}/templates/` holds the file skeletons (including `agents-md.yml.tmpl`). `${CLAUDE_SKILL_DIR}/scripts/` holds the guardrail checkers (copied into the target project at `<scripts_path>`) and the read-only audit scripts, run in place: `check_dead_paths.py`, `check_sections.py`, `check_ci_replay.py` (P3.4), and `count_rules.py` (canonical counter of normative statements and prohibitions, JSON output; method in `structure.md`; `/orchestration` reuses it). In `templates/adr-0001.md.tmpl`, fill `{{BUDGET_FIGURE}}` from the canonical budget in `structure.md`.

## Language

The documentation language is `${user_config.agents_md_doc_language}` (default English: cheaper to tokenise, the audience is a model), overridden by `--lang` or `.claude/agents-md.yml`. Reports to the user follow the user's language.

**If the repository states a documentation language rule** (a guardrail imposing a language), it wins over the default: apply it, quote the rule and its location in the plan, never override it silently.
