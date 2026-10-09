# `.claude/test-coverage.yml` — per-project config

Owned by this skill alone (it never reads another skill's config — `/full-test`'s file included). Lives at `PROJECT_ROOT/.claude/test-coverage.yml`. The inventory itself lives separately in `.claude/test-coverage/inventory.yml` (`inventory-schema.md`).

## Secrets policy (non-negotiable)

Env-var **names** only, never values. `prod_hosts:` holds hostnames — public information whose presence here *prevents* harm. Anything machine-specific (local DB URLs, emulator ports) goes in the `local:` block, kept in a gitignored `.claude/test-coverage.local.yml`.

## Layout

```yaml
# --- committed: structural, shareable ---
version: 1
detected_at: { sha: <HEAD at last detection>, note: "stamp with the git SHA after the run" }

surfaces:                             # refreshed each detection; evidence-backed
  web-frontend: { present: true,  confidence: high, evidence: "frontend/src/app" }
  api:          { present: true,  confidence: high }
  cli:          { present: false, confidence: high }

launch:
  how: "npm run dev"                  # proven by an actual start, never assumed
  url: "http://localhost:3000"
  proven_at_sha: ab12cd3              # last SHA where the start actually succeeded
  dev_accounts: "seeded via npm run seed:dev"   # how the dynamic pass logs in — never prod credentials

runners:                              # mirror of inventory profile.frameworks + idioms writing.md needs
  - name: vitest
    kind: unit
    cmd: "npx vitest run"
    single: "npx vitest run FILE"
    paths: ["src/**/*.test.ts"]
    mutates_state: false
    skip_idiom: "it.skip / it.todo"
  - name: playwright
    kind: e2e
    cmd: "npx playwright test"
    single: "npx playwright test FILE"
    paths: ["e2e/**"]
    mutates_state: true
    skip_idiom: "test.fixme"

prod_hosts:                           # (key name shared with the full-test config) the V8 / build guardrail list — confirmed human, never auto-shrunk
  - "app.exemple.org"
  - "api.exemple.org"

gated_env_var: TEST_TARGET_URL        # how gated-preprod tests receive their target (writing.md §5)

last_audit:
  path: ".claude/test-coverage/audit-2026-08-11-ab12cd3.md"
  sha: ab12cd3
  treated: none                       # none | partial | full — mirrored from the trailer by build B7
  open_findings: 12                   # open + skipped count; 0 <=> treated: full; drives bare routing

accepted_risks:                       # conscious human decisions — never auto-edited, never re-litigated outside audit
  - id: TC-GAP-ADMIN-01
    decision: "do not test the legacy admin panel (removal planned T4 2026)"
    rationale: "end-of-life code; the test effort would be thrown away with it"
    severity: P2                      # original severity, never downgraded
    accepted_at: 2026-08-11
    accepted_by: "owner"
    review_after: 2026-12-01          # optional date that reopens the question

# --- local: machine-specific (gitignore .claude/test-coverage.local.yml) ---
local:
  env_var_names: [DATABASE_URL_TEST]
  emulator: "android-studio AVD pixel-7"

# --- human-authored: never auto-overwritten (drift => show diff and ask) ---
quirks:
  - "the e2e suite requires the seed BEFORE the first test — the build wave order must respect it"
  - "vitest in --no-threads mode on this machine (sqlite lock)"

# --- speed (mode speed) — full schema and field rules in speed.md §7 ---
speed:
  target_minutes: 20                  # human: drives bare routing toward speed when the baseline is slower
  timing_sources: []                  # per runner, existing per-item timing files (format named)
  baseline: { sha: ab12cd3, path: ".claude/test-coverage/speed-baseline-ab12cd3.json", wall_s: {}, collected: {} }
  applied: []                         # close-out only: { id, runner, at_sha, gain_s, files }
  refused: []                         # close-out only: { id, runner, reason, at_sha }
  serial_groups: []                   # human-authored after first write: { runner, mechanism, tests }
  quarantine: []                      # human-confirmed one by one, still executed: { runner, step, since_sha, reason, confirmed_by, confirmed_at, review_after }
  touched_files: []                   # verify V10 scope
  cov_profile: ""                     # the coverage command kept alive when --cov leaves the default profile
```

## Field rules

- **`launch.proven_at_sha`** — launchability is re-proven whenever detection sees the dev script or its dependencies changed since this SHA; a stale proof downgrades the dynamic pass to "attempt, else blind spot".
- **`runners[]`** — machine-refreshed each detection (`cmd` re-proven). A runner that disappears is reported, not silently dropped — its mapped tests become V3 candidates.
- **`prod_hosts:`** — seeded by detection (deploy configs, CORS lists, DNS in docs), then **confirmed by the human once**; afterwards the machine may propose additions (shown, confirmed) but never removals. An empty confirmed list is itself recorded (`prod_hosts: []` + a quirk saying why) so verify V8 can distinguish "none" from "unknown" — unknown is a blind spot.
- **`accepted_risks:`** — written only after an explicit AskUserQuestion confirmation at the moment the point surfaces (audit triage or the build gate). Verify shows covered checks as WAIVED (one quiet footer line); build never re-asks; **only audit re-lists them**, and only a context change or a passed `review_after` reopens the decision.
- **`quirks:`** — human-authored operational truths the machine obeys but never edits.
- **`speed:`** — `target_minutes`, `serial_groups`, `quarantine` are human-authored (drift ⇒ diff + ask); `baseline`, `applied`, `refused`, `touched_files`, `cov_profile` are written by speed's close-out only. A `quarantine` entry is never auto-removed and never turns a step into a skip — verify V9 checks each still names a living test/step. Full rules: `speed.md` §7.

## Freshness / drift

Detection re-runs every invocation; `detected_at.sha` is the timestamp. Structural drift (runner command changed, surface appeared) updates the file with a one-line report. Human-authored drift (`quirks`, `accepted_risks`, confirmed `prod_hosts`, `speed.serial_groups`, `speed.quarantine`, `speed.target_minutes`) always shows the diff and asks. `speed.baseline.sha` older than HEAD on any `runners[].paths` ⇒ speed re-measures before proposing any lever. `last_audit` older than the current HEAD on any domain glob ⇒ build's freshness check (B1) decides between re-audit and mechanical re-verification — never trust a stale gap.
