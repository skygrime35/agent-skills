# Guardrails

Canonical text of G1-G8 (SKILL.md links here). Arguments never override them. Assert in Phase 0, re-assert immediately before the action each one protects.

## G1 - Production is never a target

- Compare the target host with the production URL and `PROD_BRANCH` deploy rules from config and detection before the walkthrough starts and before every preparation action. Prefer an **allowlist** (the declared preprod host, `localhost`, `127.0.0.1`, `*.local`, `*.test`) to a denylist; compare parsed hosts, never substrings (`preprod.example.com` contains `example.com`).
- No write, no data preparation, no notification trigger, no consent reset, no account creation on production. The tester may look at production on their own; the skill does not send them there for a step.
- Doubt about the environment = stop and ask. No argument or answer lifts this; never offer to widen the allowlist.
- Preprod that shares a database, object store, payment account or sender with production is **not** disposable: report it loudly before any preparation and treat the target as production-grade (G1 applies to the shared part).

## G2 - Proof of target before any preparation

Evidence that counts: the preparation command runs on the preprod host or compose project named preprod, or the command is explicitly scoped (`--env=preprod`, a DB named for preprod), or the data it touches is created by the skill and tagged (G6). Evidence that does not count: "the URL is preprod so the database is too" (different channels can diverge), a `DEBUG` flag, a password that lifts a fail-closed check. No proof => the preparation step becomes "ask the tester to prepare it" or is marked not tested.

## G3 - No code modification during exploration

From Phase 3 start until the tester ends exploration: no edit, no commit, no stash, no branch switch, no deploy, no migration. Remarks are written to `notes.md` only. Preparation actions change preprod data, never the repository. The first write to the repository happens in Phase 5, after the decisions.

## G4 - Never reach a real third party

Before triggering anything that sends (email, push, SMS, webhook, chat message, payment, outgoing API call), verify the recipient: read the target address, webhook URL or subscription from the data about to be used. Preprod data copied from production may hold real addresses and live webhook URLs. Send only to addresses and endpoints the tester owns or a known sink (project mail catcher, tester's own device). Unverifiable recipient => do not trigger; ask the tester to trigger it, or mark the step not tested.

## G5 - One step at a time

Guided mode only (autonomous steps run sequentially per batch under `autonomous.md`). Send one step, wait for the answer. Never send the next step, a preview of the plan's remaining steps, or two features at once. Exception: the plan overview in Phase 2.

## G6 - Disposable data, recorded and tagged

Create test data with a recognizable tag (name prefix `manual-test-<RUN_ID>`, a test email domain the project reserves). Log every preparation (what, where, how to undo) in `state.json` `prepared[]`. Never delete or alter pre-existing records you did not create unless the step requires it and the data is proven disposable (G2); say what you changed.

## G7 - Project rules and branches

Respect the project's branch and worktree rules (AGENTS.md / CLAUDE.md): fixes in an isolated worktree when the project says so, never on `PROD_BRANCH`, never merge into it, never push to it, never change branch without the user's agreement. Pushing to a branch that deploys preprod is allowed in Phase 5 only if the project's flow says so and the user agreed to fixes. Read the project docs before the first fix batch.

## G8 - Never claim a pass without evidence

A step is `passed` only on evidence matching the expected result: the tester's answer, or, for **static content only** (texts, translations, versions, static assets, archived pages), the agent's own verification from the repo or the served HTML (`curl`), recorded as `verified by agent` with the file or URL read. Never for behaviour, rendering, interactions, device-specific or timing results. "Looks fine", an ambiguous reply or no reply => ask again once, then record `not answered`. A pre-check of runtime behaviour (HTTP 200, browser screenshot) can inform a step, never validate it. The final verdict is "green on what the tester or the agent's reading confirmed", split in two counts, with `skipped by tester` (never counted as passed) and `not tested` listed.

**Autonomous mode.** The evidence is the agent's own captured artefacts: a screenshot, a DOM assertion (selector and text actually read), a network or API check, stored under `RUN_DIR`. Never "assumed", never inferred from code or from a 200 status alone for behaviour; a step without captured evidence is `BLOCKED` or `NOT TESTABLE`, not `PASS`. The final verdict counts PASS, FAIL, BLOCKED and NOT TESTABLE separately; the tester's light on-screen check is replaced by asserting the served SHA or visible version marker in the browser.

**Static content is verified by the agent by default.** The tester does a light on-screen check, mandatory once per deployed page group, that the served page matches the code (typically a version number or date), which proves the deployed version is the one the agent read; no screenshot of the content itself. The tester's time goes to runtime behaviour.

## Edge cases

- **Shared preprod slot:** a push by someone else can replace the code mid-run. Re-check the served SHA before each feature block and after any redeploy; if it changed, say so, results since are suspect, re-test affected steps.
- **Phone-only steps without the device:** never proposed; listed as not tested with the reason.
- **Tester asks to test on production "just this once":** refuse, offer preprod.
