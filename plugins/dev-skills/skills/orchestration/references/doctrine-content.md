# Doctrine blocks

Contents: B1 Model ladder | B7 Escalation | B2 Delegation | B3 Parallelism and isolation | B4 Ask before dispatch | B5 Session naming | B6 Reporting | B8 Briefing

The menu of orchestration rules this skill can write into the base doc's owned section. Eight blocks, B1 to B8, generalized from a field-proven production system and from the practices summarized in `references/models.md`. For each: purpose, canonical text (English render source), variation points keyed to interview answers, instruction cost, and when to omit it. Block IDs are stable identifiers, not reading order: the written section follows the order of `templates/doctrine-section.md.tmpl` (B1, B7, B2, B8, B3, B4, B5, B6).

**Boundary note.** Branch discipline (check the branch and cohabitation before any modification), general output style, and knowledge-graph usage belong to the base doc's behaviour section, owned by `/agents-md`. This skill never writes them; its audit only reports overlap when the owned section restates them.

**Rendering.** The canonical text below is the SOURCE, in English. At write time it is rendered into the output language decided in Phase 0 (a French base doc gets French prose), with the interview's variation points applied. Rendered, not copied: sentence order and idiom may adapt, imperatives and thresholds may not.

**Budget.** The full eight blocks cost roughly 29 to 34 instructions. Phase 2 must show the measured margin from probe D4 before proposing all eight; on a tight budget, propose B1+B7+B2+B3 (the load-bearing four) and justify dropping the rest.

## B1 - Model ladder and orchestrator role

Purpose: stop expensive models doing cheap work without under-sizing hard work, and keep the dispatch decision at planning time.

Canonical text:

> Token economy rule: never let a costly model handle a task a cheaper one does correctly. Order of capability (and cost), highest first: {LADDER}.
>
> **The orchestrator is a role, not a model**: it is the agent in direct dialogue with the user, whatever model runs it. Its job is to decompose the request and delegate each subtask to the **smallest model adequate for it**. The dispatch ladder is the list of agent types ordered by cost ({TYPE_LADDER}). At planning time, before execution starts, the orchestrator estimates the rung each subtask needs and dispatches at that rung, or one rung below when it hesitates between two; **never two rungs below its estimate**. A slight under-sizing is accepted because a failure escalates ({B7_REF}); a gross one only wastes the attempt. The orchestrator does not itself do work a lower model would do as well.{LOW_DEFAULT: **Delegated implementation starts at `{LOW}-standard`** whenever the orchestrator can write its brief (files, intended behaviour, verification); a higher rung needs a reason: a design choice the brief cannot settle, a cause still unknown, security- or data-sensitive work.}{DEEP_GATE: `{TOP}-deep` runs only when the user explicitly asks to dig deeper, or after `{TOP}-standard` failed on the same task.}
>
> The number of agents follows the task: one for a simple task, more only when the work splits into independent parts. Independent agents are launched **in parallel**, subject to the isolation required by {B3_REF}, which is its precondition, not an optional precaution.
>
> {EFFORT_AXIS: Model choice and reasoning depth (effort) are calibrated together through dedicated subagent types defined in {AGENTS_PATH}{LOCATION_NOTE}: {TYPE_LIST}. If these types are not available on the executing machine, fall back to model selection alone (the `model` parameter of the Agent tool) and the default session effort.}

Variation points:
- `{LADDER}` pruned to Q1.1's available models (models.md tiers, plus Fable above the matrix when available).
- Q1.2 sets the selection sentence: **cheapest-capable** (recommended) writes it as above; **balanced** replaces it with "default to `{MID}-standard`; go lower only for clearly mechanical work, higher only for clearly hard work"; **capability-first** with "economize only on mechanical tasks". The "never two rungs below" clause is kept under every posture.
- `{TYPE_LADDER}` lists the generated types cheapest first (for example `haiku-quick` < `haiku-standard` < `sonnet-standard` < `opus-standard` < `opus-deep`); with no types (Q1.3 "None"), it lists the available models cheapest first. A rung is one entry of that list: a task estimated at `sonnet-standard` may start at `haiku-standard`, never at `haiku-quick`. When `{EFFORT_AXIS}` is present, write `{TYPE_LIST}` in that same cheapest-first order and let `{TYPE_LADDER}` point to it ("the types listed below, in that order") instead of listing them twice.
- `{LOW_DEFAULT}` present when the matrix has a `{LOW}-standard` type and the posture is cheapest-capable. It counters the observed bias: without it, orchestrators sent fully briefed edits to the mid tier and never used the bottom one.
- `{DEEP_GATE}` per Q1.5: present (recommended) or replaced by "`{TOP}-deep` at the orchestrator's judgment". Dropped when the matrix has no `{TOP}-deep`.
- `{EFFORT_AXIS}` present only if Q1.3 chose an effort matrix; `{LOCATION_NOTE}` reads "(machine-local configuration, absent if this repo is cloned elsewhere)" when Q0.1 chose global, and is dropped when project-local; `{TYPE_LIST}` names the actually generated types with one clause each. The fallback sentence is **mandatory** whenever `{EFFORT_AXIS}` is present (audit O3.5).

Cost: 7-9 instructions. Omit only if the project runs a single model with no delegation (then B2 is also moot and the doctrine scope is probably not worth writing).

## B7 - Escalation on verified failure

Purpose: make "start small" safe. A cascade only saves money when failures are caught by an objective check; a small model's self-assessment fails exactly where escalation is needed.

Canonical text:

> A delegated result counts as done only once **checked objectively**: the tests, build or lint the brief named, or a review by another agent. The executing agent's own confidence is not a check.{CHEAP_REVIEW: When no automated check covers the change, a `{LOW}-standard` review of the result is the cheapest objective check.}
>
> On a verified failure, or when the agent reports it could not complete, re-dispatch **one rung higher** on the dispatch ladder with the failed attempt's report, so the next agent starts from it. Never retry the same rung unchanged; a single same-rung retry is allowed only when the failure came from the brief itself and the brief is corrected. A verified failure on the highest rung goes back to the user with the attempts' reports.

Variation points: `{CHEAP_REVIEW}` present only if the matrix has a `{LOW}-standard` type. Under the capability-first posture, the escalation paragraph may shrink to its last sentence; the verification paragraph stays.

Cost: 4-5 instructions. Omit only when the doctrine has no delegation at all.

## B2 - Mandatory delegation, context economy

Purpose: keep the main agent's context window alive across the session by pushing file-heavy work into subagents.

Canonical text:

> The main agent, the one in continuous dialogue with the user, delegates code modifications to a dedicated agent it prompts itself with the necessary context, rather than reading files, iterating and writing directly. {RATIONALE: Main lever: a file read by the main agent is re-billed on **every following turn** of the session; read by a subagent, it is paid once then discarded.}
>
> **Threshold.** Delegating costs a context prompt, an agent startup and a report. Below that cost (editing one or two lines in a file already in context, a trivial fix with no exploration) the main agent does it itself. Delegation becomes **mandatory** as soon as the task requires exploring, iterating, or touching several files.
>
> {FALLBACK: If delegation is unavailable (harness restricting agent launch, permission denied), the main agent executes itself and says so. An optimization rule never blocks the task.}
>
> The delegated agent's tier follows the calibration above. Context economy does not exempt from token economy; the two combine.

Variation points: `{RATIONALE}` included per Q2.2 (one sentence, costs one instruction); threshold wording follows Q2.1 ("mandatory" softens to "preferred" on the advisory answer); `{FALLBACK}` wording follows Q2.3, and if the human insists on "stop and ask" instead, write it but flag that an absolute with no workable exception is audit finding O3.2 territory.

Cost: 4-5 instructions. Omit if Q2.1 answered advisory AND the budget is tight; a preference is not worth three rules.

## B3 - Parallelism under mandatory isolation

Purpose: allow concurrent agents without them destroying each other's work. This block is **never split**: the permission to parallelize and the isolation requirement live in the same block, always (audit O3.1 exists to keep it that way).

Canonical text:

> If the user makes a request unrelated to the previous one while an agent is still working, launch a second agent in parallel rather than queueing. Never make an independent request wait because another is in progress.
>
> **Isolation is mandatory: it is the precondition of parallelization, not an optional precaution.** Two agents writing in the same working tree destroy each other's work{INCIDENT: (it happened here: one agent's `git stash` carried away another's changes, an orphan migration, no backend test running any more, with no error message anywhere)}. Impose **one of the two forms**:
>
> - **disjoint file sets**, enumerated in each agent's prompt, forbidden to leave; sufficient if no agent commits;
> - **isolated git worktrees**, one per agent; mandatory as soon as perimeters may overlap, an agent commits or stashes{MIGRATION: , or a migration is in play}.
>
> Absolute bans on a shared tree: {BAN_LIST}. Telling each agent what the others are doing remains necessary, but that is declarative coordination: it **does not replace** isolation.

Variation points: Q3.1 "never parallelize" collapses the whole block to two lines (agents run one at a time; the ban list stays); Q3.2 may choose worktrees-always (drops the disjoint-sets form) or disjoint-only (write it, but warn and record that commits under it are unprotected); `{MIGRATION}` present only if probe D9 found a migration framework; `{BAN_LIST}` defaults to `git stash`, `git add -A`, `git checkout`, `git reset` (Q3.3 may extend, shrinking it below the four is a warned decision); `{INCIDENT}` per Q3.4, one line, it is what makes the rule stick.

Cost: 6-7 instructions. Never omitted while any rule in the doc permits concurrent agents.

## B4 - Ask before dispatch

Purpose: catch misunderstood intent before subagents faithfully execute it.

Canonical text:

> Before decomposing a request and distributing it to agents, the orchestrator asks the user questions without restraint, as many as needed, whenever doubt remains about the real intent. Better to clear the ambiguity upstream than to hand subagents a misread instruction they would execute faithfully but beside the need.

Cost: 2 instructions. Omit per Q4.1 (bias-to-action posture).

## B5 - Session naming

Purpose: let the user see at a glance which model and effort run which task.

Canonical text (badge variant, probe D6 positive):

> The session label of a dispatched agent describes the task in a few words (for example "Rename variable X", "Debug JWT refresh race"), **without prefixing model or effort**: the agent panel already shows them as a badge via {STATUSLINE_PATH}, a machine-local configuration. If that configuration is absent (repo cloned elsewhere), fall back to the format `<model>(<effort>): <task>` so the information survives at a glance.

Prefix variant (D6 negative): the fallback format IS the rule, and the badge sentence is dropped.

Cost: 2 instructions. Omit if the project never dispatches named sessions.

## B6 - Subagent reporting

Purpose: subagent reports cost output tokens; buy findings, not narrative.

Canonical text:

> Dispatched agents report **findings, not execution narratives**: result first, no restatement of the task, no play-by-play. Density applies to the prose, never to the work: no shortcut on tests, verification, or flagged risks.

Cost: 2 instructions. Omit per Q2.4, or when the base doc already imposes a high-density output style globally (then this is redundancy, audit O4.2).

## B8 - Briefing

Purpose: brief quality is the first lever on delegated quality, and the cheaper the model, the less it can infer. Vague delegation produced misreads and duplicated work in every published multi-agent setup.

Canonical text:

> Every brief states the objective, the file perimeter, the expected report, and the verification command to run. For a `{LOW}` type the brief names the files, the expected behaviour and the check; an open design question is settled in the brief, or moves the task one rung up.

Variation points: the second sentence is dropped when the matrix has no `{LOW}` type.

Cost: 2-3 instructions. Never omitted when a `{LOW}` type exists; otherwise optional on a tight budget.
