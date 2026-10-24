# Start menu: the bare invocation

Shared by every dev-skills skill. A bare invocation is the user asking "where am I, and what should I do next with this skill?". Answer with a context-aware status and menu, then let the user choose. **Never auto-run a mode from a bare invocation.**

## When it applies

- **Bare** = the skill is invoked with no argument AND the user's message states no task beyond the skill's name (`/legal`, `/dev-skills:test-coverage`, "run test-coverage" with nothing else).
- **Not bare**: any argument or flag (`--help` still prints the Usage block verbatim and stops), or a stated task in natural language ("merge develop into main", "audit my legal pages", "resume the recette"). Those keep the skill's own routing: the mode-selection rules in its SKILL.md.
- A skill auto-loaded to refuse a production action (full-test, manual-test, safe-merge guardrails) is never bare: refuse and redirect as the skill says.

## Probe budget

Read-only and fast, never a full Phase 0:
- harness detection (`harness.md` H1), then only the skill's **state probes** listed in its "Start menu" section: config and journal files, stamped versions, `git log` / `git rev-list` / `git diff --stat` against recorded SHAs, file presence.
- No network, no test run, no deployment check, no subagent unless a probe needs more than a few file reads (then one `light` agent), no write of any kind (no journal, no config stamp).
- A probe that cannot run gives `unknown`, never `up to date`.

## Freshness rules

An artifact the skill produced earlier is:
- **in progress** when its journal shows an unfinished run (the skill's own resume window applies): resuming it is always the first pick;
- **stale** when its recorded SHA is not an ancestor of HEAD, or commits since that SHA touch the paths it depends on (count them, name the top paths), or a stamped copy carries an older plugin version than `plugin.json`, or its date is past the skill's freshness threshold, or it predates a structural change the skill now expects (for example a doctrine without the current blocks);
- **up to date** only when every check above passed;
- **absent** when never produced; **unknown** when a check could not run.

## Output (in the skill's report language)

1. One line: harness, repository, current branch, HEAD short SHA.
2. **Status**: a short table, one row per artifact the skill owns: artifact, state (`absent`, `in progress`, `up to date`, `stale`, `unknown`), evidence (SHA, date, commits since, version, finding count).
3. **Recommended next**: 2 or 3 picks, best first, each with the exact command to type and a one-line reason taken from the status. The first pick is what to do now.
4. **Workflow**: the skill's recommended order as a numbered list, each step marked `done`, `to redo` (stale), `next` or `later`, with the related skills that come before or after it when a signal makes them relevant (for example "`/agents-md init` first: no AGENTS.md").
5. One line: "All commands: `/<skill> --help`".

Keep it to one screen. No narrative, no restated Usage block.

## Then ask

Offer the picks as a choice (AskUserQuestion on Claude Code, the harness's question tool elsewhere, a numbered plain-text list otherwise): the recommended pick first and labelled as such, the other picks, and "nothing for now". Run the chosen command exactly as if the user had typed it, gates and confirmations included. A dry-run variant is offered as a pick whenever the skill has one and the user never ran the skill on this repository.
