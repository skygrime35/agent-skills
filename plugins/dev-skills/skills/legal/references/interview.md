# Interview funnel (build mode) + placeholder protocol

Contents: 0 Skip rules · R1 Identity · R2 Activity · R3 Per-document · R4 Wording and risk appetite · 5 Placeholder protocol

AskUserQuestion salvos, **max 4 questions each**, never one-at-a-time dripping. Options concrete and opinionated, "(Recommended)" default, `multiSelect` where choices aren't exclusive. Funnel: general → precise. **Stop when a new question would no longer change what gets written.**

## 0. Skip rules

Resolution order: CLI argument > `.claude/legal.yml` > plugin option (`legal_*`, see SKILL.md) > recommended option. Ask only blocking questions (missing identity facts, legal-regime change). Never ask what is already answered by: a CLI argument, a plugin option, a `confidence: high` config field, a detection probe result, an `accepted_risks:` entry (a recorded decision **is** an answer — do not re-litigate), or an `answered` gap. Pre-fill options from detection (git config, existing pages, Stripe fixtures) so answering is ticking, not typing.

## R1 — Identity & structure

- Q1.1 "Which legal entity publishes the site?" — [Association loi 1901 | SASU/SAS | Sole proprietor / auto-entrepreneur | No entity yet]. "No entity" + B2C selling detected ⇒ warn: selling without an entity is a P0 blocker; the pages will name the natural person as publisher (éditeur).
- Q1.2 "Who is the publication director (directeur de la publication, the legal representative)?" — options pre-filled from existing mentions légales / git config.
- Q1.3 "Which contact details should be published?" — email (pre-filled); phone with the explicit option "Do not publish a phone number — LCEN risk accepted, will be recorded in accepted_risks". Choosing it triggers the accepted-risk confirmation, then is never re-asked.
- Q1.4 "SIRET/SIREN and registered office address?" — pre-filled if found; free text otherwise.

## R2 — Activity qualification (drives the minimal-set rule in doc-templates.md)

- Q2.1 "Do you sell anything to individuals?" — [Recurring subscription | One-off purchase | Donations only | Nothing (free)].
- Q2.2 "Do users publish content visible to others?" — [Yes, public | Yes, private/team | No].
- Q2.3 "Minimum user age?" (default `${user_config.legal_min_age}`) — [18+ | 15+ (French digital age of consent, art. 45 LIL) | <15 (discouraged: double parental consent required) | No accounts].
- Q2.4 "Cookies beyond the strictly necessary (consent-based analytics, ads, reCAPTCHA, embedded YouTube)?" — [No, strictly necessary only (no-banner regime) | Yes | I don't know (the skill will inspect the code)].

## R3 — Per-document specifics (conditional sub-salvos, only for docs the minimal-set rule selected)

**R3-CGV** (if Q2.1 = subscription/purchase):
- "Price and trial period?" — pre-filled from Stripe/plan fixtures.
- "Does the service start immediately after payment?" — [Yes → L221-25 clause, prorata refund (Recommended) | No, after the withdrawal period]. The prorata route is friendlier than the full L221-28 waiver and stays valid for SaaS.
- "Do you have a signed agreement with a consumer mediator (médiateur de la consommation)?" (default `${user_config.legal_mediator_default}`) — [Yes (name + address + website) | No → suggest CM2C (~48 EUR incl. VAT / 3 years, cm2c.net) and set a placeholder meanwhile | In progress]. Announcing an unsigned médiateur is worse than the placeholder (misleading practice).
- "Commitment period?" — [No commitment, monthly, cancellable at any time (Recommended — Chatel inapplicable, only the 3-click cancellation applies) | Fixed-term commitment with renewal → activates the L215-1 Chatel notice].

**R3-JEUX** (if giveaways with real prizes): prizes and their value · frequency (framework rules + one annex per draw?) · minors allowed (⇒ parental authorization at prize delivery, contractual prudence) · territory.

**R3-RGPD**: processors (sous-traitants) — pre-filled from detection (Stripe, host, AI, analytics): confirm/complete · non-standard retention periods? · DPO (default `${user_config.legal_dpo_stance}`) — [None, generic contact (common and lawful for a small structure) | Appointed (name declared to the CNIL)]. Never justify the absence of a DPO by a fictitious threshold.

**R3-COOKIES** (if regime unclear): list detected cookies, ask which are intentional.

## R4 — Wording & risk appetite

- Q4.1 "Tone of the documents?" (default `${user_config.legal_tone}`) — [Reassuring and simple (Recommended — remains legally exact, see wording.md) | Classic/formal].
- Q4.2 (default `${user_config.legal_en_bref}`) "Add \"En bref\" (in brief) boxes at the head of each article?" — [Yes (layered notice, CNIL pattern) (Recommended) | No].
- Q4.3 (default `${user_config.legal_risk_appetite}`) "Policy on measured-risk omissions (e.g. publisher phone number)?" — [Maximum compliance everywhere | Accept measured risks case by case — each confirmed then recorded in accepted_risks].

## 5. Placeholder protocol

An unanswered question **never blocks generation**. Emit all three, atomically:

1. **In the published French doc**: bracketed professional prose in the published language (French for French law) — no TODO-speak, no XXX (some projects have anti-TODO CI). Example (French text published on a French site): « [Médiateur de la consommation : en cours de désignation — les coordonnées seront publiées ici dès la signature de la convention.] » Internal, non-published docs (registre) may use `[À COMPLÉTER — GAP-nn : <quoi>]` instead.
2. **One `gaps:` entry** in `.claude/legal.yml` — id, doc, locus, the placeholder text **verbatim** (V3 greps it), what is needed with its KB basis, severity, date, `status: open`.
3. **In the build report**: the open-gaps list, each with the sentence that it must be resolved before the text is fully opposable.

Re-runs: read the register first. A gap flipped to `answered` (the human now has the value) ⇒ patch exactly that slot, evaluate a version bump per the project's ritual, set `resolved`. A knowingly risky *decision* (as opposed to a missing *value*) goes to `accepted_risks:`, not `gaps:` — gaps are debts to fill, accepted risks are decisions to respect.
