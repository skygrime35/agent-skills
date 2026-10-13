# Skill improvements backlog (agents-md, orchestration)

Source: DebriefLab agentic-doc audit, 2026-10-09 (`/agents-md audit` + `/orchestration audit` run on dev-skills 1.1.0, then a read-only review of the skill sources). Paths are relative to `plugins/dev-skills/`. AM = `skills/agents-md`, OR = `skills/orchestration`.

Status legend: **IN 1.2.0** / **IN 1.3.0** = shipped in that release; **BACKLOG** = not done, to decide later.

| # | Proposal | Status |
|---|---|---|
| 1 | Report language default `auto` | IN 1.2.0 |
| 2 | Stable finding IDs + `Fix:` line | IN 1.2.0 (without `--decide`) |
| 3 | One instruction-counting method shared by both skills | IN 1.2.0 (written method, no script) |
| 4 | Audit check: model alias really resolves to the claimed model | IN 1.2.0 |
| 5 | Infrastructure state claims re-probed live | IN 1.3.0 |
| 6 | Archive dead-reference policy option | IN 1.3.0 |
| 7 | Doctrine spread over several headings | IN 1.3.0 |
| 8 | Documented CI-equivalent list vs real workflow jobs | IN 1.3.0 |
| 9 | README note: restart session after installing the plugin | IN 1.3.0 |
| 10 | O8.6 spend check restricted to post-install window | IN 1.2.0 |
| 11 | Bundled dead-path / section-reference scripts | IN 1.3.0 |
| 12 | Contradictions between neighbouring agent-type descriptions | IN 1.3.0 |
| 13 | `fork` / `Plan` built-ins inheriting the orchestrator model | IN 1.3.0 |
| 14 | Ambiguous top of the ladder (is Fable a rung?) | IN 1.3.0 |
| 15 | Statusline model names and oversized `maxTurns` | DROPPED (no statusline template shipped; maxTurns signal cosmetic) |

---

## 1. Report language: default `auto` instead of `en`

- Files: `.claude-plugin/plugin.json` (`orchestration_report_language`; for consistency `legal_report_language`, `test_coverage_report_language`).
- Current: the option description says "auto (conversation language) or a code such as en or fr" but `"default": "en"`; OR `SKILL.md` defines `auto` = conversation language. An unconfigured user gets English reports while conversing in French. agents-md has no such option (its SKILL.md already follows the user's language).
- Change: default `auto`; add "auto = conversation language, fallback en" to the affected SKILL.md.
- Value: real defect observed. Risk: near zero.

## 2. Stable finding IDs and a fix line per finding

- Files: AM `SKILL.md` (Audit report format, mandatory), OR `SKILL.md` (Mode audit).
- Current: P0-P3 headings, check and observed value required; no ID, no fix line. The orchestrator had to request `AM-NN` / `OR-NN` IDs and a suggested fix to arbitrate point by point.
- Change: mandatory unique `<PREFIX>-NN` IDs in report order, reused unchanged by a later sync plan; each finding has `Fix:`, plus `Options:` (2-3, recommended first) when the fix is a real choice.
- Optional extension (not done): a `--decide` step walking the owner through findings in salvos of at most 4 questions, recommended option first, then one sync applying all decisions. Rejected as marginal in the second pass (session orchestration choice, not a skill defect).
- Evals: deterministic grader (ID regex + `Fix:` presence) on `agents-md-audit-readonly` and `orchestration-audit-readonly`.

## 3. Instruction budget: one counting method

- Files: AM `references/audit-checks.md` (P2.1), OR `references/detection.md` (D4), AM `references/structure.md` (Instruction budget).
- Current: P2.1 gives two heuristics (`grep -c '^- '` and modal counting); D4 says "same method as P2.1" without defining it. Same AGENTS.md measured ~227 (agents-md) vs ~177 (orchestration).
- Change: define the method once in `structure.md` (unit = normative statement, a bullet with a modal counts once; always-loaded files + followed `@imports`; harness ~50 counted separately; ± margin); P2.1 and D4 cite it, D4 reuses the agents-md figure when available.
- Alternative (not done): a shared deterministic `scripts/count_instructions.py` emitting JSON per file/section. Heavier to maintain.

## 4. Audit check: alias resolution vs claimed model

- Files: OR `references/audit-checks.md` (O8), `scripts/usage_by_agent_type.py` (D12), `references/config-schema.md` (`quirks`), `references/agent-types.md`.
- Current: `models.md` documents "aliases lag new releases" and `agent-types.md` recommends the full ID when needed, but only init Phase 4 checks resolution; nothing in audit.
- Observed: OR-01, the `haiku` alias resolved to Haiku 4.5 on CLI < 2.1.293 for 7/7 runs while the type claimed Haiku 5.5 (~10x price, effort ignored).
- Change: new O8 check comparing `message.model` + CLI `version` in subagent transcripts to the claimed model (P1 if price ratio >= 2x, else P2; no transcripts = blind spot); D12 outputs resolved model and CLI version per type; structured `quirks` (`{type, alias, resolves_to, min_cli, pin}`); recommend pinning the full ID while an alias is unstable and never hardcoding a version in descriptions.

## 5. Infrastructure state claims re-probed live

- File: AM `references/audit-checks.md`, next to P1.4.
- Current: P1.4 covers state claims contradicted by repository artefacts; external state (CI, services, quotas, disabled features) is only implicitly covered by P1.1.
- Observed: AM-01, the doc declared hosted CI permanently "phantom" and told agents to delete runs; live probes showed real runs with 4 failing jobs (found anyway by the agent).
- Proposal: explicit check probing such claims read-only (`gh run list`, `gh run view --json jobs`, `docker compose config`, stat); contradicted = P1, P0 when paired with a destructive action; unprobeable = blind spot.
- Second-pass verdict: marginal (principle already covered).

## 6. Archive dead-reference policy

- Files: AM `references/config-schema.md`, `references/audit-checks.md` (P1.2), `plugin.json` (new `agents_md_archives_policy`).
- Current: no stance on dated records (`errors/`, `adr/`, `postmortems/`); tolerating them (AM-33) was the agent's own judgment. The owner chose to correct them with "`new` (formerly `old`)" annotations.
- Proposal: `archives: {paths, policy: tolerate | annotate | fix}`, default `tolerate`; audit reports one P3 info finding with the count; sync `annotate` only touches the reference, never the record body.

## 7. Doctrine spread over several headings

- Files: OR `references/config-schema.md` (`section_heading`, `section_span`), `references/detection.md` (D2), `references/audit-checks.md` (O3).
- Current: single heading + single span; D2 records "scattered doctrine"; O3.1 only fires when parallelism and isolation are split. Doctrine spread over 5 sibling headings (DebriefLab §5-§9) produced no finding (OR-05 was manual).
- Proposal: `section_spans: [{heading, start, end}]` (keep `section_span` as alias); D2 accepts consecutive sibling headings on the same topic; new O3 check P2 when doctrine spans >= 3 headings (recommend a parent heading or record the spans); sync never writes outside recorded spans.

## 8. Documented CI-equivalent list vs real workflow jobs

- File: AM `references/audit-checks.md`, P3.4.
- Current: P3.4 only checks that each workflow file is cited by name.
- Observed: AM-20, the local replay list omitted 9 jobs of `ci.yml`.
- Proposal: when the doc has a "CI-equivalent / replay locally" list, extract `jobs.*.steps[].run` and compare; missing job = P2; allow `ci_replay_excludes` in config.

## 9. README: restart the session after installing the plugin

- File: repository `README.md`.
- Observed: a plugin installed mid-session was not loadable by the Skill tool until restart.
- Proposal: one line in the README. Not a skill defect.

## 10. O8.6 spend check noise

- File: OR `references/audit-checks.md` (O8.6).
- Current: "`{TOP}-deep` above 25% of subagent spend over the window"; only O8.9 restricts to sessions after the types were installed.
- Observed: OR-02 flagged 40.9% for `opus-deep`, all from runs before the current matrix (0 since): noise.
- Change: same post-install window as O8.9; window < 7 days = P3 observation with a suggested re-measure date.

## 11. Bundled dead-path and section-reference scripts

- Files: new AM `scripts/check_dead_paths.py`, `scripts/check_sections.py`; AM `references/audit-checks.md` P1.2/P1.3.
- Current: P1.2 is a bash one-liner (backtick paths only); P1.3 a generic `grep -q`.
- Observed: the audit agents improvised `deadpaths.py` / `sections.py` (markdown links, anchors, line numbers, suffix resolution via `git ls-files`, domain AGENTS.md files, `FILE § Section` citations). These checks produced most P1 findings.
- Proposal: ship both (TSV `file:line<TAB>target<TAB>status`, read-only, stdlib), call them from P1.2/P1.3, widen scope to domain files.
- Second-pass verdict: marginal (P1.2 snippet considered sufficient).

## 12. Contradictions between neighbouring agent-type descriptions

- File: OR `references/audit-checks.md` (O2).
- Current: O2.1 compares doctrine to one type's frontmatter; descriptions are never compared to each other.
- Observed: OR-04, `opus-standard` said "for ordinary development use sonnet-standard" while the doctrine default is `haiku-standard`, pushing work mid-tier (OR-03).
- Proposal: new O2 check P2: each description that routes to another type must agree with the doctrine default.

## 13. `fork` / `Plan` inheriting the orchestrator model

- Files: OR `references/audit-checks.md` (O8.4), `references/doctrine-content.md`.
- Current: O8.4 only covers the `Explore` override and `CLAUDE_CODE_SUBAGENT_MODEL`.
- Observed: OR-13, `fork` 29 runs / $143 over 30 days on the parent model.
- Proposal: extend O8.4 to `fork` and `Plan` (P3 with measured spend) and offer an optional doctrine clause "`fork`/`Plan` run on the orchestrator's model: never for briefable work", conditional on measured spend (budget cost).

## 14. Ambiguous top of the ladder

- Files: OR `references/doctrine-content.md` (B1, B7), `references/audit-checks.md`.
- Observed: OR-14, "a verified failure on the highest rung goes back to the user" vs "Fable is chosen per invocation ... only for what exceeds Opus": unclear whether Fable is a rung.
- Proposal: new O2 check: when the top model is outside the matrix, the doctrine must say it is not a rung.

## 15. Statusline model names and oversized `maxTurns`

- Statusline: OR-09, the machine-local `subagent-statusline.sh` showed "Opus 5" for Opus 5.5 and "Haiku 5 5". Check first whether the skill ships a statusline template (not seen in `templates/`) before proposing anything.
- `maxTurns`: OR-10, caps far above measured usage (e.g. haiku-quick 130 for 5 calls/run). O8.7 only flags caps that are too low; a P3 signal when cap > 3x measured p95 would be cosmetic. The owner kept the current caps in DebriefLab.

---

## Round 2 (2026-10-13, field report from a fresh Go repo, plugin 1.3.0) — all IN 1.4.0

| # | Proposal | Status |
|---|---|---|
| R2-1 | agents-md checkers go to `.claude/agents-md/` (option `agents_md_guardrail_scripts_path`), `scripts/` only when git already tracks `scripts/check_*`; sync proposes relocation | IN 1.4.0 |
| R2-2 | orchestration checker goes to `.claude/orchestration/` with the same tracked-checkers exception | IN 1.4.0 |
| R2-3 | agents-md no longer writes "Concurrency isolation" (owned by orchestration); its report recommends `/orchestration`; orchestration absorbs a legacy subsection | IN 1.4.0 |
| R2-4 | Phase 4: new agent types visible only after harness reload; verify the resolved model from the transcript | IN 1.4.0 |
| R2-5 | B4 omitted when the base doc already has an ask-on-ambiguity rule (`omitted-redundant`) | IN 1.4.0 |
| R2-6 | `check_agent_refs.py --only-owned` for CI (non-owned files and absent global dirs are warnings) | IN 1.4.0 |
| R2-7 | agents-md avoids volatile state (current branch, task in progress, open PRs, drifting counts) in every agentic doc, arbitrating exceptions itself; audit flags it under P2.5 | IN 1.4.0 |
| R2-8 | agents-md writes a one-line isolation stub (`agents-md:isolation-stub`, one worktree per parallel agent, points to `/orchestration`), which orchestration replaces | IN 1.4.0 |
| R2-9 | Tracked-checkers exception ignores dev-skills' own checkers (they are a relocation candidate, not a project convention) | IN 1.4.0 |
| R2-10 | Evals: audit flags volatile state, sync proposes checker relocation, orchestration init absorbs the stub | IN 1.4.0 |
