# Writing — build's rules: isolation, fixtures, skips, discovered bugs, guardrails

Mode `speed` reuses §1's agent contract (one runner per agent, its own files only), §4's baseline rule and §5's prod guardrail verbatim; its write surface is different (test infrastructure, never test bodies) and lives in `speed.md` §5.

## 1. Isolation model

- **Unit of parallelism = the target test file.** One agent per file, `sonnet-standard` (unit/integration) or `opus-standard` (e2e — selectors, waits, and flake diagnosis need the deeper tier). Each agent's contract, verbatim in its prompt: write the assigned scenarios into YOUR file only; run YOUR file only (the framework's `single:` command from the config); iterate to green; **never edit application code, another test file, or shared fixtures; never weaken an assertion below the scenario's `expected_outcome`; never target a host in `prod_hosts`**. A needed-but-missing helper is a returned request, not an improvised local copy.
- **Fixtures/helpers first, serialized.** Before the fan-out, the main loop (or one `sonnet-standard`) writes/extends shared fixtures, factories, and seed helpers the plan identified — one pair of hands, because two agents inventing the same `createTestUser` produce exactly the drift V-checks exist to catch. Fan-out waves start only after this package is green.
- **Wave sizing.** Group files into waves so that files sharing a mutable resource (same local DB schema, same emulator instance) run in different waves or with the project's own isolation (transactions, per-test DBs). Read-only-vs-app test files can wave together freely.

## 2. Per-framework idioms (skip/todo + single-file run)

Recorded in the config at detection; defaults:

| Framework | Skip/todo idiom | Single file |
|---|---|---|
| vitest / jest | `it.todo('…')` / `it.skip('… // TC-BUG-nn SCEN-nnnn')` | `npx vitest run FILE` / `npx jest FILE` |
| pytest | `@pytest.mark.skip(reason="TC-BUG-nn SCEN-nnnn: …")` or `xfail(strict=True)` | `pytest FILE` |
| playwright | `test.fixme('… TC-BUG-nn SCEN-nnnn')` | `npx playwright test FILE` |
| cypress | `it.skip(…)` + comment marker | `npx cypress run --spec FILE` |
| go test | `t.Skip("TC-BUG-nn SCEN-nnnn: …")` | `go test ./pkg -run TestName` |
| cargo test | `#[ignore = "TC-BUG-nn SCEN-nnnn"]` | `cargo test name` |

The `TC-BUG-nn SCEN-nnnn` marker string is **mandatory and grep-exact** — verify V4 matches skips to bugs by grepping it. Prefer `xfail(strict=True)`-style idioms where they exist: the suite then *announces* the day the bug is fixed (the test flips to unexpected-pass) instead of rotting as a skip.

## 3. Discovered-bug protocol (build B5)

Trigger: a written test, asserting exactly the scenario's `expected_outcome`, fails — the expected error never occurs, a different error occurs, a crash occurs, or state is left corrupted.

1. **Re-verify the test, not the code.** Once, deliberately: is the fixture wrong, the selector stale, the outcome misread from the code? An agent that cries bug on its own typo burns the finding channel's credibility.
2. If the test is right: mark it with the framework's skip/todo idiom + the marker string; keep the true assertion **intact inside the skip** — it documents the expected behavior and becomes the regression test the day someone fixes the bug.
3. Record: `bugs:` entry in the inventory (id, scenario, test locus, `state: open`), scenario `coverage.status: bug-found`.
4. Report: a `TC-BUG-nn` finding (P0 on critical path, else P1) with a **repro** — the exact commands/steps, observed vs expected outcome.
5. **Never**: fix application code, weaken the assertion, delete the scenario, or leave the test failing red in the suite (a red suite hides the next regression behind noise).

## 4. Baseline and non-regression (B2 / B6)

- **B2 baseline** runs before any write: full local suite, results recorded per test. Pre-existing failures are named at the hard gate and never attributed to the new work.
- **B6 non-regression** runs after all waves: full local suite, **mutating suites serialized** (per-file green in parallel proves nothing about shared-state pollution — this is where it surfaces), read-only suites in parallel. Diff vs baseline: new failures in *old* tests caused by new fixtures/seeds are the build's to repair (fixtures, not app code) before reporting; anything else new is triaged as a possible `TC-BUG`.

## 5. The prod guardrail, mechanically

- Before **every** test execution (per-agent single-file runs included): resolve the run's effective target (env vars, config files the runner reads) and check it against `prod_hosts`. Match ⇒ do not run, emit the violation.
- After writing: `rg` every written/modified test file for each `prod_hosts` entry (and obvious cousins: the bare domain, `https://` variants). Any unguarded occurrence is removed before B6.
- `gated-preprod` scenarios are written with their target read from a **documented env var** (e.g. `TEST_TARGET_URL`), defaulting to nothing — the test self-skips when unset. Never read `.claude/full-test.yml` for the URL: the two skills stay uncoupled; `/full-test` sets the env var when it runs the suite.
