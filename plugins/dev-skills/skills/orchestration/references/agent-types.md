# Agent type definitions

Contents: The matrix | Built-in overrides | Frontmatter schema | Body rules | Location and fallback

How the `agents` scope designs, writes and grades subagent type files. The model facts behind every choice here live in `references/models.md`; read it first and refresh it (probe D11) when it is stale.

## The matrix

Two axes: **model capability** (which model) and **reasoning effort** (how hard it thinks). A type is one point on that grid with a name, a spawn rule, a turn cap, and a short system prompt. The canonical five:

| Type | Tier | Effort | maxTurns | Color | Spawn when |
|---|---|---|---|---|---|
| `{LOW}-quick` | low | low | 30 | green | mechanical, bounded, already located: rename, format, targeted edit, search, extraction. No judgment expected |
| `{LOW}-standard` | low | medium | 60 | cyan | **default subagent**: any task the orchestrator can brief (files, intended behaviour, verification), such as bug fixes, small features, UI tweaks, tests, doc and text edits, git chores; exploration, reading and mapping; verification and review of another agent's result; every agent launched by a subagent. Strongest value under about 100k tokens of context |
| `{MID}-standard` | mid | medium | 80 | blue | a design choice that the brief cannot settle, debugging whose cause is still unknown, a change whose shape depends on judgment across several layers |
| `{TOP}-standard` | top | medium | 120 | yellow | real reasoning: non-trivial debugging, refactoring, heavy context intake, security-sensitive or data-sensitive work. Chosen freely by the orchestrator when it judges the task needs it |
| `{TOP}-deep` | top | high | 150 | red | only when the user explicitly asks to dig deeper, or after `{TOP}-standard` failed on the same task. Never a first choice |

`{LOW}`, `{MID}` and `{TOP}` come from interview Q1.1 and `references/models.md`: typically `haiku`, `sonnet` and `opus`. A model above `{TOP}` (Fable) stays outside the matrix; the doctrine's ladder covers it.

**Why this shape** (each point is measured or documented in models.md):
- No `{MID}-deep`: a mid model at high effort runs long loops and costs nearly as much per run as the top model at medium, for less reasoning.
- `{TOP}-deep` at **high, not xhigh**: xhigh is meant for tasks of 30 minutes and more with budgets in the millions of tokens. As a routine tier it was the single largest cost line measured. Raising a type to xhigh or max is a recorded human decision (`quirks`), never a default.
- The bottom tier is the **default for briefed implementation**, not a reserve for trivia: Haiku 5.5 codes well when the brief says what to change and how to check it, at a twentieth of the mid tier's price. It trails the mid tier on open-ended design, so an open design question is settled in the brief first, or moves the task one rung up. Measured on the reference machine before this rule: no bottom-tier run at all, while half of the mid-tier runs were fully briefed edits.
- **`maxTurns` caps runaway loops.** Reaching it returns a partial result that the orchestrator can resume: the cap forces a conscious decision to continue, it does not lose work. The defaults sit near, or for the deep tier deliberately below, the measured calls per run of each tier on the reference machine (calls per run approximate turns); recalibrate them from probe D12.

**Pruning rules** (Q1.3):
- **Five types**: the full grid. Recommended when a low, a mid and a top model are all available.
- **Three types**: `{LOW}-standard`, `{MID}-standard`, `{TOP}-standard`. For users who prefer fewer choices; quick work goes to `{LOW}-standard`, deep work is resumed or re-briefed on `{TOP}-standard`.
- **None**: no files written; B1 drops its `{EFFORT_AXIS}` paragraph and relies on the Agent tool's `model` parameter alone.

**Missing tiers** (Q1.1):
- No low model: drop `{LOW}-standard`, and the quick row becomes `{MID}-quick` (mid tier, low effort, green).
- No top model: drop both top rows; `{MID}-standard` becomes the highest rung of the dispatch ladder and B1's deep gate is dropped.
- A type whose model is unavailable on this machine is finding O1.2. Never written.

**Other harnesses.** Agent type files are a Claude Code mechanism. When probe D0 finds another harness and the project shows no Claude Code use, the `agents` scope writes nothing and says so; the generic doctrine's tiers (`light`, `standard`, `strong`) carry the same matrix in words (`harness.md` H3).

## Built-in overrides

Two Claude Code built-ins silently run on the main conversation's model, often the top tier:

- **`Explore`**: a user or project agent named `Explore` replaces the built-in and keeps its own `model`. Written when Q1.4 accepts it:

  ```yaml
  ---
  name: Explore
  description: "Read-only exploration: locate files, symbols and usages, answer where-is and how-does questions. Use proactively for any codebase search that would otherwise read many files into the main context."
  model: {LOW}
  effort: medium
  maxTurns: 140
  color: green
  disallowedTools: Write, Edit, NotebookEdit, Agent
  ---
  ```

  Body: "You are a read-only exploration subagent. Locate what the orchestrator asked for and report paths with line numbers and the minimal excerpts that answer the question. Never modify anything. If the question is ambiguous, report the candidate interpretations you found instead of picking one."
  Medium, not low: at low effort the bottom tier skips searches more often, which is the one thing an explorer must not do.

- **`general-purpose`** and any custom agent with no `model` field use the `CLAUDE_CODE_SUBAGENT_MODEL` environment variable when it is set. The skill **proposes** this block for the `settings.json` matching the agents' location, and writes it only on explicit confirmation:

  ```json
  { "env": { "CLAUDE_CODE_SUBAGENT_MODEL": "{MID}" } }
  ```

  Never add `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`: it would override every type's own `model`, the whole matrix included.

## Frontmatter schema

Verified against the Claude Code field set (see models.md). Required by this skill: `name`, `description`, `model`, `effort`. Written by default: `maxTurns`, `color`. Optional: `disallowedTools`, `tools`.

```yaml
---
name: sonnet-standard    # equals the filename stem (skill convention; Claude Code does not require it)
description: ...         # states WHEN TO SPAWN it, 1-2 sentences, in the output language
model: sonnet            # an alias, or the full ID when the alias resolves to an older model (models.md)
                         # while an alias is unstable (resolution differs across CLI versions), pin the full model id for that tier and record it in quirks (O8.10)
effort: medium           # low | medium | high | xhigh | max
maxTurns: 180             # cap on agentic turns; partial result on reaching it
color: blue              # ramp green -> cyan -> blue -> yellow -> red, ascending with cost
---
```

The `description` is the dispatch contract: it must let an orchestrator choose the type without opening the body, and it should name the neighbouring tiers ("for X; for Y use `{MID}-standard`"). Keep it short: every type's description is loaded into the orchestrator's context in every session. A description that says what the agent IS instead of when to SPAWN it is finding O6.1. Never hardcode a model version number in a description ("Haiku 4.5, medium"): it goes stale at the next release and misleads the dispatcher; name the tier and effort only.

## Body rules

The body is the type's system prompt. Written in the output language. Three constraints:

1. **Second person, short.** Two to four sentences. It frames posture, it does not re-teach the craft.
2. **Scope-bounded.** The bottom tier must stop and report on ambiguity rather than guess: an explicit "could not complete" is a valid escalation signal (B7), a confident guess is not. The deep tiers explicitly license thinking before acting.
3. **Ends with a reporting instruction.** Every body's last clause tells the agent how to report: result, files touched, the verification run and its outcome. A body without it is finding O6.3.

Every body also carries the termination clause of B8/B9: bound each command with a timeout, never leave a foreground command waiting forever, stop the background processes you started before reporting, and report "could not complete" rather than wait.

Canonical bodies (English render source):

- `{LOW}-quick`: "You are a fast execution subagent. Your task is strictly bounded by the orchestrator's prompt: do not extend it, do not improve it, touch nothing outside its explicit perimeter. If the brief is ambiguous or the task turns out larger than described, stop and report what blocks you instead of guessing. Otherwise make the change directly and report the result concisely."
- `{LOW}-standard`: "You are an implementation subagent. Follow the brief and the existing patterns of the code; if you meet a design decision that neither the brief nor the existing code settles, stop and report it instead of deciding. Run the verification the brief names. Report the result, the files modified, and the verification outcome."
- `{MID}-standard`: "You are a general execution subagent. Explore what is needed to understand the task's context, make the requested changes respecting the existing style and conventions, and run the verification the brief names. Report a concise summary of the result, the files modified, and the verification outcome."
- `{TOP}-standard`: "You are a deep-reflection subagent. The task requires absorbing substantial context, weighing options, or debugging non-trivial behaviour before acting. Take the time to explore and verify your hypotheses before modifying anything, then report your key reasoning, the result, and the verification outcome concisely."
- `{TOP}-deep`: "You are a subagent for problems that resisted a first serious attempt or that the user asked to examine in depth. If a previous attempt's report is provided, start from it rather than from zero. Analyse the implications before acting, explicitly flag risks and uncertain assumptions, and report a dense technical summary of the result and its verification."

## Location and fallback

Q0.1 decides where the files live:

- **Global** (`~/.claude/agents/`): shared across every project on this machine, invisible to a clone elsewhere. The doctrine's B1 MUST then carry the location note ("machine-local configuration, absent if this repo is cloned elsewhere") and the fallback sentence. `fallback_documented: true` in the config is what audit O3.5 checks.
- **Project** (`.claude/agents/`): versioned, travels with the repo, duplicated across projects. No location note needed; the fallback sentence stays anyway (another machine may run a harness without custom agent types).

The `Explore` override follows the same location; the `CLAUDE_CODE_SUBAGENT_MODEL` block goes into `~/.claude/settings.json` for global, `.claude/settings.json` for project.

**Collision rule**: a type name present in BOTH locations resolves to the project file for this repo. If the two frontmatters diverge, that is finding O2.4; the skill never silently reconciles them.

**Replacing a previous matrix** (sync): retired types (for example `sonnet-quick`, `sonnet-deep`, an xhigh `opus-deep`) are removed only in a confirmed batch, after searching for citations of them in every AGENTS.md, CLAUDE.md and agent file on the machine (global types are shared by all projects). A retired type still cited somewhere is finding O1.1 waiting to happen.
