# End of run

Phases 4-6. Starts when the plan is exhausted or the tester says stop.

## Phase 4 - Summary and decisions

1. Present: counts (passed, of which verified by agent / failed / skipped by tester / blocked / not tested), then the skipped steps listed separately with their reason, then the notes table (open items first), then the agent suggestions awaiting confirmation (confirm or drop each).
2. Arbitrate with AskUserQuestion: **one question per remark**, multiple choice (2-4 concrete options), **recommended option first**, up to 4 remarks per call, free text allowed. When a remark needs more, run follow-up clarification rounds for that remark. Never a long text list asking "ok, or your choice per number". `[off-scope]` remarks are presented as a separate group, after the in-scope ones. Record each answer in the notes (`Status`, plus a dated line in the Decisions section).
3. Items without a choice are classed: fix now / backlog (`idea` or deferred; goes to the project's TODO or backlog file as the project's rules say) / wontfix.
4. Ask whether to proceed to fixes. "No" => straight to Phase 6 (archive with open items).

## Phase 5 - Fix and re-test

1. **Read the project rules** (AGENTS.md / CLAUDE.md, error registry, test and docs rules) before the first batch. Isolation: worktrees when the project requires or concurrency is possible.
2. **Batch fixes** by area/file set so batches are disjoint; delegate per the project's orchestration doctrine, else: simple text/mechanical `haiku-standard`, standard `sonnet-standard`, complex or data-sensitive `opus-standard`. Each batch gets: the notes rows (observed, expected, lead, decision), files it may touch, the project's checks to run, tests and docs to update in the same commit, the error-registry entry if the project has one. Fix agents never weaken a test or a guard to go green (a failing test is a finding).
3. **Integrate and deploy per the project's flow** (merge into the integration branch, push, deploy workflow). Never merge into or push `PROD_BRANCH` (G7). Pushing needs the user's agreement obtained in Phase 4.
4. **Prove the deployment:** served SHA == the integrated HEAD (prefix compare) before re-testing. Timeout => report, do not re-test against an unverified SHA.
5. **Re-test only the fixed points and the steps skipped by the tester** (offered again, the tester may skip them again): build a short plan from the `fixed` rows and the skipped steps, reuse the step format, re-prepare data (G1-G6 apply). Update statuses: `re-tested ok` / `re-tested ko`. A `ko` returns to Phase 4 (one more round at most before the tester decides to leave it open).
6. Regressions noticed during re-test are new notes.

## Phase 6 - Archive

1. File: `<archive folder>/<date>-manual-test-<scope>.md` (config `archive.filename`; folder from config, plugin option, or detection: `DOCS/AUDIT/`, `docs/audit/`, `docs/`; none found => ask). Language: the project documentation language. No secrets, no personal emails or tokens.
2. Content: header (date, scope and SHAs, target, tester devices, run id), summary table of results, the full notes table with final statuses and decisions, fixes made (commit SHAs), items left open or backlogged, items not tested with reasons, the list of data prepared on preprod and its cleanup state.
3. If the folder has an index (`README.md`, `INDEX.md`, a table of reports), add the entry in its format.
4. Show the file; commit it with the project's convention only after the tester agrees (specific file paths, never `git add -A`; never on `PROD_BRANCH`). Docs-rules of the project (emoji bans, dash rules, language) apply to the archive.
5. Undo the prepared data you tagged when the tester agrees (list first); otherwise leave it and list it.
6. Delete `RUN_DIR` once the archive is written. Final report (short): tested / passed / failed / not tested, fixed and re-validated, still open, archive path.
