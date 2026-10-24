# Autonomous mode

Phases 3-4 when `--mode=autonomous`. The agent is the tester: same scope, plan, per-group code verification, grounded expectations and app-built links as guided mode (`analysis.md`, `step-format.md`); only the executor and the evidence change. The human reads the report. Guardrails G1-G8 apply unchanged (G5 concerns the human channel and does not apply; G8 is adapted, see `guardrails.md`).

## Mode selection

`--mode=guided|autonomous` > `.claude/manual-test.yml` key `mode` > plugin option `manual_test_mode` > `guided`. Not given by argument or config: ask at launch (Phase 1) with `guided` first. Dry run: the plan also states, read-only, which driver would be used and which steps would be NOT TESTABLE.

## Browser driver resolution

Resolve once in Phase 0/1, record in `state.json` `driver`; first match wins:

1. **The project's own E2E stack** when present (for example Playwright or Cypress already installed for its tests): reuse its runtime, login helpers, base URL and basic-auth handling. Write throwaway scripts only under `RUN_DIR/driver/`; never edit or add files in the project's test suite, never change its config or dependencies.
2. **A browser automation MCP** available in the session (Claude in Chrome, the built-in browser tools).
3. **Neither:** install nothing silently. Report the blocker (what was looked for), offer guided mode, or an install the user explicitly approves.

Headless by default. Viewports: desktop (1440x900) for every step; a mobile emulation (390x844, touch, mobile user agent) for steps whose plan targets a phone. State plainly in the report that emulation is not a real device: layout and touch only, no real browser engine quirks, push, sensors or install flows. Basic-auth or SSO gates of the target: use credentials from the environment variable or file names declared in config, never print them.

## Execution rules

- **One scripted step = the guided step**: 1 to 3 actions plus a precise expected result, with login steps self-contained (same `step-format.md` rules; the "Send back" part becomes the evidence captured).
- The agent performs the actions, waits for the expected condition with bounded timeouts (default 10 s per wait, 60 s per step, longer only for a stated async trigger), compares observed with expected and records `PASS`, `FAIL`, `BLOCKED` or `NOT TESTABLE` with evidence. Dependent steps of a blocker are `BLOCKED by #n`.
- **Evidence** is always a captured artefact: screenshot, DOM assertion (selector and text read), network or API response. Static content may still be `verified by agent` from the repo or served HTML (G8).
- **Flakiness:** a failing step is re-run once (fresh page, state re-prepared if needed) before `FAIL` is recorded; both attempts are kept with their artefacts. Fails twice => `FAIL`; differs => `PASS (flaky, 1 of 2)` and a note.
- **Screenshots:** always on `FAIL` and `BLOCKED` (full page, plus the element when relevant); one representative screenshot per passed feature; for failing steps also the browser console errors and the failed network requests (URL, status). Files: `RUN_DIR/screenshots/<step>-<slug>-<attempt>.png` (step number zero-padded to 3 digits).
- Remarks the agent notices (UX, text, off-scope) go to `notes.md` as `agent suggestion, to confirm`, never silently as findings. Re-assert G1 and G3 before every preparation action and before every navigation to a new origin; follow no link that leaves the allowlist.

## NOT TESTABLE

Never fake. Classify as `NOT TESTABLE` with the reason and the cheapest way a human can check later:

| Cannot do autonomously | Cheapest human check |
|---|---|
| Real device push reception, install as app, camera, share sheet, physical sensors | one tester on the real device, steps listed in the report |
| Real third-party OAuth consent screens, SSO with real identities | tester logs in with their own account |
| Real email inbox (outside the project's mail catcher) | tester checks the inbox, or the catcher is read when the project has one |
| Payment with real cards | provider test mode by the tester, or a human run in guided mode |
| Anything needing an external account the agent does not hold | name the account and the action |

## Delegation

Execution batches may be delegated per feature group (`haiku-standard` by default, since the steps are verified and fully briefed; `sonnet-standard` for a group whose steps need judgment on ambiguous screens; the project's orchestration doctrine wins, fallback matrix in `analysis.md`). Each batch brief: the verified steps, `RUN_DIR`, driver, allowlist and credentials source, G1-G4 and G6, the output contract. Each returns structured results per step: `id`, `result`, `observed`, `attempts`, `artefacts` (paths), `console`, `network`, `lead`. The coordinator consolidates into `state.json`, `notes.md` and the report. **Never run two batches that mutate the same preprod data concurrently**: serialize groups that share entities, accounts or settings; parallelize only groups with disjoint prepared data. The final report is always written by the coordinator. Each batch agent stops the browser session and every background process it started before returning, and the coordinator closes each batch agent once its results are consolidated (`../../orchestration/references/harness.md` H4).

## Report

At the end of the run write `RUN_DIR/report.md` in the user's language (`user_config.manual_test_language`), next to `screenshots/`:

1. **Summary table:** feature, steps, PASS / FAIL / BLOCKED / NOT TESTABLE counts, totals.
2. **Per FAIL:** title, severity proposal (blocker, major, minor, cosmetic), step, URL, actions, expected, observed, screenshot(s), console and network evidence, reproduction steps, code lead (`file:line`, a hint, never a fix).
3. **Per feature:** what passed, with the representative screenshot.
4. **NOT TESTABLE:** each item with its reason and how to check it manually.
5. **Environment:** target URL, served SHA, data prepared (from `prepared[]`), browser and driver, viewports (with the emulation caveat), date, run id.

Then offer, in one line each: publish it as a richer private page if the host supports one (no specific tool required; screenshots referenced by their files otherwise), and archive it in the project's audit folder (same rules and ask-before-commit as `end-of-run.md` Phase 6; copy `report.md` and the screenshots it references, no secrets). **Default after the report: STOP, no fixes**, unless the user asked otherwise. To continue, resume `end-of-run.md` Phases 4-5 from the FAIL rows (each FAIL is a notes row); the re-test of the fixed points is autonomous or guided at the user's choice.

## State and resume

`state.json` records `mode`, `driver` (kind, runtime path or MCP name, viewports) and, per step, `result`, `attempts` and `artefacts` paths (see `notes-and-state.md`). An interrupted autonomous run resumes at the first step without a final result: re-check the served SHA, re-verify `prepared[]`, never re-record a step already final.
