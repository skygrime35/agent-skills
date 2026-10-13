# Audit check grid

Run in modes `audit` and `sync`. **No finding without evidence**: every finding states the check that produced it and the observed value (file:line or probe output). A check that could not run is itself reported as a blind spot, never a green check. Findings are reported most severe first, P0 to P3.

Severity: **P0** active risk (the doctrine sends agents into failure), **P1** false fact (the doc asserts something untrue of this machine or repo), **P2** structure and cost, **P3** hygiene.

Cross-scope checks (O1, O2) run whenever at least one involved scope is selected; a fix that lies outside the selected scopes is reported with "out of selected scope, re-run with --scope=...".

## O0 - Preconditions

- **O0.1** Base doc undetectable (probe D1 empty). Every doctrine check below is blocked; report each as a blind spot and continue on the `agents` and `checks` scopes.
- **O0.2** `.claude/agents-md.yml` absent. Budget baseline unknown; compute locally via D4 and flag the result as locally computed.

## O1 - Dead references

Extract every backticked kebab token and path from the owned section (D2 span), resolve each against reality.

- **O1.1 P0** The doctrine cites an agent type installed nowhere (neither inventory of probe D5). Every dispatch to it silently downgrades or fails. Evidence: the citing line + both `ls` outputs.
- **O1.2 P1** The doctrine names a model absent from `local.models_available`. Evidence: the line + the config field.
- **O1.3 P1** The doctrine cites a machine-local path (statusline script, global agents dir) that does not exist AND gives no fallback. With a documented fallback in the same block: pass, that is the design. Evidence: the line + `test -f` output.
- **O1.4 P1** The config lists agent files that no longer exist or no longer parse. Evidence: config entry + stat/parse error.

## O2 - Contradictions

- **O2.1 P1** Doctrine vs agent frontmatter: the doctrine describes a type (effort, model, purpose) differently from the file's own frontmatter. Evidence: both lines.
- **O2.2 P1** Doctrine vs `orchestration.yml`: for example config says `agents.location: project`, doctrine points at `~/.claude/agents/`. Evidence: both lines.
- **O2.3 P0** Doctrine vs `agents-md.yml` or vs any rule elsewhere in the base doc: a language rule, a "never spawn subagents" rule, a budget stance. Never auto-resolved; the finding names both sides and asks. Evidence: both quotes with locations.
- **O2.4 P1** The same type name defined in global AND project locations with diverging frontmatter. Evidence: both frontmatters.
- **O2.5 P2** A type's `description` routes work to another type ("for X use Y", "use `Y` for ..."), and the routing disagrees with the doctrine's default rung: briefable routine work sent above `{LOW}-standard` (or to any type other than the default) when the doctrine names that default, or a higher rung named as the destination for work the doctrine reserves for the default. Such a description pushes work to the wrong tier on every dispatch. Evidence: the description line (file) + the doctrine's default-rung sentence (B1 `{LOW_DEFAULT}`, or the posture's default).
- **O2.6 P2** The doctrine mentions a model above the matrix (a model in `local.models_available` ranked above `{TOP}`, for example `fable`) without stating whether it is a rung. The section must say explicitly: "it is not a rung" (chosen per invocation, a verified failure on the highest rung goes back to the user) or state that it is one. Evidence: the mention line, and the absence of such a sentence in the owned span.

## O3 - Doctrine gaps

- **O3.1 P0** Parallelism permitted with no isolation mechanism in the same section.

  ```bash
  # inside the owned span only:
  grep -niE 'parallel|parallél|concurren|simultan' SECTION
  grep -niE 'worktree|disjoint|cloisonn|isolat' SECTION
  ```

  First grep hits, second does not: P0. Also fired when D2 recorded scattered doctrine that splits the permission from the isolation across sections.
- **O3.2 P0** Delegation declared mandatory with no fallback for an unavailable mechanism. An absolute with no workable exception stops work in any harness that restricts subagents. Evidence: the imperative line + absence of a fallback clause in the block.
- **O3.3 P1** The orchestrator's identity keyed to a named model in a normative sentence ("Fable orchestrates") instead of a role. Ladder lists themselves are legitimate named content; the check targets normative sentences only. Evidence: the line.
- **O3.4 P2** Shared-tree ban list incomplete: any of `git stash`, `git add -A`, `git checkout`, `git reset` missing from a rule that permits shared-tree work, unless the config records a customized list (Q3.3). Evidence: the ban list line + the config markers.
- **O3.5 P1** Effort-tier doctrine (B1's effort paragraph) with no machine-absent fallback sentence. Evidence: the paragraph.
- **O3.6 P2** The owned doctrine spans three or more headings (D2 `section_spans` has >= 3 entries). Doctrine spread over several sibling headings is hard to keep consistent and easy to miss on sync. Fix: add one parent heading that holds the whole doctrine (one span), or keep the spans recorded in `section_spans` and state that sync edits only those spans. Evidence: the heading list with each span's start and end.

## O4 - Budget

- **O4.1** Total instruction count over the threshold (D4). P2 in general; **P1 if the orchestration section's own share caused the overrun**. The finding names the section's share and its cheapest cut candidates (B6, then B4, then B2's rationale sentence). Evidence: both counts.
- **O4.2 P3** Generic filler inside the owned section: "use the right model", "delegate when appropriate", "coordinate carefully". A rule with no threshold, no mechanism and no prohibition is a token tax. Evidence: the line.

## O5 - Language and style

- **O5.1 P2** The owned section's language differs from the base doc's language. Escalates to a reported conflict (never auto-fixed) if the project states a language rule. Evidence: D7 output + a sample line.
- **O5.2 P3** Em or en dashes in generated content where the project bans them. Run the project's `check_forbidden_chars` if installed (see agents-md config `guardrail_scripts`), else `grep -nP '\x{2014}|\x{2013}' SECTION`. Evidence: the hits.

## O6 - Agent file hygiene

For every file in both D5 inventories:

- **O6.1 P1** Frontmatter missing `name`, `description`, `model` or `effort`; or `name` differs from the filename stem; or `description` says what the agent is instead of when to spawn it. Evidence: the frontmatter.
- **O6.2 P2** `effort` outside {low, medium, high, xhigh, max}, or inconsistent with the tier its name claims (a `-quick` above low, a `-standard` other than medium, a `-deep` below high); `maxTurns` present but not a positive integer. Evidence: the field.
- **O6.3 P2** Body lacks a closing reporting instruction. Evidence: the body's last sentence.
- **O6.4 P3** Color ramp not ascending with cost across the set (green, cyan, blue, yellow, red), or a color outside the eight Claude Code accepts. Evidence: the table of colors.

## O7 - Checks scope

- **O7.1 P1** A check script recorded in the config but missing on disk. Evidence: config entry + `ls` output.
- **O7.2 P1** `wired: true` with no CI or pre-commit evidence (probe D10's grep empty). A false fact about enforcement is worse than no enforcement. Evidence: the config line + the empty grep.
- **O7.3 P2** The script exists but scans a location that is not the current `agents.location` (moved agents dir, renamed doc). Evidence: the script's arguments in CI vs the config.
- **O7.4 P3** The check script sits in `scripts/` although git tracks no other `scripts/check_*` file and nothing wires it: migration candidate to `.claude/orchestration/` (sync proposes it). Evidence: `git ls-files 'scripts/check_*'` + D10 grep.

## O8 - Model economy

Grounded in `references/models.md`; uses probes D5, D11 and D12.

- **O8.1 P1** A type at `xhigh` or `max` effort with no `quirks` entry recording why. Measured on the reference machine, an xhigh routine tier was the largest single cost line. Evidence: the frontmatter + the config's quirks.
- **O8.2 P2** A low-tier model is available (`local.models_available`) and no type uses it; or a `{MID}` type at high effort or above exists alongside a `{TOP}-standard` (it costs nearly as much per run for less reasoning). Evidence: the type table.
- **O8.3 P1** Escalation gated on the executing agent's self-assessment ("if it is confident", "si l'agent est sûr") instead of an objective check. P2 when the doctrine allows dispatching below the estimated rung but states no verification rule at all. Evidence: the line, or the absence of B7.
- **O8.4 P2** Built-ins inherit an expensive model: the main model is `{TOP}` or above and there is no `Explore` override, or `CLAUDE_CODE_SUBAGENT_MODEL` is unset. **P1** when `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` is set: it overrides every type's own model and silently voids the matrix. Evidence: D11 output.
  - **`fork` and `Plan`** also run on the main model (`Plan` unless `_FORCE` is set, `fork` always; models.md). **P3** when D12 shows measured runs on either: report runs, $ and share of subagent spend over the window. The optional doctrine clause "`fork` and `Plan` run on the orchestrator's model: never use them for briefable work" (doctrine-content.md, B2 variation) is proposed only when that spend is material: at least 10% of subagent spend over the window. Below that, the P3 stays as an observation. Evidence: the D12 rows for `fork` and `Plan`.
- **O8.5 P2** The doctrine forces a fixed starting rung regardless of the task ("always start with Haiku"), contradicting the never-two-rungs-below rule (the balanced posture's `{MID}-standard` default, which keeps its exceptions for clearly mechanical and clearly hard work, is not this finding); or it gates `{TOP}-standard` behind a trigger list, removing the orchestrator's judgment. Evidence: the line.
- **O8.6 P2** Measured spend contradicts the doctrine: `{TOP}-deep` above 25% of subagent spend over the window, or a `{TOP}` type is the most-launched type while the posture is `cheapest-capable`. Restrict the window to sessions started after the current types were installed (same restriction as O8.9: older sessions cannot use them). A restricted window under 7 days is too short to judge: report a P3 observation with a suggested re-measure date (install date + 7 days) instead of a P2. Below the thresholds, report the D12 table as a P3 observation. Evidence: the D12 table + the window start.
- **O8.7 P3** A type without `maxTurns`, or whose measured calls per run (D12) routinely exceed its cap. Evidence: the frontmatter + D12.
- **O8.8 P3** `references/models.md` older than 30 days and not refreshable in this run. Reported as a blind spot: every price-based finding above is then "as of <date>". Evidence: the Verified line.
- **O8.9 P2** The bottom tier is installed and the posture is `cheapest-capable`, yet `{LOW}` types account for under 30% of delegated runs in the D12 window. Count only sessions started after the types were installed: a session lists agent types and loads the base doc at start, so older sessions cannot use new types. Evidence: the D12 table + the mid- and top-tier run descriptions (`.meta.json` `description`) that read as fully briefed edits.
- **O8.10 P1/P2** Alias resolution drift. Per agent type, compare the model actually resolved in its subagent transcripts (`message.model`, together with the Claude Code CLI `version` field of the same lines; both are output per type by `usage_by_agent_type.py`, D12) against the model its type file or the doctrine claims (an alias such as `sonnet` or `haiku`, or a model named in `models.md`/`quirks`). A mismatch is **P1** when the price ratio between resolved and claimed model is 2x or more (`models.md` prices), else **P2**. Evidence: the type, the claimed model, the resolved model(s) and the CLI version(s). No subagent transcripts for the type (or at all): report a blind spot, never a pass.
