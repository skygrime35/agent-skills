---
name: orchestration
argument-hint: "[init|audit|sync] [--scope=doctrine,agents,checks] [--lang=en|fr] [--dry-run] [--help]"
description: "Use to create, audit, or update the AGENT-ORCHESTRATION layer of a project's agentic documentation: the doctrine that tells an orchestrating agent how to decompose work, choose models, delegate, parallelize and isolate concurrent agents, plus the subagent type definitions (model x effort matrix) and the mechanical checks that keep those rules real. One governed run: detect the base doc (CLAUDE.md, AGENTS.md, or a pointer chain) and its language, read the agents-md config it must never contradict, inventory the installed subagent types, refresh the dated model facts (lineup, prices, efforts) and measure real spend per agent type from local transcripts, resolve cost, delegation, parallelism and isolation policy autonomously from the user's machine-wide defaults (one plan confirmation, no interview unless --interactive), then write only the orchestration section within the shared instruction budget. Three modes: init builds a missing layer; audit grades doctrine, agent types and checks, writing nothing, reporting P0-P3 findings; sync applies audit fixes in batches under one plan confirmation, never dropping a prohibition. Portable via auto-detection + a .claude/orchestration.yml config; unknowns become blind spots."
---

# /orchestration

Build, grade, or repair the **agent-orchestration layer** of any repository's agentic documentation, in three separately invocable scopes: `doctrine` (the prose rules in the base doc file: model ladder, delegation, parallelism under isolation), `agents` (the subagent type definitions, a model x effort matrix from the cheapest tier to the top one, plus overrides of the built-ins that would otherwise inherit an expensive session model), and `checks` (the script that verifies the two agree). It is the sibling of `/agents-md` and owns exactly one section of the file agents-md governs.

This skill is **portable across any project**. It measures on every run (base doc file and its language, installed agent types global and project-local, instruction budget, isolation substrate, dated model facts) and records the non-guessable specifics in a per-project `.claude/orchestration.yml`.

Its central promise is a negative one: **it never writes what it has not verified.** Not an agent type it did not stat, not a model it was not told is available, not a parallelism rule without its isolation mechanism in the same section.

## Usage

```
/orchestration                              # interactive: detect, then propose init or audit
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

If invoked with `--help`/`-h` and nothing else, print the Usage block above verbatim and stop.

Arguments override questions. An argument never overrides a **guardrail**: `init --scope=doctrine` on a base doc that already has an orchestration section still refuses and switches that scope to audit, and `--lang` never silently overrides a language rule the project itself states.

## What this skill is for / non-goals

**For:** the rules an orchestrating agent follows to decompose, delegate, parallelize and isolate concurrent work; the subagent type files (name, description, model, effort, maxTurns, color) those rules cite, and the overrides of built-in agents; the check script that keeps doctrine, config and installed types mechanically aligned.

**Not for:** the rest of the base doc file. Behaviour rules, commands, architecture and guardrails belong to `/agents-md`, whose config this skill reads and never contradicts. **Not for** wave or workstream tables in feature plans: that is per-task planning, not standing doctrine. **Not for** creating the base doc file itself: on a repository with no AGENTS.md or CLAUDE.md, the doctrine scope stops and points at `/agents-md init`. **Not for** wiring CI or hooks: it writes the check script and hands you the block to paste, `wired: false` until you confirm. Likewise for `settings.json`: the `CLAUDE_CODE_SUBAGENT_MODEL` block is listed in the plan and written only once the plan is confirmed.

## Governing principles

These override any convenience, in all three modes.

1. **One owner per section.** The base doc belongs to `/agents-md`; this skill writes exactly one section of it, reads `.claude/agents-md.yml` first, and its audit reports on surrounding content without ever touching it. Two skills editing one file without a boundary rewrite each other's work and neither notices.
2. **The instruction budget is shared, not granted.** Every doctrine rule counts against the same 150-200 instruction budget agents-md manages, of which the harness already spends about 50. Past the threshold, a rule you add silently replaces one already there. Every added rule must name what it buys; count, report, refuse to pad.
3. **Doctrine, config and machine must agree.** Every agent type the doctrine cites is stat'd on this machine; every model named is confirmed available or carries a fallback. A doctrine citing an `opus-standard` that does not exist sends every dispatch into a silent downgrade.
4. **Parallelism never ships without isolation.** Any rule permitting concurrent agents names its isolation mechanism (disjoint enumerated file sets, or git worktrees) in the same section. Field incident: one agent's `git stash` carried away another's work, left an orphan migration and no backend tests running, with no error message anywhere.
5. **An optimization rule never blocks the task.** Every delegation or model rule carries its explicit fallback (do it yourself and say so). An absolute with no workable exception stops work in any harness that restricts subagents.
6. **Never drop a prohibition.** Sync compression rewrites justifications, never imperatives. Any batch touching the doctrine ends with a mechanical non-regression check: prohibition count before and after, plus a grep for every ban marker.
7. **Unknown is a finding, not a gap to fill.** A check that could not run is reported as a blind spot. Never a green check, never an assumption dressed as a conclusion.
8. **Smallest adequate model, never blind.** The doctrine routes each task to the cheapest rung of the dispatch ladder (the agent types ordered by cost) adequate for it, never two rungs below the orchestrator's own estimate, and leaves the top model's standard type to the orchestrator's judgment. A cheaper rung is only as safe as the objective check behind it: no escalation rule ships without a verification rule, and model facts are dated (`references/models.md`), never assumed current.

## Mode: init

Builds the layer from scratch. **Refuses per scope where the artifact already exists** (doctrine section found, agent types found, check script found) and switches that scope to `audit`; the remaining scopes proceed. Say so plainly, never overwrite.

**Phase 0 - preflight (all modes).** Resume from `.claude/orchestration/journal.md` if an in-progress run exists (offer to continue at the last completed phase). Load `.claude/orchestration.yml` and re-run the detection probes of `references/detection.md` regardless; they are independent, fan them out. Probe D11 refreshes `references/models.md` when it is stale; probe D12 measures real spend per agent type from local transcripts. On drift with a human-authored field, show the diff and ask. Announce the detected profile, the per-scope mode routing and the output language in a few lines, and continue: no confirmation here.

**Phase 1 - resolve policy.** **Autopilot by default** (`references/interview.md`): every answer comes from an argument, the project's recorded policy, the user's `~/.claude/orchestration-defaults.yml`, or the recommended option, in that order. No question is asked except the three blocking cases listed there (ambiguous base doc, language-rule conflict, contradiction with another rule of the base doc). `--interactive` runs the full interview in salvos of at most 4 questions.

**Phase 2 - propose.** Assemble the doctrine block set (`references/doctrine-content.md`), the agent matrix and built-in overrides (`references/agent-types.md`, priced with `references/models.md`) and the check, each block with its instruction cost against the measured budget margin from probe D4. Every block justified or dropped. Present it as **one plan**: files to write (doctrine section, agent types, global ones included, `Explore` override, `settings.json` block, check script, config, user defaults file), each decision with its source, the budget. **One confirmation for the whole plan**: this is the run's only stop in autopilot.

**Phase 3 - write.** What the plan confirmed: the doctrine section into the base doc, rendered in the output language; the agent `.md` files (and the `Explore` override per Q1.4) at the location chosen in Q0.1, skipping global types already installed and identical; the `settings.json` block; `check_agent_refs.py` into the project; `.claude/orchestration.yml`; `~/.claude/orchestration-defaults.yml` if it did not exist.

**Phase 4 - verify your own output.** Stat every path cited. Parse every frontmatter written. Run the check script against what was just written. For each newly written type, dispatch one minimal read-only task and confirm from its transcript's `model` field that the alias resolved to the expected model. Recount the instruction budget. Fix or remove whatever fails. **This phase is not optional**: it is the difference between this skill and a template generator.

**Phase 5 - report.** What was written, what was deliberately left out and why, what stays `wired: false` awaiting the human, the defaults file used or created, and the budget before and after.

## Mode: audit

Zero writes. Runs the check grid of `references/audit-checks.md` for the selected scopes; cross-scope consistency checks (dead references, contradictions) run whenever at least one involved scope is selected. Findings ranked P0 to P3, most severe first, each with the evidence that produced it (file:line or probe output).

The eight families: **dead references** (doctrine citing agent types installed nowhere), **contradictions** (doctrine vs config vs installed types vs agents-md, never auto-resolved), **doctrine gaps** (parallelism without isolation in the same section is P0; a mandatory rule without fallback is P0), **budget** (the section's share of the overrun, with named cut candidates), **language** (section vs doc vs stated rule), **agent file hygiene** (frontmatter schema, spawn-oriented descriptions, closing reporting instruction), **check wiring** (`wired: true` without CI evidence is a false fact), **model economy** (routine xhigh tiers, escalation gated on self-confidence, built-ins inheriting the top model, measured spend contradicting the doctrine).

No finding without evidence. Every check that could not run is itself reported as a blind spot.

## Mode: sync

Runs `audit`, then applies fixes in **batches**, most valuable first. In autopilot, all batches are shown as one plan with one confirmation, then applied in order with their checks between them; `--interactive` confirms each batch. Three operations, never mixed within a batch:

- **Correct.** Dead references and false facts. Lowest risk, highest value, always offered first.
- **Align.** Doctrine, config and agent files brought back to agreement. The plan names the side taken as source of truth for each finding (in autopilot: the user defaults and the canonical matrix for agent types; the installed files for facts about this machine); a side is never picked silently.
- **Compress and translate.** Budget cuts and language fixes, last. Keep the imperative and the threshold; move the justification out.

Sync fixes only inside the selected scopes; a cross-scope finding whose fix lies outside the selection is reported with "out of selected scope, re-run with --scope=...".

**After every batch that touched the doctrine**, run the non-regression check: prohibition count before and after must match unless a merge was explicitly approved, and every marker in `doctrine.prohibition_markers` (by default the four shared-tree bans: `git stash`, `git add -A`, `git checkout`, `git reset`) must still be greppable. Report both numbers. A sync that cannot show this check has not finished. **After every batch that wrote agent files**, run Phase 4's agent checks on them (parse, check script, one resolution dispatch per new or re-modeled type).

## Reference files

Load on demand, not upfront:

| File | When |
|---|---|
| `references/detection.md` | Phase 0 of any mode |
| `references/interview.md` | Phase 1 of init (autopilot defaults, or the full interview with `--interactive`), and any sync batch that changes policy |
| `references/doctrine-content.md` | Writing or grading the doctrine scope |
| `references/models.md` | Phase 0 (refresh via D11), and whenever a model or effort is chosen or graded |
| `references/agent-types.md` | Writing or grading the agents scope |
| `references/audit-checks.md` | Modes audit and sync |
| `references/config-schema.md` | Reading or writing `.claude/orchestration.yml` |

`templates/` holds the skeletons; `scripts/check_agent_refs.py` is the check copied into the target project on request; `scripts/usage_by_agent_type.py` is probe D12, run in place, never copied.

## Language

The skill package is written in English. Its **output adapts to the detected language of the base doc file**: a French AGENTS.md gets a French orchestration section and French subagent descriptions; an English one gets English. `--lang` overrides detection.

**If the project states a language rule** (a guardrail imposing one language for all documentation), it wins over `--lang` unless the human, shown the quoted rule and its location, decides otherwise. Never silently override; record the resolution in the config. Canonical content lives in English in the reference files and is rendered, not copied, at write time.
