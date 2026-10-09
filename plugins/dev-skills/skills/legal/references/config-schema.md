# `.claude/legal.yml` — per-project config

Contents: Secrets policy · Layout · Field rules · Freshness / drift

Owned by this skill alone (it never reads another skill's config). Lives at `PROJECT_ROOT/.claude/legal.yml`.

## Secrets policy (non-negotiable)

Env-var **names** only, never values. Exception by nature: the `editor:` block holds mentions-légales data (SIRET, registered office (siège), contact email, publication director (directeur de la publication)) — this is information the law requires to be **published on the site itself**, so committing it leaks nothing. Anything not legally public (personal phone numbers not intended for publication, internal doc paths, DPA archives) goes in the `local:` block, kept in a gitignored `.claude/legal.local.yml`.

## Layout

```yaml
# --- committed: structural + public legal-notice data ---
version: 1
detected_at: { sha: <HEAD at last detection>, note: "stamp with the git SHA after the run" }

editor:                              # public legal-notice data; asked once, then confidence: high
  legal_name: "ASSOCIATION EXEMPLE"
  legal_form: association-1901       # association-1901 | sasu | sas | ei | none-yet
  siret: "000 000 000 00000"
  siege: "1 rue Exemple, 35000 Rennes, France"
  directeur_publication: "Prénom Nom"
  contact_email: "contact@exemple.org"
  phone: null                        # null + an accepted_risks entry when knowingly unpublished
  tva: "non applicable, art. 293 B du CGI"
  confidence: high                   # low ⇒ listed in the Phase 0 plan confirmation (blocking only if it changes the corpus)

substrate:
  kind: i18n-json                    # mdx-routes | i18n-json | markdown | none
  authoritative_locale: fr           # the binding version (faisant foi)
  locales: [fr, en, es, de]
  paths: { fr: messages/fr.json }   # mdx: a glob with {loc}; markdown: a dir
  key_prefix: legal                  # i18n-json only
  archive: null                      # e.g. "frontend/src/app/(legal)/archive/"
  versioning_doc: null               # e.g. docs/LEGAL_VERSIONING.md — read at write time

version_refs:                        # every place a doc version is declared; V1's raw input
  - { doc: cgv, ref: "server/billing/subscriptions.py", extract: "CGV_CURRENT_VERSION" }
  - { doc: cgv, ref: "messages/fr.json", extract: "legal.cgv.version" }  # normalized before compare

features:                            # refreshed each detection; evidence-backed
  payments:  { present: true,  confidence: high, evidence: "server/billing" }
  accounts:  { present: true,  confidence: high }
  ugc:       { present: true,  confidence: high }
  minors:    { present: true,  confidence: low }      # low ⇒ listed in the plan confirmation; blocking only if it changes the required corpus
  ai:        { present: false, confidence: high }
  trackers:  { present: false, confidence: high }
  giveaways: { present: true,  confidence: low }
  dormant:
    - name: recaptcha
      evidence: "NEXT_PUBLIC_RECAPTCHA_SITE_KEY wired, unset in prod"
      consequence: "activation => third-party _GRECAPTCHA cookie => consent banner mandatory (breaks the art. 82 LIL no-banner regime)"

law_profile:
  jurisdiction: fr-eu
  b2c: true
  regime_notes: ["free predictions — outside the gambling scope (L320-1 CSI), to be preserved"]

last_audit:
  path: ".claude/legal/audit-2026-08-09-ab12cd3.md"
  sha: ab12cd3
  treated: none                    # none | partial | full — mirrored from the report trailer by build step B6
  open_findings: 7                 # open + skipped count; 0 <=> treated: full; drives bare-/legal routing
  kb_state: { rgpd: 2026-08, conso: 2026-08, lcen-dsa: 2026-08, structure: 2026-08 }
  # snapshot of knowledge-base.md reviewed_at values the audit relied on; build warns
  # when consuming an audit whose kb_state has since gone stale (> 6 months)

checks:                              # project-specific verify checks
  - id: no-cookie-banner
    origin: human                    # human | detected (audit-proposed, human-confirmed)
    probe: "run E2E step step_no_cookie_banner; rg for consent-script markers"
    expect: "no banner, no third-party consent script, dormant integrations still inactive"
    rationale: "art. 82 LIL regime — strictly necessary cookies only"

gaps:                                # placeholder register — machine-maintained
  - id: GAP-01
    doc: cgv
    locus: "messages/fr.json :: legal.cgv.mediation.body"
    placeholder: "Médiateur de la consommation : en cours de désignation — les coordonnées seront publiées ici dès la signature de la convention."
    needed: "signed consumer mediator (médiateur) agreement (L616-1 C. conso): name, postal address, website"
    severity: P1
    since: 2026-08-09
    status: open                     # open | answered | resolved

accepted_risks:                      # conscious human decisions — treated like quirks, never auto-edited
  - id: LCEN-MENTIONS-02
    decision: "do not publish a phone number in the mentions légales"
    rationale: "association without a dedicated line; email answered within 48h"
    severity: P1                     # original severity, never downgraded
    accepted_at: 2026-08-09
    accepted_by: "Jane Doe"
    review_after: null               # optional date that reopens the question

# --- local: machine-specific / non-public (gitignore .claude/legal.local.yml) ---
local:
  private_docs: "private/"           # GDPR register (registre RGPD), DPA PDFs, unpublishable analyses
  env_var_names: [STRIPE_SECRET_KEY]

# --- human-authored: never auto-overwritten (drift => keep stored value, report the diff) ---
quirks:
  - "public site entirely French-speaking — en/es/de are courtesy translations carrying the primacy clause"
  - "anti-TODO CI: published placeholders must be professional prose in the published language, never TODO/XXX"
```

## Field rules

- **`editor:`** — asked once (interview R1; defaults from the `legal_editor_*` plugin options when config and published pages lack a value), then `confidence: high`; drift (a probe finds a different SIRET in the published pages) is a V4 FAIL: the stored value is kept, the diff is reported, and nothing is overwritten in either direction. No question is asked.
- **`version_refs:`** — machine-refreshed each detection. `extract` is a constant name (grep) or a dotted JSON path (jq). In-text version strings are normalized (`"Version 1.0"` → `1.0`) before comparison.
- **`features.*.confidence`** — `low` is listed in the single Phase 0 plan confirmation; it is asked as a blocking question only when it changes which documents are required (the corpus). An answer raises it to `high` and records the answer's date implicitly via `detected_at`.
- **`checks:`** — the audit may **propose** entries (`origin: detected`), presented for confirmation, never added silently. `origin: human` entries are untouchable by the machine.
- **`gaps:`** — the skill appends on unanswered interview questions, flips `status: answered` when the human supplies the value (next build patches exactly that slot and evaluates a version bump), `resolved` once published. `placeholder` holds the published text (French for a French site) **verbatim** — V3 greps for it. Internal (non-published) docs may instead carry `[À COMPLÉTER — GAP-nn : <what>]`; that string then goes in `placeholder`.
- **`accepted_risks:`** — written only after an explicit AskUserQuestion confirmation at the moment the point surfaces (interview, hard gate, or audit triage). Verify shows the covered check as WAIVED (one quiet footer line); build/interview never re-ask; **only audit re-lists them** (dedicated "Accepted risks" section, original severity), and only a context change (e.g. accepted in preprod, payments now live) or a passed `review_after` reopens the decision.

## Freshness / drift

Detection re-runs every invocation; `detected_at.sha` is the timestamp (the git SHA is the stamp). Structural drift (substrate moved, a version_ref path died) updates the file with a one-line report. Human-authored drift (`quirks`, `accepted_risks`, `origin: human` checks, confirmed `editor:` fields) keeps the stored value and reports the diff; it never overwrites and never asks. `last_audit.kb_state` older than 6 months on any area ⇒ build warns that consumed findings may rest on stale law and re-verifies them before acting.
