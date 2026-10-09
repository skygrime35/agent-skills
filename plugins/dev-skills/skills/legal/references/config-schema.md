# `.claude/legal.yml` — per-project config

Owned by this skill alone (it never reads another skill's config). Lives at `PROJECT_ROOT/.claude/legal.yml`.

## Secrets policy (non-negotiable)

Env-var **names** only, never values. Exception by nature: the `editor:` block holds mentions-légales data (SIRET, siège, contact email, directeur de la publication) — this is information the law requires to be **published on the site itself**, so committing it leaks nothing. Anything not legally public (personal phone numbers not intended for publication, internal doc paths, DPA archives) goes in the `local:` block, kept in a gitignored `.claude/legal.local.yml`.

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
  confidence: high                   # low ⇒ re-confirm with the human each run

substrate:
  kind: i18n-json                    # mdx-routes | i18n-json | markdown | none
  authoritative_locale: fr           # la version faisant foi
  locales: [fr, en, es, de]
  paths: { fr: frontend/messages/fr.json }   # mdx: a glob with {loc}; markdown: a dir
  key_prefix: legal                  # i18n-json only
  archive: null                      # e.g. "frontend/src/app/(legal)/archive/"
  versioning_doc: null               # e.g. AGENTS/LEGAL_VERSIONING.md — read at write time

version_refs:                        # every place a doc version is declared; V1's raw input
  - { doc: cgv, ref: "backend/apps/billing/services/subscriptions.py", extract: "CGV_CURRENT_VERSION" }
  - { doc: cgv, ref: "frontend/messages/fr.json", extract: "legal.cgv.version" }  # normalized before compare

features:                            # refreshed each detection; evidence-backed
  payments:  { present: true,  confidence: high, evidence: "backend/apps/billing" }
  accounts:  { present: true,  confidence: high }
  ugc:       { present: true,  confidence: high }
  minors:    { present: true,  confidence: low }      # low ⇒ confirmation salvo
  ai:        { present: false, confidence: high }
  trackers:  { present: false, confidence: high }
  giveaways: { present: true,  confidence: low }
  dormant:
    - name: recaptcha
      evidence: "NEXT_PUBLIC_RECAPTCHA_SITE_KEY wired, unset in prod"
      consequence: "activation => cookie tiers _GRECAPTCHA => bandeau de consentement obligatoire (rupture du régime art. 82 LIL)"

law_profile:
  jurisdiction: fr-eu
  b2c: true
  regime_notes: ["pronostics gratuits — hors champ jeux d'argent (L320-1 CSI), à préserver"]

last_audit:
  path: ".claude/legal/audit-2026-08-09-ab12cd3.md"
  sha: ab12cd3
  treated: none                    # none | partial | full — mirrored from the report trailer by build B6
  open_findings: 7                 # open + skipped count; 0 <=> treated: full; drives bare-/legal routing
  kb_state: { rgpd: 2026-08, conso: 2026-08, lcen-dsa: 2026-08, structure: 2026-08 }
  # snapshot of knowledge-base.md reviewed_at values the audit relied on; build warns
  # when consuming an audit whose kb_state has since gone stale (> 6 months)

checks:                              # project-specific verify checks
  - id: no-cookie-banner
    origin: human                    # human | detected (audit-proposed, human-confirmed)
    probe: "run E2E step step_no_cookie_banner; rg for consent-script markers"
    expect: "aucun bandeau, aucun script tiers de consentement, dormants toujours inactifs"
    rationale: "régime art. 82 LIL — cookies strictement nécessaires uniquement"

gaps:                                # placeholder register — machine-maintained
  - id: GAP-01
    doc: cgv
    locus: "frontend/messages/fr.json :: legal.cgv.mediation.body"
    placeholder: "Médiateur de la consommation : en cours de désignation — les coordonnées seront publiées ici dès la signature de la convention."
    needed: "médiateur signé (L616-1 C. conso) : nom, adresse postale, site"
    severity: P1
    since: 2026-08-09
    status: open                     # open | answered | resolved

accepted_risks:                      # conscious human decisions — treated like quirks, never auto-edited
  - id: LCEN-MENTIONS-02
    decision: "ne pas publier de numéro de téléphone dans les mentions légales"
    rationale: "association sans ligne dédiée; email répond sous 48h"
    severity: P1                     # original severity, never downgraded
    accepted_at: 2026-08-09
    accepted_by: "Romain"
    review_after: null               # optional date that reopens the question

# --- local: machine-specific / non-public (gitignore .claude/legal.local.yml) ---
local:
  private_docs: "private/"           # registre RGPD, DPA pdfs, analyses non publiables
  env_var_names: [STRIPE_SECRET_KEY]

# --- human-authored: never auto-overwritten (drift => show diff and ask) ---
quirks:
  - "site public entièrement francophone — en/es/de sont des traductions de courtoisie avec clause de primauté"
  - "anti-TODO CI : les placeholders publiés doivent être en français professionnel, jamais TODO/XXX"
```

## Field rules

- **`editor:`** — asked once (interview R1), then `confidence: high`; drift (a probe finds a different SIRET in the published pages) is a V4 FAIL plus a question, never a silent overwrite in either direction.
- **`version_refs:`** — machine-refreshed each detection. `extract` is a constant name (grep) or a dotted JSON path (jq). In-text version strings are normalized (`"Version 1.0"` → `1.0`) before comparison.
- **`features.*.confidence`** — `low` queues the flag for the Phase 0 confirmation salvo; an answered salvo raises it to `high` and records the answer's date implicitly via `detected_at`.
- **`checks:`** — the audit may **propose** entries (`origin: detected`), presented for confirmation, never added silently. `origin: human` entries are untouchable by the machine.
- **`gaps:`** — the skill appends on unanswered interview questions, flips `status: answered` when the human supplies the value (next build patches exactly that slot and evaluates a version bump), `resolved` once published. `placeholder` holds the published French text **verbatim** — V3 greps for it. Internal (non-published) docs may instead carry `[À COMPLÉTER — GAP-nn : <quoi>]`; that string then goes in `placeholder`.
- **`accepted_risks:`** — written only after an explicit AskUserQuestion confirmation at the moment the point surfaces (interview, hard gate, or audit triage). Verify shows the covered check as WAIVED (one quiet footer line); build/interview never re-ask; **only audit re-lists them** (dedicated « Risques assumés » section, original severity), and only a context change (e.g. accepted in preprod, payments now live) or a passed `review_after` reopens the decision.

## Freshness / drift

Detection re-runs every invocation; `detected_at.sha` is the timestamp (scripts have no clock — the git SHA is the stamp). Structural drift (substrate moved, a version_ref path died) updates the file with a one-line report. Human-authored drift (`quirks`, `accepted_risks`, `origin: human` checks, confirmed `editor:` fields) always shows the diff and asks. `last_audit.kb_state` older than 6 months on any area ⇒ build warns that consumed findings may rest on stale law and re-verifies them before acting.
