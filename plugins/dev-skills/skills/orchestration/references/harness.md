# Harness detection and portable orchestration

Contents: H1 Detect the harness | H2 Profiles | H3 Role map | H4 Agent lifecycle | H5 Degradations

Shared by every dev-skills skill. Each skill runs H1 as the **first step of its Phase 0**, before any other probe, and then dispatches agents through the profile H2 selects. The skills name Claude Code agent types (`haiku-standard`, `sonnet-standard`, ...) in their tables: on Claude Code they are used as written; on any other harness they are read as **roles** through H3, and no model is ever named.

## H1 - Detect the harness

The authoritative signal is the agent's **own toolset**, observed, never guessed. Corroborating signals help only when the toolset is ambiguous.

| Signal | Claude Code | Other harness |
|---|---|---|
| Spawn tool | `Agent` (or `Task`) taking `subagent_type` and an optional `model` | a differently named spawn tool, or none |
| Companion tools | `AskUserQuestion`, `TaskStop`, `SendMessage`, `TaskCreate`/`TaskUpdate`, `Monitor`, `ToolSearch` | absent or named otherwise |
| Skill directory | `${CLAUDE_SKILL_DIR}` already substituted with a real path in SKILL.md | the literal placeholder is still visible: the skill directory is the folder holding the SKILL.md being read |
| Shell environment | `CLAUDECODE=1` (`env \| grep -E '^CLAUDE_?CODE'`) | variable absent |

Decision: **Claude Code** when the spawn tool takes `subagent_type` or two other Claude Code signals agree; **other** otherwise, with the harness name when it is self-evident (Codex, Gemini CLI, Cursor, OpenCode, Copilot, ...), else `unknown`. Then record the capabilities, each `true`, `false` or `unknown`:

```yaml
harness:
  name: claude-code | <name> | unknown
  subagents: true|false          # can this agent launch another agent at all
  named_types: true|false        # agent types selectable by name (Claude Code: the types the Agent tool offers)
  model_choice: true|false       # a per-call model or tier can be chosen
  nested_subagents: true|false|unknown   # a subagent can launch its own subagents
  ask_tool: true|false           # structured question tool (AskUserQuestion or equivalent)
  stop_tool: true|false          # a way to stop a running agent or background command (TaskStop or equivalent)
  background: true|false         # agents or commands can run in the background
```

Announce the result in one line with the other Phase 0 facts (`Harness: claude-code` or `Harness: other (<name>), subagents yes, model choice no`). Never block on it: an `unknown` capability is used as `false` and listed as a blind spot.

## H2 - Profiles

**Claude Code profile** (`name: claude-code`). Agent types, models and efforts are used as the skill and the project's orchestration section name them. Model rules:
- **Haiku 5.5 is the default subagent model.** It is strong and cheap below about 100k tokens of context (cache reads twenty times cheaper than the mid tier there, see `models.md`), which is the normal size of a subagent's context. Every briefed subagent task (exploration, reading, mapping, verification, review of another agent's work, briefed implementation, mechanical edits) starts at `haiku-standard`, or `haiku-quick` when purely mechanical.
- **Sub-subagents** (agents launched by a subagent) start at `haiku-quick` or `haiku-standard`; a subagent that needs a higher rung for its own child says why in its report.
- A higher rung needs a reason the brief cannot remove: an open design choice, an unknown cause, security- or data-sensitive work, or a context that will clearly exceed 100k tokens. A task table that assigns `sonnet-standard` or `opus-standard` is a ceiling for that role, not a starting point, when the brief settles the open questions.
- A named type missing from what the Agent tool offers: pass the model through the Agent tool's `model` parameter with the session's default effort, and report it.

**Generic profile** (any other harness). The orchestration rules stay, the vocabulary changes:
- Never name a model, a model family or a Claude Code type in a dispatch or a written file. Choose by **capability tier** (H3): `light` (the cheapest model or agent kind the harness offers), `standard`, `strong`.
- Use the harness's own spawn mechanism, its own question tool (plain-text questions when there is none), its own task list (a checklist in the skill's journal when there is none).
- `model_choice: false`: every agent runs on the session model; keep the decomposition, briefs, isolation and verification rules unchanged, and keep the tier names only as a sizing hint in the brief.
- `subagents: false`: the main loop executes the waves itself, one package at a time in the planned order, and says so in the final report. Fan-outs become sequential; every guardrail and gate stays.
- `nested_subagents: false|unknown`: a subagent never plans on launching children; the orchestrator splits the work one level further instead.

## H3 - Role map

| Role (as skills name it) | Claude Code type | Generic tier | Typical work |
|---|---|---|---|
| mechanical | `haiku-quick` | light | rename, format, located edit, search, extraction, one probe |
| briefed | `haiku-standard` | light | exploration, reading and mapping, verification and review, briefed implementation, tests from a clear brief, doc edits, sub-subagents |
| judgment | `sonnet-standard` | standard | a design choice the brief cannot settle, debugging with an unknown cause, synthesis across many sources |
| reasoning | `opus-standard` | strong | non-trivial debugging, heavy context intake, security- or data-sensitive analysis, final arbitration |
| deep | `opus-deep` | strong (stated as "in depth" in the brief) | only on the user's explicit request or after the reasoning rung failed on the same task |

The project's own orchestration section (AGENTS.md / CLAUDE.md) wins over this table when present; a skill's own table wins over this one for its own roles.

## H4 - Agent lifecycle

An agent whose report has arrived and that has no planned follow-up is **closed** at once. Agents do hang: a subagent waiting on a command that never returns (a dev server, a watcher, an interactive prompt, a test runner without a timeout) stays open, holds resources and can later write into the tree.

- **Brief for termination.** Every brief tells the agent to bound each command with a timeout, never to start an interactive or never-ending command in the foreground, to stop every background process it started before reporting, and to report "could not complete" rather than wait indefinitely.
- **Close after the report.** Once the report is read and verified, and no follow-up message to that agent is planned, stop it and any background command it left: Claude Code `TaskStop` on the agent or shell task still listed as running; another harness, its own stop, kill or close action. Keep an agent open only when a follow-up to it is planned, and close it after the follow-up.
- **Stalled agent.** No progress and no report past the expected duration of its task (or twice its slowest sibling's): read its partial output, stop it, then re-dispatch from that output or finish inline. Never leave it running while the run moves on.
- **Before the final report**, list the agents and background commands this run started; anything still running is stopped, or named in the report with the reason it stays.
- No stop tool (`stop_tool: false`): end the agent's turn by message when the harness allows it, and report any agent that could not be closed.

## H5 - Degradations

Every capability used as `false` is reported once, in the skill's final report or blind-spot list: no subagents (waves run inline), no model choice (session model everywhere), no question tool (plain-text questions), no stop tool (agents closed by message only), no background tasks (long commands run in the foreground with an explicit timeout).
