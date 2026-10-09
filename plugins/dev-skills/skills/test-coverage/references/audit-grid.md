# Audit grid — finding taxonomy, severity, report contract

## 0. Output contract

Findings are emitted **in the report language** (`${user_config.test_coverage_report_language}`; the templates below are in English and are translated when the report language differs), canonical block:

```markdown
### [TC-GAP-AUTH-03] "Invalid credentials" error never verified on the login flow
- **Severity**: **HIGH (P1)**
#### What
<one paragraph: the uncovered scenario(s), plainly — what bug would go undetected>
#### Where
<FEAT/SCEN ids + entry_points file:line — the evidence>
#### Why
<what this outcome protects (anti-enumeration, data integrity, CLI contract…) + what silently breaks if it regresses>
#### Remediation
<target test file + framework + effort estimate; or "written as gated-preprod → /full-test">
```

**ID rules.** Stems: `TC-GAP-<DOMAIN>-NN` (uncovered scenarios, grouped — one finding may carry several SCEN ids when they share a cause), `TC-BUG-NN` (a written test proved a wrong outcome), `TC-DRIFT-NN` (inventory vs code vs tests desync: dead mappings, orphan skips, partition holes, unowned referrals), `TC-BASE-NN` (re-baseline events), `TC-FLAKY-NN` (mode speed: a test/step whose result depends on order or parallelism — isolated in a serial group, never skipped; P2). Before minting, read the ID registry of prior audits under `.claude/test-coverage/`: a persisting issue **reuses its ID verbatim** (audits stay diffable); a new one continues the sequence; a used ID is never re-assigned to a different fact.

**Severity ladder.**
- **P0** — a critical path (payment, auth, data loss/corruption, irreversible action) has **zero** tests, nominal included; or a `TC-BUG` on such a path.
- **P1** — an expected error on a main flow is never verified as actually produced (the suite would stay green if the error branch silently died); or a `TC-BUG` off the critical path.
- **P2** — an uncovered edge case, a `partial` coverage (test touches the feature, not the outcome), a mechanical drift (dead mapping, orphan skip).
- **P3** — a `costly` chain left untested, dormant-feature scenarios, quality (a covered scenario whose test asserts less than the `expected_outcome`).

**Evidence rule.** No finding without evidence — FEAT/SCEN ids resolving to real `entry_points`, a probe output, a dynamic-pass trace. wave 6 arbitration (`opus-deep`) kills anything that lacks it, and kills invented scenarios the same way: a scenario whose `expected_outcome` no code path can produce is over-generation, not coverage ambition.

**Accepted risks.** A gap matching an `accepted_risks:` entry (config) is **not** emitted in the P0-P3 list. It appears only in "Accepted risks": ID, decision, date, rationale, original severity — plus a ⚠ re-open line **only if** context changed (the waived feature now sits on a paid flow; `review_after` passed). Outside audit (verify, build, the gate) these are silent (WAIVED).

## 1. What the audit checks (beyond the gaps themselves)

| Q | Verify by | Sev | Stem |
|---|---|---|---|
| Every domain explored, `misc` included, no unowned referral? | fan-out ledger vs partition | P1 | TC-DRIFT |
| Dynamic pass ran on every launchable surface? | P3 probe vs wave 2 ledger | blind spot if not | — |
| Every FEAT has ≥1 nominal + its expected errors derived? | grid completeness sweep | P2 | TC-GAP |
| Existing tests all mapped to a scenario (reverse drift)? | test index vs `coverage.tests` | P2 | TC-DRIFT |
| Existing skips/todos each tied to a `TC-BUG` or waiver? | V4 output as audit input | P2 | TC-DRIFT |
| Previous audit's `applied` findings still true (tests alive + green)? | rg + targeted run | P1 if regressed | reuse original id |
| ID matching clean, re-baseline threshold respected? | matching-cascade ledger | P0 if silently re-minted | TC-BASE |

## 2. Report skeleton

```markdown
# Coverage audit — <PROJECT> — <YYYY-MM-DD> (SHA <SHORTSHA>)
Scope: <domains> · Dynamic pass: <done / blind spot + reason> · Inventory: N features, M scenarios
## Summary            <5-10 lines: counters per coverage status, count per severity, the 3 findings that matter>
## Findings           <P0 → P3, canonical blocks>
## Accepted risks     <from accepted_risks; ⚠ only on context change / review_after>
## Blind spots        <what was NOT explored/derived and what that means — non-launchable surfaces, excluded domains, unresolved referrals>
## Verdict            "Covered on the verified scope" or the honest sentence that fits better
```

Followed by the fenced machine-readable trailer (`inventory-schema.md` §4). The audit emits every finding `status: open`, `treated: none` — it never marks its own work done. Coverage counts in the Summary always give the denominator: "148/214 scenarios covered" — never a bare percentage, which hides both the inventory's size and its growth since last audit.
