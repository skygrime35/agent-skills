---
name: manual-test
argument-hint: "[--scope=develop..main|<ref>..<ref>|branch|all|features:\"a,b\"] [--target=preprod|local] [--mode=guided|autonomous] [--resume] [--dry-run] [--help]"
description: "Runs a manual acceptance test (recette) of a project's user-visible features on preprod or local: scopes the change set, groups it by feature, derives the user journeys, then either walks a human tester through them one short step at a time (guided) or executes them itself in a browser and delivers a screenshot report (autonomous), preparing the needed data itself. Records every remark in a notes file without touching code, then runs a fix and re-test round and archives the notes. Production is never a target. Counterpart of /full-test with a human or a browser agent as tester."
when_to_use: "manual test, recette, autonomous manual test, agent-driven browser acceptance run with screenshot report, acceptance test, guided walkthrough of new features, test the new features with me on preprod, check what changed by hand, user acceptance, UAT, resume a manual test session; also when asked to run manual steps or data-preparing actions against production (this skill must be loaded to refuse and redirect to preprod)"
---

# /manual-test

Plugin options appear in this file as their configured value. In reference files they stay as `user_config.<key>` placeholders: use the value this file shows. If a value still shows as a placeholder here (option never configured), use its `default` in `${CLAUDE_SKILL_DIR}/../../.claude-plugin/plugin.json`.

Skill directory: `${CLAUDE_SKILL_DIR}`. Reference files mark bundled paths with the CLAUDE_SKILL_DIR variable in dollar-brace form; the shell does not set it, so replace it with this directory before running or copying anything.

**Manual acceptance test**, guided (a human tester in the loop) or autonomous (the agent is the tester): what changed -> which features -> which user journeys -> one short step at a time, in chat (guided) or executed by the agent in a browser with a final report (autonomous) -> every remark noted -> decisions -> fixes -> re-test of the fixed points only -> archive. Portable: branches, environment URL, devices, archive folder are detected on every run; non-guessable specifics live in `.claude/manual-test.yml`. It is the human counterpart of `/full-test` (automatic battery); the two skills are independent, this one never runs or requires the other (a green `/full-test` beforehand is a good idea, not a prerequisite).

Reports and chat follow `${user_config.manual_test_language}` (auto = the user's conversation language, fallback en). Every file, identifier and comment stays English except the archived notes, which follow the project documentation language. Steps shown to the tester use the project's user-facing language for UI labels exactly as they appear on screen.

Central promise: **production is never a target and no code changes while exploring.**

**Request to run manual steps, data preparation or "just a quick check" against production / the live site:** refuse plainly, prepare nothing there, no confirmation lifts it (G1). Offer the same walkthrough on preprod, or read-only observation of public pages by the tester alone.

**Harness (first step of Phase 0, every mode, dry runs included).** If `${CLAUDE_SKILL_DIR}` still shows as a literal placeholder, the harness is not Claude Code and the skill directory is the folder holding this SKILL.md. Detect the harness per `${CLAUDE_SKILL_DIR}/../orchestration/references/harness.md` (H1) and announce it with the detected profile. **Claude Code**: the agent types, tools and degradations below apply as written; Haiku types are the default for briefed subagents and for every agent launched by a subagent, a higher type being a ceiling for its role, not a start (H2). **Any other harness**: read each agent type below as its role tier (H3: `haiku-*` light, `sonnet-standard` standard, `opus-*` strong), use the harness's own spawn, question, task-list and stop mechanisms, never name a model; without subagents the waves run inline in their planned order with every gate kept, and each degradation is reported (H2, H5). On every harness, close each agent once its report is used and stop stalled ones before moving on (H4).

## Usage

```
/manual-test [--scope=develop..main|<ref>..<ref>|branch|all|features:"a,b"] [--target=preprod|local] [--mode=guided|autonomous] [--resume] [--dry-run] [--help]
```

- `--scope=` what to test (`references/scoping.md`): `develop..main` (default: integration vs production branch, both detected), `<ref>..<ref>` two refs, `branch` current branch vs its merge-base, `all` every user-facing feature, `features:"a,b"` a named list. Missing => asked.
- `--target=preprod|local`: environment of the walkthrough (default preprod). `production` does not exist as a value (G1).
- `--mode=guided|autonomous`: who tests (default guided; asked at launch if not given). `guided`: a human, one step at a time in chat. `autonomous`: the agent runs every step itself in a browser, captures screenshots and writes a report; the human only reads it (`references/autonomous.md`).
- `--resume` resumes the latest unfinished run; without the flag an unfinished run younger than 7 days is offered for resume.
- `--dry-run`: Phases 0-2 read-only: prints scope, feature groups and the ordered plan (and, in autonomous mode, the browser driver and the NOT TESTABLE steps), then stops. Zero writes (no `.claude/manual-test/`, no config, no data preparation) and ends with a line confirming it.
- `--help` / `-h` alone: print this Usage block and stop.

**Resolution order for every policy answer:** command argument > `.claude/manual-test.yml` > plugin option > recommended default. **Arguments never override G1-G8.**

| Plugin option | Default | Meaning |
|---|---|---|
| `${user_config.manual_test_language}` | `auto` | language of chat and reports |
| `${user_config.manual_test_mode}` | `guided` | who tests: `guided` or `autonomous` (`.claude/manual-test.yml` key `mode`) |
| `${user_config.manual_test_archive_folder}` | `auto` | project folder receiving the archived notes; `auto` = detect (`DOCS/AUDIT/`, `docs/audit/`, `docs/`, else ask) |

Ask (AskUserQuestion, grouped, max 4 questions per call; absent => plain text) only when: scope, target, mode or devices are unknown, a decision belongs to the human (end of run), or a guardrail is hit. Say when degraded.


## Start menu (bare invocation)

A bare invocation shows status and a menu and never auto-runs a mode: rules, freshness and output format in `${CLAUDE_SKILL_DIR}/../orchestration/references/start-menu.md`. State probes: `.claude/manual-test.yml`, an unfinished run under `.claude/manual-test/<RUN_ID>/` (`state.json`: phase, groups done, open remarks), the last archived notes (date, served SHA), commits on the integration branch since that SHA, the last `/full-test` result when its report exists.

Picks: unfinished run => `/manual-test --resume`; remarks recorded but not fixed => `/manual-test --resume` (fix and re-test round); new commits since the last recette => `/manual-test` (guided) and `/manual-test --mode=autonomous` as the alternative; never run here => `/manual-test --dry-run`; nothing new => `/safe-merge`.

Workflow: 1 `/full-test` green -> 2 `--dry-run` (first time) -> 3 `/manual-test` -> 4 fix and re-test -> 5 archive -> 6 `/safe-merge`.

## Scope

**For:** a human (guided) or the agent in a browser (autonomous) validating user-visible behavior on a deployed preprod (or local) stack: screens, buttons, emails, notifications, admin screens, API docs, offline modes; with data prepared by the skill and a fix + re-test round.
**Not for:** automatic batteries (`/full-test`), writing tests (`/test-coverage`), merging or releasing (`/safe-merge`), testing production, load or security testing.

## Governing principles (override any convenience)

1. **One step at a time, short** (also the unit of an autonomous script). 1 to 3 actions, a direct link, the exact expected result, the evidence to send. Never a batch of steps, never a wall of text.
2. **Evidence or it did not pass.** A step is passed only on the tester's answer or evidence (autonomous: the agent's captured artefact), compared to the expected result; for static content (legal texts, versions, translations) the agent's own reading of the repo or served HTML counts, recorded `verified by agent` (G8). Silence, "ok" to a different question or an inference never validate.
3. **Explore read-only.** No code change, no commit, no fix while the tester explores; every remark is noted, not acted on. Short clarification rounds are allowed (`references/step-format.md`).
4. **The skill prepares the state, never the tester.** Accounts, entities, notifications, consent resets are created by the skill through the project's own tools, on disposable preprod data only.
5. **No real third party is ever reached.** Verify before triggering anything that sends (email, push, webhook, chat message, payment).
6. **Disposable by default, reversible when not.** Prefer data the skill created and tagged; record every preparation so it can be listed and cleaned.
7. **Unknown => ask or declare, never assume green.** A journey that cannot be exercised (no device, no data route) is "not tested" in the report.
8. **Verify before sending.** Expected results come from the code, not the feature's purpose: a strong plan review for large plans, a code check of each group just before it is sent (`references/analysis.md`).
9. **Any step can be skipped** by the tester: `skipped by tester`, never failed, offered again at re-test.

## Tooling

- CLIs: `git`, `gh`, `curl` + `jq`, plus the project's own tools (seed, management commands, deploy workflow, `docker`, `ssh` as the project documents).
- Agents: follow the project's orchestration section (AGENTS.md / CLAUDE.md) if present; else the matrix in `references/analysis.md` (haiku reading, mapping and per-group verification, sonnet grouping and journeys, opus for plan review and ambiguous cases); the project's doctrine wins over the matrix. Missing type => the Agent tool `model` parameter (another harness: the role tiers of `harness.md` H3). The chat with the tester is always held by the main loop, never delegated.
- Optional in guided mode: claude-in-chrome or built-in browser MCP to pre-check a link or a screen before sending it (a pre-check never replaces the tester's evidence). Autonomous mode needs a browser driver (`references/autonomous.md`); TaskCreate/TaskUpdate absent => checklist in `state.json`; AskUserQuestion absent => plain-text questions.

## Reference files (load on demand)

- `${CLAUDE_SKILL_DIR}/references/guardrails.md`: **canonical G1-G8**, proof of target, third-party check. Load before Phase 3.
- `${CLAUDE_SKILL_DIR}/references/scoping.md`: Phase 0-1: scope forms, branch detection, environment, devices, config schema.
- `${CLAUDE_SKILL_DIR}/references/analysis.md`: Phase 2: agent matrix, feature grouping, journey derivation, plan format.
- `${CLAUDE_SKILL_DIR}/references/step-format.md`: Phase 3: exact step format with examples, data preparation, re-sends.
- `${CLAUDE_SKILL_DIR}/references/autonomous.md`: autonomous mode: driver resolution, execution rules, screenshots, NOT TESTABLE, delegation, report. Load when the mode is autonomous.
- `${CLAUDE_SKILL_DIR}/references/notes-and-state.md`: notes file, `state.json`, report and screenshots layout, resume.
- `${CLAUDE_SKILL_DIR}/references/end-of-run.md`: Phases 4-6: summary, decisions, fix batches, re-test, archive.

---

# Procedure

Follow the phases in order; register them with TaskCreate. Placeholders are UPPERCASE: `PROD_BRANCH`, `INTEGRATION_BRANCH`, `ENV_URL`, `RUN_ID` (`YYYYMMDD-HHMM`), `RUN_DIR` (`.claude/manual-test/<RUN_ID>/`).

**Mode routing (first):** `--help` => print Usage, stop. `--dry-run` => Phases 0-2 read-only, print the plan, stop. `--resume` or an offered unfinished run accepted => load `state.json` (`references/notes-and-state.md`) and continue at the recorded step. Else run all phases.

## Phase 0 - Preflight and detection
0. **Harness.** Detect and announce it first (**Harness** paragraph above, `harness.md` H1); everything below dispatches through the selected profile.

Load `references/scoping.md`. Read `.claude/manual-test.yml` if present and re-run detection regardless (drift on human-authored fields: keep the stored value, report the diff). Establish `PROD_BRANCH`, `INTEGRATION_BRANCH`, the environment URL for the target, and the project's data-preparation tools. Hard stop if the target environment cannot be established with certainty or is the production URL: list what is missing and where to declare it. Check `git status --porcelain` and the current branch; the skill needs no clean tree but never modifies the tree during exploration (G3).

## Phase 1 - Launch questions

Ask what the arguments did not give: scope, target, mode (guided first), tester devices (desktop, Android, iPhone; autonomous: which viewports the plan needs) and the account to use (login hints from config; never a password in chat or notes). Offer the plain default for each. Create `RUN_DIR` with `state.json` and an empty `notes.md` (not in `--dry-run`); `.claude/manual-test/` is added to `.git/info/exclude` when the project does not already ignore it (never edit the committed `.gitignore` here).

## Phase 2 - Analysis and plan

Delegate per `references/analysis.md`: change set, feature grouping, journeys, what is not manually tested and why. Have the plan reviewed for logic when it exceeds about 15 steps (`references/analysis.md` § Verification), then present the **ordered plan** (feature, risk, device, step count, data to prepare, estimated minutes), the not-tested list and the one-line rationale for the verification passes, then ask once to go or adjust. Steps carry one global numbering. Persist the plan in `state.json`.

## Phase 3 - Execution

**Autonomous mode:** load `references/autonomous.md` and `references/guardrails.md` instead of the tester-facing parts below; the per-group verification, data preparation (G4-G6) and G1/G3 re-assertions are identical, but the agent executes each verified step in a browser, records PASS / FAIL / BLOCKED / NOT TESTABLE with captured evidence and ends with `report.md` (then Phase 4 is offered on the FAIL rows, default STOP).

**Guided mode:** load `references/guardrails.md`, `references/step-format.md`, `references/notes-and-state.md`. Before each group: a mid-tier agent re-checks every step of the group in the code and corrects it (`references/analysis.md` § Verification); mark the group verified in `state.json`. Per step: prepare the state (G4-G6), pre-check links, send the step, wait, compare to expected, record result and remarks, update `state.json`, next. Remarks go to `notes.md` immediately. Suggestions of your own are marked `agent suggestion, to confirm`. Re-assert G1 and G3 before every preparation action. The tester may stop at any time; the run is resumable.

## Phase 4 - Summary and decisions

Autonomous mode: the report replaces the live summary; arbitrate only if the user asks to go on. Load `references/end-of-run.md`. Present the notes table; arbitrate one question per remark (multiple choice, recommended first, max 4 remarks per AskUserQuestion call, `[off-scope]` apart). Record every answer in the notes Decisions section.

## Phase 5 - Fix and re-test

With the tester's agreement: delegate fixes in batches under the project's own rules (worktrees, tests, docs, error registry, push and deploy flow), never merging into `PROD_BRANCH` (G7). After the deployment is proven (served SHA), run a re-test (guided or autonomous, at the user's choice) of **only the fixed points and the steps skipped by the tester or NOT TESTABLE before**, same step format. Anything still failing returns to Phase 4 or is left open in the archive.

## Phase 6 - Archive

Write the dated notes file into the project's archive folder (indexed if the folder has an index), commit it with the project's convention only if the tester agrees, then delete `RUN_DIR`. In autonomous mode the archive also takes `report.md` and the screenshots it references. Final report: tested / passed / failed / not tested, fixed and re-validated, still open.
