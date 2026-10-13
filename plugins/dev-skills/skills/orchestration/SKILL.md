---
name: orchestration
argument-hint: "[init|audit|sync] [--scope=doctrine,agents,checks] [--lang=en|fr] [--interactive] [--dry-run] [--help]"
description: "Creates, audits or updates the agent-orchestration layer of a project's agentic docs: delegation doctrine in the base doc (CLAUDE.md/AGENTS.md), subagent type definitions (model x effort matrix) and the check script tying them together. Modes init, audit, sync; one plan confirmation, no interview by default."
when_to_use: "orchestration doctrine, subagent types, model ladder, delegation rules, which model for subagents, agent costs, haiku-quick/opus-standard types, parallel agents isolation, audit orchestration section, set up multi-agent rules"
---

# /orchestration

Skill directory: `${CLAUDE_SKILL_DIR}`. Reference files mark bundled paths with the CLAUDE_SKILL_DIR variable in dollar-brace form; the shell does not set it, so replace it with this directory before running or copying anything. Plugin options appear in this file as their configured value. In reference files they stay as `user_config.<key>` placeholders: use the value this file shows. If a value still shows as a placeholder here (option never configured), use its `default` in `${CLAUDE_SKILL_DIR}/../../.claude-plugin/plugin.json`.

Builds, grades or repairs the **agent-orchestration layer** of a repository's agentic documentation, in three scopes: `doctrine` (prose rules in the base doc: model ladder, delegation, parallelism under isolation), `agents` (subagent type definitions, a model x effort matrix, plus overrides of built-ins that inherit the session model), `checks` (the script verifying the two agree). Sibling of `/agents-md`; owns exactly one section of the file agents-md governs. Portable: it measures on every run and records non-guessable specifics in `.claude/orchestration.yml`.

Central promise: **never write what has not been verified.** No agent type that was not stat'd, no model not confirmed available, no parallelism rule without its isolation mechanism in the same section.

## Usage

```
/orchestration                              # auto: init if no layer exists, else audit (the choice is printed)
/orchestration init                         # build the layer (refuses per scope where it exists)
/orchestration audit                        # grade the existing layer, write nothing, report P0-P3
/orchestration sync                         # audit, then apply fixes (one plan confirmation)
/orchestration --scope=doctrine             # only the orchestration section of the base doc file
/orchestration --scope=agents               # only the subagent type definitions
/orchestration --scope=checks               # only the mechanical verification script
/orchestration audit --scope=agents,checks  # scopes combine with any mode and with each other
/orchestration --lang=en|fr|...             # force the output language instead of detecting
/orchestration --interactive                # full interview instead of autopilot defaults
/orchestration --dry-run                    # print the execution plan. Zero writes
/orchestration --help                       # print this Usage block and stop
```

With `--help`/`-h` and nothing else, print the Usage block verbatim and stop.

**Resolution order** for every policy answer, first match wins: command argument > project `.claude/orchestration.yml` > plugin option `${user_config.*}` (see the table below) > the recommended option of `${CLAUDE_SKILL_DIR}/references/interview.md`. An argument never overrides a **guardrail**: `init --scope=doctrine` on a base doc that already has an orchestration section still refuses and switches that scope to audit, and `--lang` never silently overrides a language rule the project states.

Plugin options (change them with `/config`; each maps to the `policy:` field of the same name):

| Option | Value now | Meaning |
|---|---|---|
| `orchestration_agents_location` | `${user_config.orchestration_agents_location}` | where agent type files live (global or project) |
| `orchestration_cost_posture` | `${user_config.orchestration_cost_posture}` | `cheapest-capable`, `balanced`, `capability-first` |
| `orchestration_matrix` | `${user_config.orchestration_matrix}` | `five-types`, `three-types`, `none` |
| `orchestration_deep_gate` | `${user_config.orchestration_deep_gate}` | when the top deep type may run |
| `orchestration_builtin_overrides` | `${user_config.orchestration_builtin_overrides}` | built-ins to override |
| `orchestration_delegation_threshold` | `${user_config.orchestration_delegation_threshold}` | when delegation is mandatory |
| `orchestration_delegation_rationale` | `${user_config.orchestration_delegation_rationale}` | include the context-economy sentence |
| `orchestration_delegation_fallback` | `${user_config.orchestration_delegation_fallback}` | what to do when delegation is unavailable |
| `orchestration_report_style` | `${user_config.orchestration_report_style}` | subagent report style |
| `orchestration_parallelism` | `${user_config.orchestration_parallelism}` | parallelism appetite |
| `orchestration_isolation` | `${user_config.orchestration_isolation}` | isolation policy |
| `orchestration_shared_tree_bans` | `${user_config.orchestration_shared_tree_bans}` | comma-separated shared-tree bans |
| `orchestration_cite_incident` | `${user_config.orchestration_cite_incident}` | cite the field incident in doctrine B3 |
| `orchestration_ask_before_dispatch` | `${user_config.orchestration_ask_before_dispatch}` | ask-before-dispatch posture |
| `orchestration_session_naming` | `${user_config.orchestration_session_naming}` | session naming variant |
| `orchestration_check_script_path` | `${user_config.orchestration_check_script_path}` | where the check script goes (`auto`: `.claude/orchestration/`, fixed) |
| `orchestration_report_language` | `${user_config.orchestration_report_language}` | language of reports to the user |

## Scope and non-goals

**For:** the rules an orchestrating agent follows to decompose, delegate, parallelize and isolate concurrent work; the subagent type files (name, description, model, effort, maxTurns, color) those rules cite and the built-in overrides; the check script aligning doctrine, config and installed types.

**Not for:**
- the rest of the base doc (behaviour, commands, architecture, guardrails): that is `/agents-md`, whose config this skill reads and never contradicts;
- wave or workstream tables of feature plans (per-task planning);
- creating the base doc itself: with no AGENTS.md or CLAUDE.md the doctrine scope stops and points at `/agents-md init`;
- wiring CI or hooks: the check script is written and the block to paste is handed over (it calls the script with `--only-owned`, so machine-local agent files and an absent global agents dir in CI never fail the build), `wired: false` until the human confirms. The same holds for `settings.json`: the `CLAUDE_CODE_SUBAGENT_MODEL` block is listed in the plan and written only once confirmed.

## Governing principles

These override any convenience, in all modes.

1. **One owner per section.** Write exactly one section of the base doc; read `.claude/agents-md.yml` first; audit reports on surrounding content, never touches it.
2. **The instruction budget is shared.** Every doctrine rule counts against the budget agents-md manages (size and counting method: `${CLAUDE_SKILL_DIR}/../agents-md/references/structure.md`, owned by the agents-md skill). Every added rule names what it buys; count, report, refuse to pad.
3. **Doctrine, config and machine agree.** Every agent type cited is stat'd on this machine; every model named is confirmed available or carries a fallback.
4. **Parallelism never ships without isolation.** Any rule permitting concurrent agents names its isolation mechanism (disjoint enumerated file sets, or git worktrees) in the same section.
5. **An optimization rule never blocks the task.** Every delegation or model rule carries its explicit fallback (do it yourself and say so).
6. **Never drop a prohibition.** Compression rewrites justifications, never imperatives. Any batch touching the doctrine ends with a mechanical non-regression check: prohibition count before and after, plus a grep for every ban marker.
7. **Unknown is a finding.** A check that could not run is a blind spot, never a green check or an assumption.
8. **Smallest adequate model, never blind.** Route each task to the cheapest rung of the dispatch ladder (agent types ordered by cost) adequate for it, never two rungs below the orchestrator's own estimate; the top model's standard type is the orchestrator's judgment. No escalation rule ships without a verification rule. Model facts are dated (`${CLAUDE_SKILL_DIR}/references/models.md`), never assumed current.

## Common preflight (all modes)

**Phase 0 - detect.** Load `${CLAUDE_SKILL_DIR}/references/detection.md`. If `.claude/orchestration/journal.md` shows an in-progress run younger than 24 h, resume at the last completed phase automatically and say so; an older journal is reported and ignored. Load `.claude/orchestration.yml` and run the detection probes regardless (independent: fan them out). D11 refreshes `models.md` when stale; D12 measures real spend per agent type by running in place `python3 ${CLAUDE_SKILL_DIR}/scripts/usage_by_agent_type.py --days 30` (never copied). On drift of a human-authored field, keep it and report the diff, do not ask. Announce the detected profile, the per-scope mode routing and the output language in a few lines; no confirmation here.

**Mode selection.** Bare `/orchestration`: `init` if no orchestration layer exists (no section, no agent types, no check), else `audit`. Print the choice; do not ask.

**Phase 1 - resolve policy.** Autopilot by default per the resolution order above and `${CLAUDE_SKILL_DIR}/references/interview.md`. Ask only the three blocking cases listed there. `--interactive` runs the full interview in salvos of at most 4 questions (plain-text questions if AskUserQuestion is absent; report the degradation).

## Dry run (`--dry-run`, or a request to "show what it would do" / "write nothing")

Applies to every mode. **Zero writes of any kind**: no project file, no `.claude/` directory, no journal, no config, no copied script, no `models.md` refresh (report stale model facts as a blind spot instead), no `settings.json`. Only the probes of Phase 0 run, and they do run for real (read-only, one tool call each, fanned out): never report a probe result (agent types, isolation, usage, model facts) that was not obtained from a command in this run, and report any probe the sandbox blocked as a blind spot. Never ask policy questions: apply the resolution order and label each decision's source.

Phases 0, 1 and 2 run, then stop. Print, in this order: (1) `Mode: <init|audit|sync> (dry run)` and the detected profile; (2) **one plan**: a table with one row per file a real run would write (doctrine section in the base doc, each agent type file, the `Explore` override, the `settings.json` block, the check script, `.claude/orchestration.yml`), columns file, action, source of the decision (argument, project, plugin option, recommended); (3) the doctrine rules the plan would add, with the parallelism rule shown together with its isolation mechanism and the prohibitions it would keep; (4) budget before and after; (5) blind spots; (6) a last line stating `Nothing was written` and that the base doc is unchanged. Then stop: no Phase 3, no confirmation prompt, and no claim that an environment limit blocked the real run unless a probe showed it.

## Mode: init

Builds the layer from scratch. **Refuses per scope where the artifact already exists** (doctrine section, agent types, check script) and switches that scope to `audit`; remaining scopes proceed. Say so plainly, never overwrite. The agents-md isolation stub or a legacy agents-md "Concurrency isolation" subsection (D2) is not an existing orchestration section: it is absorbed into the new one and does not switch the doctrine scope to audit.

**Phase 2 - propose.** Assemble the doctrine blocks (`${CLAUDE_SKILL_DIR}/references/doctrine-content.md`), the agent matrix and built-in overrides (`${CLAUDE_SKILL_DIR}/references/agent-types.md`, priced with `models.md`) and the check, each block with its instruction cost against the margin from probe D4. Every block justified or dropped. Say in the plan when a legacy "Concurrency isolation" subsection is absorbed (D2) and when B4 is omitted as redundant (interview Q4.1). Present **one plan**: files to write (doctrine section, agent types incl. global ones, `Explore` override, `settings.json` block, check script, config), each decision with its source (argument, project, plugin option, recommended), the budget. **One confirmation for the whole plan**: the run's only stop in autopilot.

**Phase 3 - write.** Exactly what the confirmed plan lists: the doctrine section rendered in the output language; the agent `.md` files (and the `Explore` override) at the chosen location, skipping identical installed global types; the `settings.json` block; `check_agent_refs.py` copied from `${CLAUDE_SKILL_DIR}/scripts/` to `.claude/orchestration/` (fixed location, as part of the confirmed plan), stamped on copy: `sed "2s/__PLUGIN_VERSION__/<version>/"` with `version` read from `${CLAUDE_SKILL_DIR}/../../.claude-plugin/plugin.json`, the marker line being the only difference from the canonical script, together with the Checker triage moves and version replacements of the plan; `.claude/orchestration.yml`. Never write outside the plan.

**Phase 4 - verify your own output** (not optional). Stat every cited path. Parse every frontmatter written. Run the check script against what was written. Newly written agent type files (and overrides such as `Explore`) are visible to the Agent tool only after the harness reloads them (a "new agent types available" notice). Before that, dispatch fails with "Agent type not found", and a built-in such as `Explore` silently runs on its built-in definition (the parent model), not on the override. So: wait for the reload notice and then dispatch one minimal read-only task per new type, or defer this verification to the next session and report it as a blind spot. **Never validate a type or override from the mere fact that it answered**: confirm the resolved model from the transcript (`python3 ${CLAUDE_SKILL_DIR}/scripts/usage_by_agent_type.py`, "Resolved models"). Recount the budget. Fix or remove whatever fails.

**Phase 5 - report.** What was written, what was left out and why, what stays `wired: false`, the plugin options that drove the choices (change them with `/config`), budget before and after.

## Mode: audit

Zero writes. Runs the grid of `${CLAUDE_SKILL_DIR}/references/audit-checks.md` for the selected scopes; cross-scope checks (dead references, contradictions) run whenever one involved scope is selected. Findings ranked P0 to P3 with evidence (file:line or probe output). **Label every finding with its literal rank** (`P0`, `P1`, `P2` or `P3`) in the report, never only prose severity words. **Number every finding `OR-NN`** (`OR-01`, `OR-02`, ...): unique, in report order (most severe first), never renumbered afterwards; a later `sync` plan reuses the same IDs unchanged. Each finding carries a `Fix:` line (the concrete correction, or the question to settle) and, when the fix is a real choice, an `Options:` line with 2-3 options, the recommended one first. End with the line `Nothing was written`.

Eight families: **dead references**, **contradictions** (never auto-resolved), **doctrine gaps** (parallelism without isolation in the same section is P0; a mandatory rule without fallback is P0), **budget** (the section's share, with named cut candidates), **language**, **agent file hygiene**, **check wiring** (`wired: true` without CI evidence is a false fact), **model economy** (routine xhigh tiers, escalation gated on self-confidence, built-ins inheriting the top model, measured spend contradicting the doctrine).

No finding without evidence. Every check that could not run is reported as a blind spot.

## Mode: sync

Runs `audit`, then applies fixes in **batches**, most valuable first. Autopilot shows all batches as one plan with one confirmation, then applies them in order with checks between; `--interactive` confirms each batch. Three operations, never mixed within a batch. The agents-md isolation stub or a legacy agents-md "Concurrency isolation" subsection (D2) is absorbed in Align: moved into the owned section, every rule kept, the non-regression count below applies, and the plan says so.

- **Correct.** Dead references and false facts. Always first.
- **Align.** Doctrine, config and agent files back to agreement. The plan names the side taken as source of truth per finding (autopilot: plugin options and the canonical matrix for agent types; installed files for facts about this machine); never pick a side silently.
- **Compress and translate.** Budget cuts and language fixes, last. Keep the imperative and the threshold; move the justification out.

Sync writes to the base doc only inside the recorded `section_spans` (`${CLAUDE_SKILL_DIR}/references/config-schema.md`); a span that no longer matches is a finding, never a re-anchor. Sync fixes only inside the selected scopes; a cross-scope finding whose fix lies outside is reported as "out of selected scope, re-run with --scope=...".

**Always print the plan first**, in the reply, before the first edit, even when the user already said they confirm it: `Mode: sync`, then the batches (Correct, Align, Compress) with each finding, its evidence and the fix. The final message of the run must contain, in this order, whatever the size of the document: `Mode: sync`; `Plan` (the batches as applied, each finding ranked P0 to P3 under its audit `OR-NN` ID); `Result` (the new section verbatim); `Non-regression` (below), as a literal line `Non-regression: prohibitions <N before> -> <N after>; markers <each marker> OK|MISSING` (the numbers and the per-marker grep result must appear; a prose sentence like "bans are still there" does not count). A reply that only shows the new text, or that lacks this line, is an unfinished sync. Run every probe in the foreground during a sync: a background task that completes after the report produces a later message that replaces it as the final one. A dead agent type (cited but stat'd nowhere) is a Correct finding: replace it by an installed type or by a neutral "a subagent" wording, and report the dead name. A parallelism rule without isolation gets its mechanism added in the same section (Align).

**Prohibition count.** Count each distinct banned command or imperative "never/do not" clause separately (a line banning four commands is four prohibitions). Rewording must keep every one.

**After every batch that touched the doctrine**, run the non-regression check: prohibition count before and after must match unless a merge was explicitly approved, and every marker in `doctrine.prohibition_markers` (default: `git stash`, `git add -A`, `git checkout`, `git reset`) must still be greppable. Report both numbers and the marker grep result in a closing block, e.g. `Non-regression: prohibitions 4 -> 4; markers git stash OK, git add -A OK, git checkout OK, git reset OK`. A sync that cannot show this check has not finished; this holds even for a tiny base doc, and even when the only batch is a rewrite meant to shorten the section. **After every batch that wrote agent files**, run the Phase 4 agent checks (parse, check script, resolved-model confirmation per new or re-modeled type, or deferred as a blind spot per Phase 4).

**Checker triage (init, audit, sync).** Detection D10 finds every `check_agent_refs.py` and every file with the marker `dev-skills: orchestration`. A copy outside `.claude/orchestration/` is moved there with `git mv`, and every reference is updated (CI workflows, pre-commit config, Makefile, package.json scripts, docs, `.claude/orchestration.yml`), wired or not. Then the moved script is re-run from its new location, and every updated hook or target that can run locally. Audit reports each move as O7.4 (P3) and writes nothing; init and sync include the moves in the single plan. `/agents-md` performs the same triage for all agentic scripts, whichever skill runs first.

**Copy version (audit, sync).** Compare each project copy with the canonical `${CLAUDE_SKILL_DIR}/scripts/check_agent_refs.py`, using the marker version and `plugin.json`. An older unedited copy is replaced in the plan (O7.5). A locally edited copy gets its diff shown in the plan and is never overwritten blindly; its extra capabilities go to the report as upstream candidates (O7.6).

## Reference files

Load on demand, not upfront:

| File | When |
|---|---|
| `${CLAUDE_SKILL_DIR}/references/detection.md` | Phase 0 of any mode |
| `${CLAUDE_SKILL_DIR}/references/interview.md` | Phase 1 (autopilot precedence, or the full interview with `--interactive`), and any sync batch that changes policy |
| `${CLAUDE_SKILL_DIR}/references/doctrine-content.md` | Writing or grading the doctrine scope |
| `${CLAUDE_SKILL_DIR}/references/models.md` | Phase 0 (refresh via D11), and whenever a model or effort is chosen or graded |
| `${CLAUDE_SKILL_DIR}/references/agent-types.md` | Writing or grading the agents scope |
| `${CLAUDE_SKILL_DIR}/references/audit-checks.md` | Modes audit and sync |
| `${CLAUDE_SKILL_DIR}/references/config-schema.md` | Reading or writing `.claude/orchestration.yml` |

`${CLAUDE_SKILL_DIR}/templates/` holds the skeletons. `${CLAUDE_SKILL_DIR}/scripts/check_agent_refs.py` is copied into the project only as part of the confirmed plan (`--only-owned` flag: see its docstring); `${CLAUDE_SKILL_DIR}/scripts/usage_by_agent_type.py` (probe D12) is run in place, never copied.

## Language

The skill package is English. **Output adapts to the detected language of the base doc**: a French AGENTS.md gets a French section and French subagent descriptions. `--lang` overrides detection. Reports to the user follow `${user_config.orchestration_report_language}`; auto = the user's conversation language, fallback en.

**A language rule stated by the project** (a guardrail imposing one language for all documentation) wins over `--lang` unless the human, shown the quoted rule and its location, decides otherwise. Never override silently; record the resolution in the config. Canonical content is English in the reference files and is rendered, not copied, at write time.
