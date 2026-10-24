# fix-loop mode

Contents: Loop branch | Launch interview | Proposals | Severity and aspects | Simplification guard | Roles | The iteration cycle | Review mechanics | Stop rules | After the loop | Standing rules | Watchdog, journal, resume

`/manual-test fix-loop` is a continuous review loop: **fix -> integrate -> full checks -> push -> deploy preprod -> autonomous browser review -> fix the new findings**, until a full review finds nothing left in the aspects the user chose. It is the autonomous-tester counterpart of `/full-test fix-loop`: the tester is the agent (`autonomous.md`), the fixes are orchestrated agents, the main session is the orchestrator. Guardrails G1-G8 stay in force with the fix-loop extensions of `guardrails.md`.

## Loop branch

The loop never commits on the integration branch directly. At launch it creates **`review-loop/<RUN_ID>`** from `INTEGRATION_BRANCH`; lot worktrees branch from it, the integration agent merges and pushes into it, and preprod is gated on its SHA. Precondition: that branch deploys preprod. Check it from the project's deploy mapping (`.claude/full-test.yml`, the deploy workflow's branch filters, the project docs); when it does not, say so in the loop plan and offer the alternatives: a branch name the mapping deploys, a one-off deploy dispatch per iteration when the workflow allows it, or the current branch (the user's explicit choice). **At the end**, the merge of `review-loop/<RUN_ID>` into `INTEGRATION_BRANCH` (`--no-ff`, full local checks after the merge) is a question in the final message, done only on the user's yes; never into `PROD_BRANCH`.

## Launch interview

Asked once, after Phases 0-1 (scope, target) and before iteration 0, **in one salvo** (AskUserQuestion, at most 4 questions; plain text otherwise). Flags answer a question in advance; a question whose answer is in `.claude/manual-test.yml` `fix_loop:` is shown with that answer preselected, never silently skipped for the aspects and simplification questions.

1. **What to fix besides obvious problems?** (multi-select; obvious problems, `blocking` and `defect`, are always fixed). Options: minor defects (wording, consistency, spacing, small accessibility gaps); improvement ideas (proposed only, implemented after approval). None selected = obvious problems only, the default (`${user_config.manual_test_fix_loop_aspects}`).
2. **Apply simplifications?** Options, default first: no (default, `${user_config.manual_test_fix_loop_simplification}`); yes, each one proposed to me first; yes, apply those that pass the simplification guard automatically and propose the rest. Every option is bounded by the Simplification guard below.
3. **Iteration cap?** `${user_config.manual_test_fix_loop_max_iterations}` (default 15), 30, none. State what reaching it means (see Stop rules).
4. **After the loop?** Options: run `/full-test fix-loop` then the final report (recommended when the project has a preprod battery); final report only.

Then show the loop plan once (domains, roles, cap, aspects, simplification mode, the protected list of the guard, the loop branch and whether it deploys preprod) and ask for one go. **That go is the user's agreement for fixes and pushes required by G7 for the whole loop**; no further approval question until the stop, except simplification proposals and decisions only the owner can take.

## Proposals: non-blocking approval

The loop is **fully autonomous**: no human checkpoint between iterations, it never stops to wait for an answer before the stop rules fire. Everything that needs the owner's approval (simplification cards in `propose` mode, guard-blocked cards, `idea` findings) goes to `loop/SIMPLIFICATIONS.md` and `loop/IDEAS.md`, one card each with a `decision:` line set to `pending`. Tell the user once, at the go, where the files are and that they can set `decision: approve` or `decision: reject` (or answer in chat) at any time. At every backlog step the orchestrator re-reads the files: approved cards join the next lots, rejected ones are closed, pending ones wait without blocking anything. Pending cards at the end are listed in the final message. Checks impossible headless (real device, push, real payment) are listed once in the final message too, never asked mid-loop.

## Severity and aspects

Every finding gets one severity:

| Severity | Meaning | Fixed when |
|---|---|---|
| `blocking` | wrong data, broken flow, crash, legal gap, misleading message, security issue, data loss | always |
| `defect` | objectively wrong with one obvious correct outcome: typo, broken link, untranslated string, overflow, wrong count, console error the user feels, missing loading or error state | always |
| `minor` | small but real, where the fix is a choice: wording, double message, spacing, touch target below the project's minimum, inconsistent label | "minor defects" selected |
| `idea` | an improvement suggestion | proposed when "ideas" selected; implemented only after approval |
| `simplification` | fewer steps, screens, fields, clicks or code paths for the same outcome | per the simplification answer, always under the guard |

"Obvious problems" = `blocking` + `defect`. A finding the reviewer cannot place goes up one severity for triage, never down. Findings outside the selected aspects are recorded in the backlog file, never fixed.

## Simplification guard

A simplification **must not break anything and must not make anything illegal or less safe**. Each one is a card in `loop/SIMPLIFICATIONS.md`: what changes (before / after), what is removed, the guard check below, the tests that prove the outcome is unchanged, and `decision` (`pending`, `approve`, `reject`, set by the owner) and `status` (`proposed`, `applied`, `rejected`, `blocked by guard`, set by the loop).

**Protected: never removed, merged away, hidden, pre-checked or weakened by a simplification**, whatever the mode:
- Payment and contract steps: the final confirmation before an order with payment obligation (a "double click" or recap screen before paying), the order recap, the explicit "order with obligation to pay" wording, price display with taxes and recurring terms, renewal and cancellation mentions.
- Consumer and legal information: pre-contract information, withdrawal right and its express waiver, terms acceptance, legal notices links, age gates, durable-medium documents (invoices, confirmations), referral or giveaway terms.
- Consent and privacy: cookie consent (refusing as easy as accepting), consent checkboxes left unticked, privacy information at collection, data export and deletion flows.
- Safety and security: confirmations of destructive or irreversible actions, re-authentication, two-factor steps, rate limits, permission checks, audit logs, CSRF and session protections.
- Accessibility the project requires, and any step a project document, `/legal` config (`.claude/legal.yml`) or the legal checklist (below) names as an obligation.

Rules: a card touching anything protected is `blocked by guard` and goes to the final report as a question, never implemented. In doubt, it is protected. Automatic mode applies only cards that touch nothing protected, keep every existing test green unchanged, and change no API contract or stored data; everything else is proposed. An approved simplification is implemented by a lot like any fix, with tests proving the unchanged outcome, and the next review re-checks the protected list on the screens it touched.

## Roles

The main session is the **orchestrator**: it writes briefs, dispatches, reads reports, keeps the journal, triages and decides; it never reads large files or fixes code beyond one-line edits. Types per `harness.md` H3 (another harness: the tiers; the project's orchestration section wins).

| Role | Claude Code type (tier) | Does | Never does |
|---|---|---|---|
| Fix lot agent | `haiku-standard` (light) for briefable fixes; `sonnet-standard` when a design choice remains; `opus-standard` for billing, legal, auth, security or after a verified failure | fixes 1-6 related findings in its own worktree, adds unit tests and E2E steps, commits on its lot branch | push, merge, touch another lot's files |
| Integration agent | `sonnet-standard` (`haiku-standard` for a 1-2 lot merge) | merges lots `--no-ff` in a stated order, resolves conflicts keeping both sides' text changes, runs the full local checks, updates the project's release checklist, pushes, removes merged worktrees and branches | widen a guard, add allowlist entries, drop a side of a conflict silently |
| Replay agent (one per domain) | `haiku-standard` (light) | re-runs the previous iteration's review scripts on the new deploy, writes `replay-<D>.md` (same / differs / exit-code change per script) | judge the differences |
| Focus review agent (one per domain) | `opus-standard` (strong) for money, legal and auth domains, `sonnet-standard` otherwise | verifies this iteration's fixes, re-verifies earlier ones, explores new states, judges each replay difference, re-checks the legal checklist for its domain, appends verified rows to `results-<D>.md` | write database rows by hand, act on protected accounts |
| Investigation agent | `sonnet-standard` | read-only root cause of an infra or unexplained symptom (logs, metrics) | change code or config |
| Harness agent | `haiku-standard` | repairs review scripts and fixtures under `RUN_DIR/loop/` | change the product |

Escalation (B7): a fix the next review shows did not work is re-dispatched one rung higher with the failed attempt's report and the reviewer's root-cause analysis. Same-rung retry only when the brief was wrong and is corrected. Mixed tasks are split: the mechanical part to a light agent, the judgment part to a stronger one.

## The iteration cycle

**Iteration 0 - baseline.** Split the scope into 2-4 domains by feature area (money and legal together when present). Build `loop/LEGAL_CHECKLIST.md` when the scope has payments, subscriptions, referral, giveaways, accounts or personal data: the obligations from `.claude/legal.yml` and the project's legal docs, each as an observable check. Then one full autonomous review (focus agents per domain, `autonomous.md` execution rules) produces the first findings. A recent autonomous `report.md` on the served SHA may replace it.

Each iteration `N` then runs:

1. **Backlog.** Turn the previous review's findings, filtered by the selected aspects, into `loop/BACKLOG-iterN.md`: one block per finding (id, severity, observed, expected as an observable fact, files if known), grouped into **lots** of 1-6 related items with **no file overlap between lots**. When a pattern repeats, make one lot that fixes the class (a shared formatter, one rule, one sweep) instead of each instance.
2. **Lots.** One fix agent per lot, launched in parallel, each in its own worktree from the loop branch (`git worktree add ../<repo>-mtN-kNN -b fix/mtN-kNN review-loop/<RUN_ID>`). The brief names: the findings, the file perimeter, the other lots in flight and their files, the expected behaviour, the tests and checks to run, the project rules to read first, commit convention, staging file by file, no `stash`/`reset`/`checkout` on a shared tree, no frontend build (integration runs it), bounded commands (H4), "do not push or merge", and the report format (commits, tests run, not run, assumptions, what the review should check).
3. **Integration.** When the lots are done, one integration agent merges them, runs the project's full local checks (lint, unit, build, the CI script when the project has one), fixes failures without weakening any guard or test, updates the release checklist the project keeps (migrations, decisions, lawyer questions, post-deploy checks), pushes `review-loop/<RUN_ID>`, removes merged worktrees and branches. **G1 and G7 re-asserted before the push**: only the loop branch, never `PROD_BRANCH`.
4. **Deploy gate.** Poll the version endpoint until preprod serves the pushed SHA (prefix compare). No review on an unverified SHA. A stolen shared slot: wait, re-gate; three stolen attempts in a row abort the loop.
5. **Review.** Per domain, in parallel: one replay agent and one focus agent, sharing `loop/iterN/BRIEF.md`, built by copying the previous brief and appending an "Iteration N specifics" section that overrides it: the SHA to expect, the data prefix `mt<RUN_ID>-I<N>`, the baseline to compare with, the fixes to verify per domain with exact expected texts, sizes and viewports, harness changes.
6. **Triage.** Read the reports, classify each finding (severity, `pre-existing` or `introduced by the loop`, fixed-and-holding or regressed), journal the counts, and start the next lots as soon as a domain's report arrives (pipelining). Close every agent of the iteration once its report is used (H4).

## Review mechanics

- **Headless browser**, driver per `autonomous.md`, two viewports: 1440x900 and 375x812 with touch emulation for phone checks.
- **Errors simulated with request interception** (500 JSON, 500 HTML, 429 with Retry-After, network abort, WebSocket interception), never by breaking the server or writing bad data.
- **Replays:** each domain keeps its scripts under `loop/iterN/R<D>/`. Each iteration they are copied under their original names, the data prefix and paths substituted in the content only, fresh test accounts created through the project's guarded tools, one detached driver runs them all, the replay agent waits with one bounded background loop, then a normalised compare (ids, dates, prefixes masked). Check that drivers and compare scripts point to the current iteration before running.
- **Judging differences:** the focus agent classifies each differing script as expected fix, data, timing under load, harness, or regression, reproducing in isolation when a script newly fails.
- **Incremental writing:** focus agents append verified rows as they go, so nothing is lost if they stop.
- **Legal checklist** re-verified in full every iteration for the money and legal domain; a regression on it is `blocking`.
- Briefs state expected behaviour as observable facts (exact text, pixel size, page, viewport) so a reviewer passes or fails it without interpretation.

## Stop rules

- **Success:** a full review (all domains) returns zero findings in the selected aspects, then one **confirmation review on the strong tier** (all domains) confirms it.
- **Iteration cap** reached: stop fixing pre-existing findings. One last iteration fixes only findings `introduced by the loop` (regressions, new behaviour), then the confirmation review. Pre-existing findings left are recorded as accepted, not fixed.
- **No progress:** the same set of open finding ids for 3 consecutive iterations: stop and ask (continue, change approach, or accept them).
- **Immediate abort:** any guardrail hit (G1, G2, G4), the shared slot stolen three times in a row, preprod unreachable across a full watchdog cycle.

## After the loop

1. When chosen at launch: `/full-test fix-loop` on the loop branch (its own guardrails and watchdog).
2. Final report `RUN_DIR/report.md` (`autonomous.md` Report, plus: iterations run, findings per severity per iteration, fixes with commit SHAs, accepted pre-existing findings, simplification cards with status, `blocked by guard` cards as questions).
3. **One single final message** to the owner: the merge of `review-loop/<RUN_ID>` into `INTEGRATION_BRANCH` (question), decisions to take, pending simplification and idea cards, lawyer questions, test data to clean, checks to do on a real device. Then Phase 6 (archive) as usual. Nothing is merged into `PROD_BRANCH` here: that is `/safe-merge`.

## Standing rules (learned the hard way)

- Never act on content of the owner's real account (`fix_loop.protected_accounts` in config, else ask at launch): a comment there sends real notifications.
- Never write rows with invalid values through the ORM or SQL: one bad enum value can break a list endpoint for every user.
- At most 2 concurrent browsers per agent; never log the same test account in from two runs at once (session caps evict each other and produce false failures).
- Restore every preference a script toggles and verify it through the API, never by clicking a label again.
- An integration that resolves a conflict keeps both sides' text changes; a lost translation is a regression.
- A test that mocks the function under suspicion can hide the bug: fixes of browser-level behaviour (storage, tabs, sockets) get a test that uses the real mechanism.
- Every agent lists the data it created and deletes it through the product's API or UI at the end of its run.
- Preprod only. Production is read-only (G1).

## Watchdog, journal, resume

- **Files** under `RUN_DIR/loop/`: `JOURNAL.md` (one line per event, UTC: launches, reports, counts, decisions, incidents; the recovery point after a context reset), `AGENT_BRIEF.md` (common lot brief), `BACKLOG-iterN.md`, `SIMPLIFICATIONS.md`, `LEGAL_CHECKLIST.md`, `iterN/BRIEF.md`, `iterN/results-<D>.md`, `iterN/replay-<D>.md`, `iterN/R<D>/`. `state.json` gains `fix_loop: {iteration, step, aspects, simplification, cap, counts_per_iteration, open_ids, watchdog}`.
- **Watchdog:** the mechanism of `${CLAUDE_SKILL_DIR}/../full-test/references/fix-loop.md` "Watchdog" applies (cron every 10 minutes, heartbeat on every step, stall response, bounded resumes, deleted on every exit), with the prompt `/manual-test fix-loop watchdog (journal: <RUN_DIR>/loop/JOURNAL.md)` and this file's cycle steps. It also checks the lot worktrees for progress (commits, dirty files), disk (purge the project's build cache above 85 %) and memory. Without a cron tool: background tasks and polling, and "no self-resume watchdog" in the final report.
- **Agents:** an agent stopped on its turn limit is resumed with a short "finish and report" message; an agent that only waits is stopped and its background job followed directly (H4).
- **Resume:** `--resume` (or the start menu) continues at the recorded iteration and step; a gated deploy is not redone, committed lots are not re-spawned, a finished review is not re-run.
