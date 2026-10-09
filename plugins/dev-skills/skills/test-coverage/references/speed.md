# Speed — mode speed's rules: measurement, lever catalogue, invariants, flakiness, write surface, report, config

The whole mode rests on one sentence: **a lever that cannot be proven to detect exactly the same bugs is not applied.** Every lever below carries its precision invariant and the recipe that verifies it; an agent that cannot run the recipe returns the lever as *unverifiable*, never as *applied*. Nothing here touches a test body, an assertion, or application code — the allowed write surface (§5) is exhaustive and goes verbatim into every agent prompt.

## 1. Measurement first (per runner kind)

Every recipe must yield four things: **wall time**, **collected count**, **per-item durations**, and the **pass / fail / skip id sets** (stable ids: nodeid, full test title, step label). Without id sets there is no invariant (b) and the runner can only be measured, not optimized. Measure the suite **unchanged** — the baseline is the project as it is, including its red tests. A baseline older than HEAD on any `runners[].paths` is stale ⇒ re-measure.

| Runner | Recipe | Notes |
|---|---|---|
| pytest | `pytest -o addopts="" -q -rA --durations=0 --durations-min=0.05 --junitxml=<baseline>.xml` ; count via `pytest --collect-only -q -o addopts="" \| tail -1` | Overriding `addopts` explicitly is the point: run once with the project's `addopts` (e.g. `--cov`) and once without ⇒ the **coverage tax** is measured, not guessed. `--durations` lines give the setup / call / teardown split — a suite dominated by `setup` is fixture-bound (cache purges, DB creation), not test-bound. |
| vitest / jest | `npx vitest run --reporter=json --outputFile=<baseline>.json` (jest: `--json --outputFile`) | `numTotalTests`, per-file and per-test `duration`. Record `pool`, `isolate`, `fileParallelism`, worker count in effect. |
| playwright / cypress | `npx playwright test --reporter=json` ; count via `npx playwright test --list` | Per-test `duration`, `retry` index, `status`. If the target is remote (`baseURL` not localhost), sample the health endpoint's latency every 10 s during the run (`curl -w '%{time_total}'` loop) and keep its p95 — the saturation evidence playwright lever 1 needs. |
| custom harness | The project's own timing file if one exists (declared in `speed.timing_sources`, format named); else an env-gated timing hook around the step runner writing `{label, status, attempts, seconds}` per step | The hook is the **only harness edit allowed before the gate**, and only after the Phase 0 salvo confirms it. Derive: per-step duration, attempts observed, **failure cost = Σ attempts × time-to-fail** (a red step retried to timeout is usually the single biggest line), steps red in ≥ K consecutive history runs (quarantine candidates, K default 3). |
| other | `runners[].cmd` wrapped in `time`, id sets from whatever the runner prints | Per-item timing absent ⇒ named blind spot; the runner is still counted in the before/after table. |

Write the baseline to `.claude/test-coverage/speed-baseline-<SHORTSHA>.json`: `{sha, measured_at, runners: {<name>: {wall_s, collected, passed: [...], failed: [...], skipped: [...], durations: [{id, s, setup_s?, teardown_s?}], top50: [...], notes}}}`. It is a measurement artefact: it exists even when the gate is refused, and the report says so.

## 2. Lever catalogue

Ranked by payoff / risk within each runner. Each entry: **what** · **invariant** (what must stay identical) · **recipe** (how it is verified, always against the baseline id sets) · **rollback**. Estimated gains are stated at the gate as ranges from the baseline numbers, never as promises.

### pytest

1. **Process parallelism** — add `pytest-xdist`, run `-n <cores> --dist loadgroup`; mark every test touching a non-transactional shared resource (cache/Redis, filesystem paths, ports, process-level singletons, external sandboxes) with `@pytest.mark.xdist_group("<resource>")` so they share one worker; give each worker its own cache namespace (a conftest hook setting the cache `KEY_PREFIX` from the xdist worker id — infrastructure, not app code). pytest-django already isolates the DB per worker (`test_<db>_gw<n>`). *Invariant*: collected count and id sets identical; every test found by the shared-state census is grouped or serialized. *Recipe*: `-n 1` then `-n auto`, N runs (§4), junit diff empty. *Rollback*: remove the `-n` from the profile; markers are inert without xdist.
2. **DB reuse** — `--reuse-db` in the default profile, `--create-db` documented as the escape hatch (a `quirks` line + a `Makefile`/script target), and an automatic `--create-db` when `git diff --name-only <speed.baseline.sha>..HEAD -- '**/migrations/**'` is non-empty (a wrapper script or a conftest `pytest_configure` hook). *Invariant*: schema identical to a fresh create — guaranteed by the escape hatch, proven once by running the suite both ways. *Rollback*: drop the flag.
3. **Coverage off by default** — remove `--cov*` from `addopts`; keep a separate **cov profile** (`pytest -c pytest-cov.ini`, or a `test:cov` script) that CI / `/safe-merge` keep calling, recorded in `speed.cov_profile`. *Invariant*: none on detection (coverage is measurement, not detection) — but the cov command must still run and is proven once. *Rollback*: restore `addopts`.
4. **Targeted cache purge** — an autouse fixture that purges a cache before *and* after every test is a per-test round-trip × N. Keep it autouse (its guarantee is what matters) but make it cheap: purge only when the test actually touched the cached tables (a `post_save`/`post_delete` counter installed by the fixture, or an explicit opt-in marker on the modules that mutate them, chosen from the census). `cache.clear()` calls **inside tests are never removed**. *Invariant*: every test that reads the cached tables still starts from a clean cache — proven by the N-run campaign under xdist **with random ordering** (`pytest-randomly` or `-p randomly`); a single order-dependent failure refuses the lever. *Rollback*: restore the unconditional purge.
5. **`transaction=True` / `TransactionTestCase` audit** — list them (truncate-based teardown is the slowest class). Report those that show no need for it as a **finding for the human**; never auto-convert — changing the isolation class can change what a test proves.
6. **Cheap wins** — `-v` out of `addopts` (output cost on thousands of tests), `-p no:cacheprovider` only where the cache dir is unwritable, a fast password hasher in the **test settings** (invariant: `rg` shows no test asserting on the hash algorithm), `--import-mode=importlib` where the layout allows. Each is its own lever with its own recipe.

### vitest / jest

1. **Pool + isolation** — benchmark `pool: 'threads'` vs `'forks'`; `isolate: false` **only** for files the census proves free of module-level mutable state (global mocks reset in `afterEach`, no module singletons), via a second `project` — the default stays `isolate: true`. *Invariant*: same count and id sets across N runs with `--sequence.shuffle`. *Rollback*: drop the project.
2. **Environment per file** — `jsdom` boot is the tax; files with no DOM access get `// @vitest-environment node` (marker line, allowlisted). Chosen per file by census, never blanket. *Invariant*: id sets identical.
3. **`setupFiles` cost** — measure; heavy mocks become lazy imports inside the setup file (infrastructure). *Invariant*: same mocks installed — recipe: N runs.
4. **Misc** — `maxWorkers`/`fileParallelism` sizing to the machine, `css: false`, dependency optimizer tuning. Each measured separately.

### playwright / cypress

1. **Worker cap vs target saturation** — **never raise the worker cap when the target is remote and shared**: a config comment documenting measured saturation is evidence, not an obstacle. A higher worker count is accepted only if the health-endpoint p95 sampled during the run stays ≤ baseline p95 × 1.5 **and** id sets are identical. If `launch.how` can start the app locally, the preferred lever is **running against localhost** with more workers, preprod-only specs staying `gated-preprod`. *Rollback*: previous `workers`.
2. **Project split** — read-only specs (parallel, higher cap) vs state-mutating specs (`fullyParallel: false` or a serial project), from a `mutates_state` census per spec. *Invariant*: id sets identical, N runs.
3. **Retries** — keep the configured `retries` **unless** the same lever adds an equivalent guard: an infrastructure fail-fast (health endpoint down or deployed SHA changed ⇒ abort the run as `invalid` instead of retrying every test 3×) and/or retries restricted to tests tagged as network-dependent. *Invariant*: every functional failure of the baseline still appears as a failure. `retries: 0` alone is never a lever.
4. **Artefacts** — `trace: 'on-first-retry'`, `video: 'retain-on-failure'`, `reuseExistingServer`. No invariant beyond "still produced on failure".
5. **Sharding** — `--shard` across machines only if several exist; splitting a single machine's run into sequential shards gains nothing and is not proposed.

### custom harness (project-owned step runner)

1. **Infra-vs-functional failure classifier** in the runner — timeout, 5xx, connection refused, health-down ⇒ *infrastructure* ⇒ retry within budget; an assertion on content/state ⇒ *functional* ⇒ **fail immediately, no retry** (a deterministic functional failure retried to timeout is the classic 40-minute hole). *Invariant*: the failed-step set is identical or a **superset** of the baseline's (a step that used to pass on attempt 2 may now be recorded as flaky — added precision, reported as such). *Recipe*: replay the last K history runs' failure messages through the classifier and check every `fail` stays `fail`; then a real run diffed against the baseline. *Rollback*: classifier off by env var.
2. **Per-step timeout from history** — `timeout(step) = max(floor, p95(step) × 3)` instead of one global ceiling; exceeding it is an infrastructure timeout, recorded, not retried beyond budget. *Invariant*: no baseline-passing step times out in N runs (else the floor is raised for that step, never the step removed).
3. **Fail-fast on infrastructure** — health probe every M steps; target down or redeployed (SHA changed — the harness's own notion, never `/full-test`'s config) ⇒ the run ends as `invalid` with what ran, instead of spending the remaining hundreds of steps on a dead target. *Invariant*: an `invalid` run is never reported as green.
4. **Step dependency graph ⇒ phase-level parallelism** — analysis agents annotate each step call with `produces:` / `consumes:` (accounts, uploaded objects, comments, settings…) from the step code and the seed; phases with disjoint state **and** their own accounts/pages (the harness's page pool) become `run_parallel` groups in the orchestrator's call structure. Only phases proven disjoint are parallelized; a group that fails the N-run campaign returns to serial. *Invariant*: same step count, same ok/fail set, unchanged order inside a phase.
5. **Quarantine (explicit, human-confirmed, still executed)** — steps red for ≥ K consecutive history runs are proposed **one by one** at the gate; a confirmed entry moves to `speed.quarantine` and the runner executes it **at the end of the run, once, retries 0**, reporting it under its own heading. Never skipped, never deleted; each entry carries `confirmed_by`, `confirmed_at`, `since_sha`, `reason`, `review_after`. A quarantined step that turns green is reported as « prêt à sortir de quarantaine » — the human removes the entry.
6. **Ordering** — longest phases first within a parallel group so the tail is short; known-skipped steps cost nothing and are left alone.

## 3. Hard invariants (after every lever, again at close-out)

Lettered (a)–(e) — SKILL.md and verify V10 cite them by letter (`§3c` = the assertion-diff invariant).

- **(a) Collected count** per runner identical to `speed.baseline.collected` (`--collect-only`, `--list`, `numTotalTests`, harness step count).
- **(b) Id sets** pass / fail / skip identical to the baseline. A `fail` that became `pass` ⇒ the lever is refused, unless the classifier's evidence shows an infrastructure flake — then it is logged as a `TC-FLAKY-nn` finding, never counted as a pass. A `pass` that became `fail` ⇒ the lever is refused (or the test isolated per §4 if the campaign shows order dependency).
- **(c) Zero assertion diff** — `git diff --name-only` since the lever's start ⊆ the allowed write surface (§5); for a test file, only lines matching the marker allowlist may change: `@pytest.mark.xdist_group(...)`, `@pytest.mark.usefixtures(...)` referencing an existing fixture, `test.describe.configure({ mode: 'serial' })`, `// @vitest-environment ...`, `@pytest.mark.<group-marker>` declared in the runner config. Any added `skip` / `xfail` / `fixme` / `todo` / `only` / commented-out test ⇒ FAIL, lever reverted.
- **(d) No skip added** except quarantine entries, which are executed.
- **(e) Prod guardrail** (`writing.md` §5) re-checked before every run.

Verify's V9 / V10 re-check (a), the markers and (c) later, mechanically.

## 4. Flakiness under parallelism

- **Campaign**: N runs of the runner's full suite (N = 3 default; 2 for e2e/harness because of cost — the report says which), with random ordering where supported (`pytest-randomly`, `--sequence.shuffle`).
- **Isolation, not deletion**: green at baseline and red in ≥ 1 campaign run ⇒ put the test/step into the runner's serial mechanism (`xdist_group`, own worker, serial project, serial phase), re-run N. Still red ⇒ a real order-dependency bug in the *test* ⇒ `TC-FLAKY-nn` finding (P2) with the two orders that disagree; it stays isolated, never skipped.
- **Retries are counted**: « 4 tests/steps ont eu besoin d'une seconde tentative » is a report line, because a retry hides a signal. Retry-passes never count as clean passes in the invariant check.

## 5. Allowed write surface (verbatim in every agent prompt)

May write — and only these, each enumerated at the gate:
- **Runner configuration**: `pytest.ini`, `pyproject.toml [tool.pytest.*]`, `setup.cfg [tool:pytest]`, `tox.ini` pytest section, `vitest.config.*`, `jest.config.*`, `playwright.config.*`, `cypress.config.*`; a **new** coverage profile file; `package.json` scripts / `Makefile` targets that only wrap a runner invocation.
- **Test bootstrap**: `conftest.py` (any level), vitest/jest `setupFiles`, playwright `globalSetup`/`globalTeardown`, test settings modules — **fixtures and settings only**; a fixture's guarantee may become cheaper, never weaker (proven by §3).
- **Custom harness — runner / infrastructure modules** (step runner, config, context, page pool, timing, launcher script) and the **orchestrator's call structure** (grouping step calls into parallel groups, wiring classifier / timeouts / quarantine / fail-fast). **Never a step function body, never an assertion inside a step, never the harness's own target guard.**
- **Test files**: marker / decorator / `configure` lines from the §3c allowlist only; zero change to test bodies.
- **Test dependency manifests**: adding `pytest-xdist`, `pytest-randomly` or equivalents to test requirements / `devDependencies` — shown at the gate.
- `.claude/test-coverage.yml` `speed:` block, `.claude/test-coverage/speed-*.{json,md}`, `journal.md`.

Never: application code (anything outside `runners[].paths` and the files above), migrations, CI workflows that deploy or target production, `prod_hosts`, any assertion, any `skip`/`xfail`/`fixme`/`todo`/`only`, any test deletion or rename, a `retries` reduction without its replacing guard in the same lever. A needed change outside this surface is a **returned request** (finding for the human), not an improvisation.

## 6. Report (French) — `.claude/test-coverage/speed-<YYYY-MM-DD>-<SHORTSHA>.md`

```
# Accélération de la suite — <PROJET> — <date> (<SHA>)
Baseline : <path> (<SHA>, mesuré le <date>) · Gate : go all | go partiel (<leviers>) | périmètre réduit par --levers/--runners : <liste>

## Synthèse
| Runner | Avant (wall) | Après (wall) | Gain | Collectés avant → après | ok/fail/skip avant → après |
Total : <avant> → <après> (−<x> %)

## Leviers
| Levier | Runner | Gain mesuré | Invariant vérifié | Fichiers touchés | Statut |
(Statut : appliqué · refusé — <raison + preuve> · non proposé — <raison> · non vérifiable · hors périmètre (--levers))

## Groupes sériels
<test/step> — <mécanisme> — <ressource partagée / preuve de l'isolement>

## Quarantaine
<entrée> — confirmée par <qui> le <date> — exécutée en fin de run : <résultat> — revue après <date>

## Flakiness
Campagne : N = <n> runs (<ordre aléatoire ? >). <k> tests isolés, <m> TC-FLAKY-nn, <r> retries observés.

## Non-régression
Diff des ensembles ok/fail/skip vs baseline : vide | <explication par écart>

## Blind spots
<runner non mesuré / levier non vérifiable / e2e non rejoué N fois / timing par item absent>

## Verdict
« Plus rapide à précision identique sur ce qui a tourné » — <la phrase honnête : ce qui n'a pas tourné, ce qui reste lent et pourquoi>
```

Trailer (machine-readable, same shape as the audit trailer):

```yaml
speed:
  baseline_sha: ab12cd3
  levers:
    - { id: pytest-xdist, runner: pytest, status: applied, gain_s: 2900, files: [backend/pytest.ini, backend/conftest.py] }
    - { id: vitest-isolate-off, runner: vitest, status: refused, reason: "2 fichiers changent de résultat sous shuffle" }
```

Statuses are never collapsed (`reporting.md`); numbers always carry their denominator and delta.

## 7. Config — the `speed:` block of `.claude/test-coverage.yml`

```yaml
speed:
  target_minutes: 20                      # human wish; a slower recorded baseline makes bare routing propose speed
  timing_sources:                         # per runner, where per-item durations already live (format named, never guessed)
    - { runner: e2e-harness, file: "~/e2e-timings/history.json", format: "<project-name>-history-v1" }
  baseline:
    sha: ab12cd3
    path: ".claude/test-coverage/speed-baseline-ab12cd3.json"
    wall_s:    { pytest: 4100, vitest: 900, playwright: 1500, e2e-harness: 7020 }
    collected: { pytest: 6057, vitest: 3623, playwright: 30, e2e-harness: 709 }
  applied:                                # written by close-out only
    - { id: pytest-xdist, runner: pytest, at_sha: cd34ef5, gain_s: 2900, files: [backend/pytest.ini, backend/conftest.py] }
  refused:
    - { id: vitest-isolate-off, runner: vitest, reason: "2 fichiers changent de résultat sous shuffle", at_sha: cd34ef5 }
  serial_groups:                          # human-authored after the first write: drift shows the diff and asks
    - { runner: pytest, mechanism: "xdist_group('redis')", tests: ["apps/billing/tests/test_plan_cache.py"] }
  quarantine:                             # human-confirmed one by one; still executed; never skipped
    - { runner: e2e-harness, step: "Checkout SCA (carte 3DS)", since_sha: ab12cd3, reason: "…", confirmed_by: "Romain", confirmed_at: 2026-08-28, review_after: 2026-10-01 }
  touched_files: [backend/pytest.ini, backend/conftest.py, backend/pytest-cov.ini]   # V10 scope
  cov_profile: "cd backend && pytest -c pytest-cov.ini"                              # the coverage command that still exists, proven once
```

Field rules: `target_minutes`, `serial_groups`, `quarantine` are human-authored ⇒ drift shows the diff and asks (`config-schema.md` § Freshness / drift). `baseline`, `applied`, `refused`, `touched_files`, `cov_profile` are written by close-out only. A quarantine entry is never auto-removed; a quarantined test that turns green is reported, and the human removes it.
