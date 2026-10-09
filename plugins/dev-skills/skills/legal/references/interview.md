# Interview funnel (build mode) + placeholder protocol

AskUserQuestion salvos, **max 4 questions each**, never one-at-a-time dripping. Options concrete and opinionated, "(Recommended)" default, `multiSelect` where choices aren't exclusive. Funnel: general → precise. **Stop when a new question would no longer change what gets written.**

## 0. Skip rules

Never ask what is already answered by: a CLI argument, a `confidence: high` config field, a detection probe result, an `accepted_risks:` entry (a recorded decision **is** an answer — do not re-litigate), or an `answered` gap. Pre-fill options from detection (git config, existing pages, Stripe fixtures) so answering is ticking, not typing.

## R1 — Identity & structure

- Q1.1 « Quelle structure juridique édite le site ? » — [Association loi 1901 | SASU/SAS | Entreprise individuelle / auto-entrepreneur | Aucune structure encore]. « Aucune structure » + B2C selling detected ⇒ warn: vendre sans structure est un bloqueur P0 ; les pages nommeront la personne physique comme éditeur.
- Q1.2 « Qui est le directeur de la publication (représentant légal) ? » — options pre-filled from existing mentions légales / git config.
- Q1.3 « Coordonnées à publier ? » — email (pre-filled) ; téléphone with the explicit option « Ne pas publier de téléphone — risque LCEN assumé, sera consigné dans accepted_risks ». Choosing it triggers the accepted-risk confirmation, then never re-asked.
- Q1.4 « SIRET/SIREN et adresse du siège ? » — pre-filled if found; free text otherwise.

## R2 — Activity qualification (drives the minimal-set rule in doc-templates.md)

- Q2.1 « Vendez-vous quelque chose à des particuliers ? » — [Abonnement récurrent | Achat ponctuel | Dons uniquement | Rien (gratuit)].
- Q2.2 « Les utilisateurs publient-ils du contenu visible par d'autres ? » — [Oui, public | Oui, en privé/équipe | Non].
- Q2.3 « Âge minimum des utilisateurs ? » — [18+ | 15+ (majorité numérique française, art. 45 LIL) | <15 (déconseillé : double consentement parental requis) | Pas de comptes].
- Q2.4 « Cookies au-delà du strict nécessaire (analytics avec consentement, pubs, reCAPTCHA, YouTube embarqué) ? » — [Non, strictement nécessaire uniquement (régime sans bandeau) | Oui | Je ne sais pas (le skill inspectera le code)].

## R3 — Per-document specifics (conditional sub-salvos, only for docs the minimal-set rule selected)

**R3-CGV** (if Q2.1 = abonnement/achat):
- « Prix et période d'essai ? » — pre-filled from Stripe/plan fixtures.
- « Le service démarre-t-il immédiatement après paiement ? » — [Oui → clause L221-25, remboursement au prorata (Recommended) | Non, après le délai de rétractation]. The prorata route is friendlier than the full L221-28 waiver and stays valid for SaaS.
- « Avez-vous une convention signée avec un médiateur de la consommation ? » — [Oui (nom + adresse + site) | Non → proposer CM2C (~48 € TTC / 3 ans, cm2c.net) et poser un placeholder en attendant | En cours]. Announcing an unsigned médiateur is worse than the placeholder (pratique trompeuse).
- « Durée d'engagement ? » — [Sans engagement, mensuel résiliable (Recommended — Chatel inapplicable, seule la résiliation en 3 clics s'impose) | Engagement à durée déterminée avec reconduction → active l'avis Chatel L215-1].

**R3-JEUX** (if giveaways real-prize): dotation et valeur des lots · périodicité (règlement-cadre + annexe par tirage ?) · mineurs admis (⇒ autorisation parentale à la remise du lot, prudence contractuelle) · territoire.

**R3-RGPD**: sous-traitants — pre-filled from detection (Stripe, hébergeur, IA, analytics) : confirmer/compléter · durées de conservation dérogatoires ? · DPO — [Aucun, contact générique (fréquent et licite en petite structure) | Désigné (nom déclaré CNIL)]. Never justify absence of DPO by a fictitious threshold.

**R3-COOKIES** (if regime unclear): list detected cookies, ask which are intentional.

## R4 — Wording & risk appetite

- Q4.1 « Ton des documents ? » — [Rassurant et simple (Recommended — reste juridiquement exact, cf. wording.md) | Classique/formel].
- Q4.2 « Encadrés "En bref" en tête d'article ? » — [Oui (layered notice, pattern CNIL) (Recommended) | Non].
- Q4.3 « Politique face aux omissions à risque mesuré (ex. téléphone éditeur) ? » — [Conformité maximale partout | Accepter des risques mesurés au cas par cas — chacun confirmé puis consigné dans accepted_risks].

## 5. Placeholder protocol

An unanswered question **never blocks generation**. Emit all three, atomically:

1. **In the published French doc**: bracketed professional French — no TODO-speak, no XXX (some projects have anti-TODO CI). Example: « [Médiateur de la consommation : en cours de désignation — les coordonnées seront publiées ici dès la signature de la convention.] » Internal, non-published docs (registre) may use `[À COMPLÉTER — GAP-nn : <quoi>]` instead.
2. **One `gaps:` entry** in `.claude/legal.yml` — id, doc, locus, the placeholder text **verbatim** (V3 greps it), what is needed with its KB basis, severity, date, `status: open`.
3. **In the build report**: the open-gaps list, each with the sentence that it must be resolved before the text is fully opposable.

Re-runs: read the register first. A gap flipped to `answered` (the human now has the value) ⇒ patch exactly that slot, evaluate a version bump per the project's ritual, set `resolved`. A knowingly risky *decision* (as opposed to a missing *value*) goes to `accepted_risks:`, not `gaps:` — gaps are debts to fill, accepted risks are decisions to respect.
