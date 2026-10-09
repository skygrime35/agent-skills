# Interview

Runs in Phase 1 of `init`, and in `sync` only when a batch changes policy. The goal is to give every doctrine variation point an answer.

## Autopilot (default)

**By default the skill asks no policy question.** Every answer below is resolved, first match wins:

1. a command-line argument;
2. the project's recorded `policy:` in `.claude/orchestration.yml`;
3. the user's defaults file `~/.claude/orchestration-defaults.yml` (same layout as `policy:`, plus `agents.location`), which is what keeps the orchestration identical across projects;
4. the answer marked **(Recommended)** in this file, applied with the probe results (D5, D6, D9, D11, D12) that the recommendation depends on.

Q1.1 has no recommended option: in autopilot the available models are the current lineup of `references/models.md` (after D11), minus any model whose resolution dispatch fails in Phase 4.

No defaults file on this machine: write it at the end of the run with the answers actually used, so the next project inherits them.

Only these may still interrupt the run, each because no default can be safe:
- **Q0.2** several candidate base docs or orchestration headings (D1/D2 ambiguous);
- **Q4.3** a language conflict with a rule the project states (guardrail, never resolved silently);
- an **O2.3 contradiction** with a rule elsewhere in the base doc (for example "never spawn subagents").

Everything else, including the creation of global agent types on a machine that has none and the `settings.json` block, goes into the **single plan confirmation of Phase 2**, listed as decisions taken with the source of each (argument, project, user defaults, recommended). The human can amend any line there; that is the only stop.

`--interactive` restores the full interview below. It is also the way to change the user defaults: answers given interactively are offered for saving into `~/.claude/orchestration-defaults.yml`.

## Full interview (`--interactive`)

Rules:

- Salvos of **at most 4 questions** via AskUserQuestion, general to precise.
- Mark the recommended option "(Recommended)" and put it first. Use multiSelect where choices are not exclusive.
- **Skip any question already answered** by an argument, a `policy:` field in the config, or a detection probe. A recorded decision is a fact, not a question.
- Stop when a new question would no longer change what gets written.
- An unanswered question becomes a registered gap in the report, never a guessed value.

Every question states its effect on the output. That effect is the reason the question exists; a question with no effect is cut.

## S0 - Placement (init only)

- **Q0.1 Where do the agent type files live?** [Global `~/.claude/agents/`, shared across this machine's projects; the doctrine will carry the documented fallback for other machines (Recommended when probe D5 already found global types) | Project `.claude/agents/`, versioned, travels with the repo]. Effect: `agents.location`, the location note and fallback wording in doctrine block B1, where Phase 3 writes the files.
- **Q0.2 Confirm the base doc and section placement.** Only if D1/D2 were ambiguous (several candidate files, several candidate headings). Effect: `base_doc.file`, `base_doc.section_heading`.

## S1 - Cost posture and models

Five questions, so two salvos: Q1.1 to Q1.3, then Q1.4 and Q1.5. Present alongside the dated facts of `references/models.md` (refreshed by probe D11) and this machine's measured cost per agent type (probe D12) when transcripts exist.

- **Q1.1 Which models are available here?** multiSelect over the current lineup in models.md (for example Fable, Opus, Sonnet, Haiku). Effect: the ladder in B1 lists only these, in capability order; `local.models_available`; the matrix's `{LOW}`/`{MID}`/`{TOP}` and the missing-tier rules in agent-types.md.
- **Q1.2 Cost posture?** [Cheapest adequate agent type per subtask, estimated at planning time, never two rungs below the estimate on the ladder of types ordered by cost, escalating one rung on verified failure (Recommended) | Balanced: `{MID}-standard` by default, lower only for clearly mechanical work, higher only for clearly hard work | Capability-first: economize only on mechanical tasks]. Effect: B1's selection sentence, B7's escalation paragraph, B2's threshold default, `policy.cost_posture` (values `cheapest-capable`, `balanced`, `capability-first`).
- **Q1.3 Agent matrix?** [Five types `{LOW}-quick`, `{LOW}-standard`, `{MID}-standard`, `{TOP}-standard`, `{TOP}-deep` (Recommended when a low, a mid and a top model are available) | Three types, one per tier at medium effort | None, model parameter only]. Effect: how many files the `agents` scope writes; B1's effort paragraph present or absent.
- **Q1.4 Override the built-ins that inherit the session model?** multiSelect: [An `Explore` agent on `{LOW}`, read-only (Recommended) | `CLAUDE_CODE_SUBAGENT_MODEL={MID}` in settings.json, so `general-purpose` and model-less agents stop inheriting the top model (Recommended)]. Effect: the `Explore.md` file, the proposed settings block (written only on confirmation), `policy.builtin_overrides`.
- **Q1.5 When may `{TOP}-deep` run?** [Only on the user's explicit request to dig deeper, or after `{TOP}-standard` failed on the same task (Recommended) | At the orchestrator's judgment]. Effect: B1's `{DEEP_GATE}` sentence, the type's description, `policy.deep_gate`. Skipped when the matrix has no `{TOP}-deep`.

## S2 - Delegation

- **Q2.1 Delegation threshold?** [Mandatory as soon as a task needs exploration, iteration, or several files; below that the main agent does it itself (Recommended) | Mandatory only for large multi-file work | Advisory, never mandatory]. Effect: B2's threshold sentence and vocabulary ("mandatory" vs "preferred"), `policy.delegation_threshold`.
- **Q2.2 Include the context-economy rationale?** [One sentence: a file read by the main agent is re-billed every following turn, read by a subagent it is paid once (Recommended, it is why the rule exists) | Omit, imperative only]. Effect: B2 length, one instruction of budget.
- **Q2.3 Fallback when delegation is unavailable?** [The main agent does it itself and says so; an optimization rule never blocks the task (Recommended) | Stop and ask]. Effect: B2's fallback clause. "Stop and ask" is written if chosen, with a stated warning: it converts an optimization into a blocker, which audit O3.2 will keep flagging.
- **Q2.4 Subagent report style?** [High-density findings, no execution narrative (Recommended) | Free form]. Effect: B6 present or absent.

## S3 - Parallelism and isolation

- **Q3.1 Parallelism appetite?** [Parallelize unrelated requests by default, never queue an independent request (Recommended) | Only on explicit user request | Never]. Effect: B3's opening; "Never" collapses B3 to a two-line prohibition and skips Q3.2 to Q3.4.
- **Q3.2 Isolation policy?** [Escalating: disjoint enumerated file sets when no agent commits; git worktrees mandatory when perimeters may overlap, an agent commits or stashes, or a migration is in play (Recommended) | Worktrees always | Disjoint file sets only, warned: unprotected the moment an agent commits]. Effect: B3's two forms and triggers, `policy.isolation`. The migration trigger appears only if probe D9 found a migration framework.
- **Q3.3 Shared-tree bans?** [The four: `git stash`, `git add -A`, `git checkout`, `git reset` (Recommended) | Customize the list]. Effect: B3's ban list AND the exact markers sync's non-regression grep protects (`doctrine.prohibition_markers`).
- **Q3.4 Cite the field incident as justification?** [One-line citation: a stash that carried away another agent's work, an orphan migration, no error anywhere (Recommended, it is what makes the rule stick) | Omit]. Effect: B3 length.

## S4 - Interaction and naming

- **Q4.1 Ask-before-dispatch posture?** [Ask the user freely, as much as needed, whenever intent is ambiguous, before decomposing (Recommended) | Minimize questions, bias to action]. Effect: B4 present or absent.
- **Q4.2 Session naming?** Pre-answered by probe D6. Statusline present: [Task description only, no model/effort prefix, badge shows them; fallback format documented for machines without it (Recommended) | Always prefix]. Statusline absent: [Prefix format `model(effort): task` (Recommended) | Task description only]. Effect: B5 variant.
- **Q4.3 Language resolution.** Only if probe D7 found a conflict. Quote the stated rule and its location, list the options, record the decision in `policy.language_resolution`.
- **Q4.4 Where does the check script go?** [`scripts/` next to the project's other checkers (Recommended when scripts/ exists) | `.claude/orchestration/` | Skip the checks scope]. Effect: `checks[].path`, `wired: false` regardless.

## Answer-to-artifact map

| Question | Doctrine block | Config field | Files |
|---|---|---|---|
| Q0.1 | B1 location note + fallback | `agents.location`, `agents.path` | where agent .md files land |
| Q1.1 | B1 ladder | `local.models_available` | matrix `{LOW}`/`{MID}`/`{TOP}` |
| Q1.2 | B1 selection sentence, B7, B2 threshold | `policy.cost_posture` | |
| Q1.3 | B1 effort paragraph, B7 cheap review, B8 second sentence | `policy.matrix`, `agents.types` | 0, 3, 4 or 5 agent files (4 when no low model: see missing tiers) |
| Q1.4 | | `policy.builtin_overrides` | `Explore.md`, settings.json env block (on confirmation) |
| Q1.5 | B1 deep gate | `policy.deep_gate` | `{TOP}-deep` description |
| Q2.1 | B2 threshold | `policy.delegation_threshold` | |
| Q2.2 | B2 rationale sentence | `policy.delegation_rationale` | |
| Q2.3 | B2 fallback clause | `policy.delegation_fallback` | |
| Q2.4 | B6 | `policy.report_style` | |
| Q3.1 | B3 opening or collapse | `policy.parallelism` | |
| Q3.2 | B3 forms and triggers | `policy.isolation` | |
| Q3.3 | B3 ban list | `policy.shared_tree_bans`, `doctrine.prohibition_markers` | check script markers |
| Q3.4 | B3 incident line | `policy.cite_incident` | |
| Q4.1 | B4 | `policy.ask_before_dispatch` | |
| Q4.2 | B5 variant | `policy.session_naming` | |
| Q4.3 | rendering language | `policy.language_resolution` | |
| Q4.4 | | `policy.check_script_path`, `checks[].path` | check script location |
