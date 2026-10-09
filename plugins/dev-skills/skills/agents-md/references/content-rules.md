# What to write, and what actively harms

The rules in this file decide the quality of everything the skill produces. They are ordered by how much damage ignoring them causes.

## 1. Generic content is worse than no content

Agent instruction files written by LLMs measurably **reduce** task success (degradation observed in 5 of 8 tested settings, 2.45 to 3.92 extra steps per task) because models generate verbose, generic instructions that state what the agent already knows.

Never write:

- "Follow best practices", "write clean, maintainable code", "use descriptive variable names"
- "Handle errors appropriately", "write tests for new features"
- A restatement of what the framework's own documentation says
- A description of the directory tree that `ls` would produce

Write instead the thing an agent **would get wrong** by reasoning from the code alone:

> Celery's `autodiscover_tasks()` only scans `tasks.py`. A `@shared_task` defined elsewhere must be imported there explicitly, or it stays queued forever.

That sentence cannot be inferred from the code. It cost someone a day. It belongs in the file.

**The test:** if the sentence would be true of most projects in this language, delete it.

## 2. The counter-intuitive convention is the one worth documenting

Rank candidates by how surprising they are:

| Priority | Kind of fact | Example |
|---|---|---|
| Highest | A rule whose violation is silent | "A `cache.clear()` in a test fixture flushes the live Redis when the suite runs inside the preprod container" |
| High | A convention contradicting the ecosystem default | "Named exports only, including for React components" |
| High | A prohibition protecting production, money, or user data | "Never auto-repair a record created before this cutoff" |
| Medium | A verified command that is not the obvious one | The actual mypy invocation with its real scope |
| Low | Layer boundaries, naming patterns | Useful, but partly inferable |
| Never | Anything true of every project | "Write tests" |

## 3. Verified or absent

Every command written into the documentation must have been **executed** in the target repository during this run. Every path must have been stat'd. Every branch must have been resolved.

Field evidence: a documented `sudo docker compose` survived months in a file considered reliable, on a host where docker had long run unprivileged (the `sudo` triggered permission prompts and left root-owned files in the tree). A `gh run list --branch refactor/hexagonal` pointed at a branch deleted long before. Both were in the project's most-trusted file.

When a fact resists verification, the options are: ask the human, or write the slot empty with a one-line note. Never write the plausible version.

## 4. Behaviour and guardrails are different species

**Behaviour** applies on every turn, whatever file is being touched: how to decompose a task, when to ask instead of guess, how to delegate, how to report. It must be in the always-loaded root file. Externalising behaviour into an on-demand file guarantees it is read too late, or never.

**Guardrails** apply when a specific domain is touched: this ORM rule, that deployment constraint, this billing invariant. The prohibition belongs in the root file; the justification, the history and the procedure belong in the domain file. The cost then becomes conditional, which is the whole point: an agent working on the frontend stops paying for the video pipeline's guardrails on every session.

## 5. A guardrail works by its imperative, not its justification

This is what makes compression safe. Keep the prohibition and any numeric threshold; move everything else.

Before (1046 characters):

> **Player asset auto-repair bounded by `VIDEO_AUTOREPAIR_CUTOFF`**: the periodic selection of degraded ready videos (`repair_degraded_player_assets`) never examines a video created before this bound (default `2026-08-01T00:00:00Z`), a mechanical guardrail (SQL filter, fail-closed if unreadable), not a comfort setting. Explicit product requirement: the production fleet existing when this engine shipped (38 videos, 37 healthy and in use by paying subscribers) must never be touched by an automatic repair. Only the support command [...]

After (230 characters):

> **Player asset auto-repair**: no automatic repair of a video created before `VIDEO_AUTOREPAIR_CUTOFF` (default `2026-08-01`, fail-closed SQL filter). Manual repair one `--video-id` at a time, never a bulk backfill. Rationale and procedure: `AGENTS/BACKEND_LOGIC_VIDEOS.md`.

The prohibition, the bound, the fail-closed behaviour and the no-backfill rule all survive. The fleet count, the task name and the rhetorical reinforcement do not.

## 6. Never externalise without probing the destination

Before removing detail from the root file, grep the destination for the specific facts leaving. If they are not there, this is deletion wearing compression's clothes.

The operation that made this safe in the field: fifteen probes across seven destination files, every one confirming the detail was already present, before a single character was removed.

## 7. History is not agent documentation

Completed refactor phases, the reasoning behind settled decisions, what was split and why: this is archaeology. An agent needs the current state, not how it was reached. Move it to an architecture file or a history folder.

A root file that opens with the project's refactor narrative is paying, on every session forever, for a story that changes nothing about what the agent should do now.

## 8. Redundancy announces itself

The reliable tell is a cross-reference that follows a restatement: a paragraph that explains something, then ends with "see the section above". If the reader had to be told twice, one of the two is surplus. Keep the one in the more specific location, and leave a pointer only.

## 9. A rule without a mechanical check decays

Any rule that can be verified by a script should have one. A written prohibition depends on every future agent reading and honouring it; a script depends on nobody. Generate the checker, and hand over the CI block rather than wiring it.

Wire the check **after** clearing the existing violations, never before, or the pipeline is red on day one and the rule gets disabled instead of respected.

## 10. CLAUDE.md is a pointer, never a copy

Where a project uses both, `CLAUDE.md` imports `AGENTS.md` and adds nothing but the import and, at most, a few lines of hierarchy explanation. Two competing sources of truth are worth less than one: they drift, and the reader cannot tell which won.

## 11. Prose density

Write the way an engineering report is written: result first, no preamble, no restatement of the request, no closing summary. Fragments are fine. Tables beat paragraphs for anything enumerable.

Every line is paid for on every session, in every subagent. A paragraph that could be a table row should be a table row.

## 12. Concurrency rules belong in every generated file set

Any project where more than one agent may run must state the isolation rule, because the failure mode is silent and destructive: two agents writing to one working tree destroy each other's work, and a `git stash` from one carries away the other's changes with no error message anywhere.

The generated behaviour section must therefore always include: disjoint file sets enumerated per agent, or isolated git worktrees; and the absolute prohibitions on a shared tree (`stash`, `add -A`, `checkout`, `reset`). Plus the staging rule that prevents the most common version of the accident: **stage only files you modified yourself.**
