# `inventory.yml` — the feature/scenario inventory contract

Lives at `PROJECT_ROOT/.claude/test-coverage/inventory.yml`, **committed**, written by the main loop alone (never by a subagent). It is the machine source of truth; audit reports are human-readable views over it. Timestamped by git SHA (`generated_at.sha` — scripts have no clock, the SHA is the stamp).

## 1. Layout

```yaml
version: 1
generated_at: { date: 2026-08-11, sha: ab12cd3 }
counters: { feature_seq: 57, scenario_seq: 214 }   # monotonic, never decremented, never reused

profile:
  surfaces: [web-frontend, api, cli]
  launchable: { web: true, how: "npm run dev", dynamic_pass: done }   # false => blind spot
  frameworks:
    - { name: vitest,     kind: unit, cmd: "npx vitest run", single: "npx vitest run FILE", paths: ["src/**/*.test.ts"], mutates_state: false }
    - { name: playwright, kind: e2e,  cmd: "npx playwright test", single: "npx playwright test FILE", paths: ["e2e/**"], mutates_state: true }

domains:                                            # the disjoint partition (detection.md §2)
  - { id: DOM-01, name: auth,    globs: ["src/auth/**", "backend/apps/accounts/**"] }
  - { id: DOM-99, name: misc,    globs: ["<everything unmatched>"] }
  # optional future sharding: add `file: inventory/DOM-01.yml` and move that domain's
  # features/scenarios there; this index file then lists domains only. Activate past ~2000 lines.

features:
  - id: FEAT-012                                    # zero-padded, stable sort
    domain: DOM-01
    name: "Email / password login"
    kind: ui-action        # ui-action | route | endpoint | cli-command | job | webhook | config-flag
    entry_points: ["src/pages/login.tsx:42", "POST /api/auth/login"]
    discovered_by: [static, dynamic]
    status: active         # active | dormant (wired but disabled) | removed (kept one cycle)
    fingerprint:
      anchor: "POST /api/auth/login"                # the most stable handle: route/command/symbol
      symbol: "loginHandler"
      slug: auth-login-email                        # minted once, never recomputed

scenarios:
  - id: SCEN-0087
    feature: FEAT-012
    class: expected-error  # nominal | expected-error | edge | chain
    chain_of: []           # class: chain only — 2-3 SCEN ids sharing state
    description: "unknown email → 'invalid credentials' without revealing whether the account exists"
    expected_outcome: "HTTP 401 + generic message identical to the wrong-password case"
    cost: cheap            # cheap | moderate | costly | gated-preprod
    severity_if_missing: P1                         # set by arbitration, not by explorers
    coverage:
      status: missing      # covered | partial | missing | waived | gated | bug-found
      tests: []            # [{ path, name, kind }] when covered/partial
      mapped_at_sha: null
    waiver: null           # accepted_risks id when status: waived

bugs:                                               # discovered by build-written tests
  - { id: TC-BUG-02, scenario: SCEN-0087, test: "tests/auth/login.spec.ts :: 'rejects unknown email'", state: open, finding: P1 }
    # state: open | fixed-elsewhere (verify saw the skip removed and the test green) | waived
```

## 2. Field rules

- **`counters`** — advance-only. A deleted feature's ID stays dead forever; a new feature takes the next number even if "slots" look free. V2 FAILs if a counter is below the max observed ID.
- **`expected_outcome`** — always an **observable** (status code, exact message, state left behind, exit code), never an intention ("should fail"). It is what the written test asserts; an outcome that cannot be observed is a derivation defect, kicked back in arbitration.
- **`coverage.status`** — the six values are never collapsed: `covered` (≥1 living test asserts the outcome), `partial` (a test touches the feature but not this outcome), `missing` (the gap), `waived` (conscious human decision, `waiver:` points into `accepted_risks`), `gated` (`gated-preprod` cost — written or not, runnable only via `/full-test`), `bug-found` (a written test proved the outcome wrong; `bugs:` holds the record).
- **`severity_if_missing`** — only arbitration (wave 6) writes it; explorer-proposed severities are hints.
- **`bugs`** — appended by build B5; flipped by verify V5 when the annotated skip disappears and the test passes (`fixed-elsewhere`) — the skill itself never fixes.

## 3. ID stability (the matching cascade)

At every audit, features found by exploration are matched against the previous inventory **before** anything is minted:

1. **Anchor match.** `fingerprint.anchor` greps identically (same route, same command, same symbol signature) ⇒ same FEAT id; refresh `entry_points`.
2. **Symbol match.** Anchor dead, but `fingerprint.symbol` found — including via `git log --follow` on a moved file ⇒ same id; refresh anchor + entry_points.
3. **Candidate match.** Same domain + same `kind` + similar `slug`/name ⇒ a **disputed pair** handed to arbitration with both records; the arbiter decides same-id or new-id. Never auto-merged.
4. **Unmatched previous feature** ⇒ `status: removed`, kept **one cycle** with its scenarios (listed as orphans in the report); purged at the next audit if still absent. Its scenarios' history dies with it — which is why step 3 exists.
5. **Re-baseline breaker.** If > ~30 % of previous features fail steps 1-3 (mass refactor, rename storm), **stop and propose an explicit re-baseline** (fresh IDs, old inventory archived as `inventory-<sha>.yml.bak`) instead of silently minting — a half-matched inventory poisons every future diff.

Scenario IDs follow their feature: a scenario re-derives under the same FEAT ⇒ matched by `class` + `expected_outcome` similarity (exact ⇒ same id; disputed ⇒ arbitration; new outcome ⇒ new id).

## 4. Audit report trailer (what build consumes)

Every audit report `audit-<YYYY-MM-DD>-<SHORTSHA>.md` ends with a fenced machine-readable trailer:

```yaml
treated: none                        # none | partial | full — stamped by build B7, never by audit
findings:
  - { id: TC-GAP-AUTH-03, severity: P1, scenarios: [SCEN-0087, SCEN-0091], action: write-tests, status: open }
  - { id: TC-BUG-02,      severity: P1, scenarios: [SCEN-0087], action: report-bug, status: open }
  # action: write-tests | write-gated (written, not run) | report-bug | rebaseline | add-check
  # status: open (audit writes only this) | applied | skipped | obsolete — updated by build B7
```

Same lifecycle as the legal skill's findings (open/applied/skipped, treated); keep both in sync. Rules: build's worklist = `open` + `skipped`; `applied` is never re-proposed; a twice-refused `skipped` finding is offered to `accepted_risks:` (decided once) or dropped to the next audit; `treated: full` routes bare invocations to verify or a fresh audit.
