# Detection probes

Contents: D1 Base doc | D2 Existing section | D3 agents-md config | D4 Budget | D5 Agent types | D6 Statusline | D7 Language | D8 Delegation capability | D9 Isolation | D10 Existing checks | D11 Model facts | D12 Measured usage | Output profile

Run in Phase 0 of every mode. The probes are independent: fan them out. Each yields a verified fact or an explicit unknown; nothing in between. The output is the profile YAML at the end, whose `unknowns:` list is never empty on a real repository. A run that reports zero unknowns has guessed somewhere.

## D1 - Base doc file

```bash
ls AGENTS.md CLAUDE.md GEMINI.md .cursorrules 2>/dev/null
grep -l '@AGENTS.md' CLAUDE.md 2>/dev/null
```

If CLAUDE.md contains `@AGENTS.md` (or a one-line textual redirect), CLAUDE.md is a thin pointer and **AGENTS.md is the source of truth**: the doctrine is written there, never into the pointer. Record `{file, pointer, evidence}`.

Neither file found: the `doctrine` scope stops with "no base doc file, run `/agents-md init` first". The `agents` and `checks` scopes may still proceed.

## D2 - Existing orchestration section

Two passes over the base doc:

```bash
grep -nE '^#{2,4} .*([Oo]rchestrat|[Mm]ulti.agent)' BASE_DOC
grep -niE 'worktree|sous-agent|subagent|deleg|délég|parallel|parallél|effort' BASE_DOC
```

The heading probe finds the owned section; record its span (start line, end line of the heading's content, bounded by the next same-level heading). The semantic probe finds orchestration rules living OUTSIDE that span: each such hit is recorded as **scattered doctrine** and feeds audit family O3. No heading but semantic hits: there is doctrine with no owned section, `init` on the doctrine scope still switches to `audit` (the artifact exists, dispersed).

## D3 - agents-md config

```bash
cat .claude/agents-md.yml 2>/dev/null
```

Read `language.written`, `budget.instructions`, `structure.root`, `guardrail_scripts` (is `check_forbidden_chars` installed, with which chars?). Absent: blind spot, budget computed locally by D4, and `structure.root` falls back to D1's answer.

## D4 - Instruction budget

Same method as agents-md check P2.1: count normative statements (imperatives, "never", "always", "must", bullet rules) across every always-loaded file (base doc + pointer + anything they `@`-import). Then isolate the orchestration section's own share using D2's span. Report both numbers; the threshold and the harness share are owned by the agents-md skill (`references/structure.md`).

## D5 - Installed agent types

```bash
ls ~/.claude/agents/*.md 2>/dev/null
ls .claude/agents/*.md 2>/dev/null
```

Parse every frontmatter: `name`, `description`, `model`, `effort`, `maxTurns`, `color`, `disallowedTools`. Verify `name` equals the filename stem. Keep the two inventories separate: the global one is machine-local and belongs under `local:` in the config; the project one is versioned. A file that fails to parse is recorded with `verified: false` and a note, never silently dropped.

## D6 - Statusline

```bash
test -f ~/.claude/subagent-statusline.sh && echo present
```

Present: session-naming block B5 uses the badge variant (task description only, badge shows model and effort). Absent: B5 uses the prefix format. Either way B5 documents the other variant as fallback.

## D7 - Language

Three signals: accent and stopword scan of the base doc's prose; D3's `language.written`; any stated language rule in the doc's guardrails:

```bash
grep -niE 'langue|language' BASE_DOC | grep -iE 'toujours|partout|always|all'
```

If the signals disagree, or `--lang` contradicts a stated rule, record the conflict verbatim with its location. Surface it, never resolve it silently (see SKILL.md, Language).

## D8 - Harness delegation capability

Not probeable from the repository, but observable by the agent running this skill: if its own toolset exposes the Agent tool, record `local.delegation_capable: true`; otherwise `false`. Unknown at write time: blind spot, and block B2 must keep its "if delegation is unavailable" fallback clause unconditionally.

## D9 - Isolation substrate

```bash
git worktree list 2>/dev/null
find . -maxdepth 4 -type d -name migrations | head -5
ls alembic.ini prisma/schema.prisma 2>/dev/null
```

Worktrees usable: B3 may name them as the strong isolation form. A migration framework present: B3's escalation trigger mentions migrations explicitly ("a migration is in play forces worktrees"). No migration framework: that trigger is omitted rather than written speculatively.

## D10 - Existing checks

```bash
ls scripts/check_agent_refs.py .claude/orchestration/check_agent_refs.py 2>/dev/null
grep -rn 'check_agent_refs' .github/workflows/ .pre-commit-config.yaml 2>/dev/null
```

The second command is the only admissible evidence for `wired: true`. Script on disk but absent from CI and pre-commit: `wired: false`, whatever the config claims (a claim without evidence is finding O7.2).

## D11 - Model facts and built-in routing

```bash
grep -m1 -n 'Verified:' ${CLAUDE_SKILL_DIR}/references/models.md
grep -n 'CLAUDE_CODE_SUBAGENT_MODEL' ~/.claude/settings.json .claude/settings.json .claude/settings.local.json 2>/dev/null
grep -n '"model"' ~/.claude/settings.json .claude/settings.json 2>/dev/null
ls ~/.claude/agents/Explore.md .claude/agents/Explore.md 2>/dev/null
```

The model table is a dated snapshot. When it is older than 30 days, or a model named by the user or the installed types is missing from it, re-read the official pages listed in models.md (lineup, pricing, effort) and update the table and its date before Phase 2; record `local.models_verified_at`. No network: keep the table, report "model facts as of <date>" as a blind spot.

Record the main model, `CLAUDE_CODE_SUBAGENT_MODEL` (and whether `_FORCE` is set: it overrides every type's model, finding O8.4), and whether an `Explore` override exists. These answer Q1.4's starting point.

## D12 - Measured usage

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/usage_by_agent_type.py --days 30
```

Reads the local Claude Code transcripts (`~/.claude/projects/*/*/subagents/*.jsonl` with their `.meta.json`) and prints, per agent type: runs, calls per run, context per call, estimated cost per run at API prices, and share of subagent spend; plus main-session spend per model. Read-only, local, nothing leaves the machine. Prices come from the script's table, which mirrors models.md: when D11 updates models.md, update the script's `PRICES` in the same batch.

Runs in every mode when transcripts exist: in init it informs Q1.2, Q1.3 and the `maxTurns` defaults; in audit and sync it feeds family O8 and the `maxTurns` recalibration. No transcripts (another harness, cleared history, a fresh machine): blind spot, and the reference figures of models.md stand in, labeled as such.

## Output profile

```yaml
base_doc: {file, pointer, section_heading, section_span, language, evidence}
scattered_doctrine: [{line, excerpt}]
agents_md: {config, budget}
agent_types: {global: [...], project: [...]}
statusline: true|false
language: {detected, stated_rule, conflict}
isolation: {worktrees_ok, migrations}
checks: {script_path, wired_evidence}
models: {verified_at, stale, main_model, subagent_model_env, subagent_model_force, explore_override}
usage: {window_days, by_type: [{type, runs, calls_per_run, cost_per_run, share}]}   # D12, null when no transcripts
unknowns: []   # never empty on a real repository
```
