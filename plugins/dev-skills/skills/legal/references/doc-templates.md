# Document templates — minimal-set rule + document skeletons

Contents: 0 Minimal-set rule · T1 Mentions légales · T2 CGU · T3 CGV · T4 Privacy · T5 Cookies · T6 Jeu-concours règlement · Notes for the drafting agent

Templates are **substrate-agnostic content skeletons**: what a document says, section by section. Instructions are in English; the fenced and quoted blocks, and the French article titles in quotes, are sample output text for a French-language site (French law, the binding version) and stay French. For other audience languages, translate faithfully. Serialization into MDX / i18n JSON keys / markdown is `substrates.md`'s job. `{{SLOT}}` = interview-fillable; `{{#if COND}}` = feature-conditional (the condition is a detected feature or an interview answer, never a guess). Unfilled slot ⇒ placeholder protocol (`interview.md` §5).

## 0. Minimal-set rule

| Feature profile | Required docs — nothing more |
|---|---|
| Landing page, no accounts, strictly-necessary cookies | T1 (cookies handled as a section inside T1 — no separate page) |
| + accounts, free service, UGC | T1, T2, T4, T5-A |
| + B2C subscription / paid offer | + T3 |
| + real-prize giveaways | + T6 |
| + non-essential cookies/trackers | T5-B instead of T5-A + banner/CMP flagged as a code requirement |

**Anti-bloat rule:** never generate a doc this matrix doesn't require; never add a clause whose KB trigger is absent (no international-transfer clause without a non-EU processor; no DPO section without a DPO; no moderation charter without UGC). Every extra document is a standing obligation the éditeur must then honor.

Shared blocks, every doc: header `_Dernière mise à jour : {{DATE}} — version {{VERSION}}_` ("Last updated"); translations open with « Seule la version française fait foi. » ("Only the French version is binding."); footer links to the sibling docs that exist.

## T1 — Mentions légales (complete template, French output)

```markdown
# Mentions légales
_Dernière mise à jour : {{DATE}} — version {{VERSION}}_

## Éditeur du site
Le site {{NOM_SITE}} ({{URL}}) est édité par :
**{{DENOMINATION}}**, {{FORME_JURIDIQUE}}
Siège social : {{ADRESSE_SIEGE}}
SIRET : {{SIRET}}{{#if RNA}} — RNA : {{RNA}}{{/if}}
Email : {{EMAIL_CONTACT}}
{{#if TELEPHONE}}Téléphone : {{TELEPHONE}}{{/if}}   <!-- refused => accepted_risks entry; drop the line, never fake -->
Directeur de la publication : {{DIRECTEUR_PUBLICATION}}
{{#if VENTE_B2C}}TVA : TVA non applicable, art. 293 B du CGI.{{/if}}

## Hébergeur
{{HEBERGEUR_NOM}} — {{HEBERGEUR_ADRESSE}} — {{HEBERGEUR_TELEPHONE}}

{{#if VENTE_B2C}}
## Médiation de la consommation
Conformément aux articles L612-1 et suivants du Code de la consommation, vous pouvez
recourir gratuitement au médiateur de la consommation suivant :
{{MEDIATEUR_NOM}} — {{MEDIATEUR_ADRESSE}} — {{MEDIATEUR_SITE}}
{{/if}}

{{#if UGC}}
## Signaler un contenu
Pour signaler un contenu que vous estimez illicite : {{URL_SIGNALEMENT}}
(règlement (UE) 2022/2065 « DSA », article 16).
{{/if}}

## Propriété intellectuelle
Les contenus de ce site (hors contenus publiés par les utilisateurs) sont la propriété
de {{DENOMINATION}}. Les marques citées appartiennent à leurs titulaires respectifs.
```

Do NOT include: the EU ODR platform (closed 2025-07-20 — remove it where found), a DPO section without a DPO, a CNIL declaration number (regime abolished in 2018).

## T2 — CGU (skeleton)

Sections (French article titles in quotes; content rules in English):
1. « Objet et acceptation » — versioned acceptance, proof of consent.
2. « Compte » — {{AGE_MINIMUM}} years minimum; one account per person; credential security.
3. « Le service » — honest description; availability on a "reasonable efforts" basis, never "guaranteed 100 %".
4. « Règles d'usage » — short list of what is forbidden, readable at 15.
5. {{#if UGC}}« Vos contenus » — non-exclusive license limited to the needs of the service (hosting, display, technical adaptation), for the life of the account; the user warrants holding the rights (including the image rights of filmed persons){{/if}}.
6. {{#if UGC}}« Modération et signalement » — clear policy (DSA art. 14), reporting (art. 16), reasoned decision and redress (art. 17){{/if}}.
7. « Suspension et résiliation » — carve-out for illegal content; otherwise notice + reasons.
8. « Responsabilité » — per wording.md, never a total exclusion.
9. « Évolution des CGU » — notification + re-acceptance if the change is substantial.
10. « Droit applicable, contact, médiation » — mediation only if paid B2C.

## T3 — CGV (skeleton + drafted key articles)

Outline (French article titles in quotes): 1 « Objet » · 2 « Prix » (prices incl. VAT; « TVA non applicable, art. 293 B du CGI ») · 3 « Commande et paiement » (L221-14 order button) · {{#if TRIAL}}4 « Période d'essai » (conversion date and amount announced BEFORE card entry + reminder email){{/if}} · 5 « Durée et renouvellement » · 6 « Résiliation » · 7 « Droit de rétractation » · 8 « Garanties légales » — **mandatory boxed summary** (encadré) of the conformity guarantee for digital services (L224-25-1 s., décret n° 2022-946: reproduce the model box from the regulatory annex) · 9 « Responsabilité » · 10 « Données personnelles » (refer to T4) · 11 « Médiation de la consommation » · 12 « Droit applicable » · Annex: model withdrawal form (annexe à R221-1, 2022 version).

Drafted key articles (French output text):

```markdown
### Article 7 — Droit de rétractation
**En bref : 14 jours pour changer d'avis, remboursement au prorata.**
Vous disposez d'un délai de 14 jours à compter de la souscription pour vous rétracter,
sans motif (art. L221-18 du Code de la consommation). En souscrivant, vous demandez
expressément que le service commence immédiatement. Si vous vous rétractez pendant ces
14 jours, nous vous remboursons le montant payé, déduction faite de la valeur des jours
de service déjà utilisés (art. L221-25). Pour exercer ce droit : un email à
{{EMAIL_CONTACT}} suffit, ou le formulaire en annexe.

### Articles 5-6 — Durée, renouvellement, résiliation
**En bref : sans engagement, résiliable en trois clics.**
L'abonnement est conclu pour {{PERIODE}} et se renouvelle automatiquement. Vous pouvez
le résilier à tout moment depuis votre compte ({{CHEMIN_RESILIATION}}), conformément aux
articles L215-1-1 et D215-1 et suivants du Code de la consommation ; la résiliation
prend effet à la fin de la période en cours, sans frais.
{{#if ENGAGEMENT_DUREE_DETERMINEE}}Avis de reconduction : nous vous rappelons par écrit,
entre 3 mois et 1 mois avant la date limite de non-reconduction, votre faculté de ne pas
reconduire (art. L215-1). À défaut d'avis, vous pouvez résilier sans frais à tout moment
à compter de la reconduction.{{/if}}
<!-- Monthly at-will subscription: L215-1 (Chatel) is inapplicable (no fixed term, no
     tacit renewal in the legal sense); only the 3-click cancellation applies. Do not
     add a Chatel clause the contract shape doesn't trigger. -->

### Article 11 — Médiation de la consommation
En cas de litige non résolu avec notre support ({{EMAIL_CONTACT}}, réponse sous
{{DELAI_SUPPORT}} jours), vous pouvez saisir gratuitement le médiateur de la
consommation dont nous relevons : {{MEDIATEUR_NOM}}, {{MEDIATEUR_ADRESSE}},
{{MEDIATEUR_SITE}} (art. L612-1 et L616-1 du Code de la consommation).
<!-- No ODR-platform mention: closed since 2025-07-20 (Reg. (UE) 2024/3228). -->
```

## T4 — Politique de confidentialité (art. 13/14 map)

Sections (French titles in quotes):
1. « Qui sommes-nous » — controller (responsable de traitement) = `editor:`.
2. « Ce que nous collectons et pourquoi » — **one table: purpose (finalité) × legal basis (base légale) × data × retention (durée)**, generated from the art. 30 register (the register is the source of truth; 2-way sync is audit check RGPD-02 — never freehand).
3. « Destinataires » — the REAL processor list from detection; DPA + transfer basis per non-EU processor.
4. {{#if AI}}« Traitements avec IA » — provider named, consent basis, what is sent, transfer safeguard{{/if}}.
5. « Durées de conservation » — only durations a purge job actually enforces (promising an unenforced duration is a META-1 finding).
6. « Vos droits » — access, rectification, erasure, portability, objection, plus « vous pouvez saisir la CNIL : www.cnil.fr », and how to exercise them ({{EMAIL_CONTACT}}, in-app paths if they exist).
7. « Sécurité » — facts only: measures actually in place.
8. {{#if MINORS}}« Moins de 18 ans » — plain-language paragraph readable at 15{{/if}}.
9. Contact + date/version.

## T5 — Cookies

**T5-A (no-banner regime):** French opening text: « Ce site n'utilise aucun cookie publicitaire ni de traçage. Aucune bannière de consentement n'est donc nécessaire (art. 82 de la loi Informatique et Libertés ; délibération CNIL n° 2020-091). » Then the exhaustive table — name · purpose · duration · type (« essentiel » / « mesure d'audience exemptée ») — of every cookie/storage actually set. The table must match reality (COOK-01); a new non-exempt cookie voids the whole page.

**T5-B (consent regime):** categories (« essentiels » / « mesure d'audience » / « marketing »), per-category cookie table, how to change choices at any time (link reopening the CMP), consent duration (max 13 months for the choice, 25 for measurement), no consent-wall.

## T6 — Giveaway rules (règlement de jeu-concours: framework rules + one annex per draw)

Framework (cadre), French titles in quotes: 1 « Organisateur » ({{DENOMINATION}}, SIRET, registered office) · 2 « Accès au jeu » — **free and no purchase necessary** (« gratuit et sans obligation d'achat »); participation via {{MECANISME}} (free entry is what keeps the draw out of L320-1 CSI — this clause is load-bearing, never conditional) · 3 « Participants » ({{AGE}} years minimum; one entry per person; {{TERRITOIRE}}; {{#if MINORS}}for minors, prize delivery requires the consent of a legal guardian{{/if}}) · 4 « Désignation des gagnants » ({{MODE_TIRAGE}}; date; notification; claim period for the prize then forfeiture: {{DELAI}}) · 5 « Dotation » (annex: list of prizes + unit value incl. VAT; no cash equivalent) · 6 « Données personnelles » (purpose limited to the draw and prize delivery, short retention, refer to T4) · 7 « Modification ou annulation » for cause · 8 « Accessibilité du règlement » ({{URL}}) · 9 « Droit applicable ». Per-draw annex: dates, exact prizes, precise draw method. Note: deposit of the règlement with a commissaire de justice is **optional** since loi n° 2014-1545 (evidentiary measure, not required).

## Notes for the drafting agent

- The trigger for every conditional block is a KB entry; when unsure whether a block applies, that's a question, not a coin-flip.
- After drafting, run the wording pass (red lines + trap list) before the hard gate.
- TVA reference: « art. 293 B du CGI » stays exact until 2026-12-31 — the CIBS recodification was postponed to 2027-01-01 (ordonnance n° 2026-671) and the article renumbered L. 233-3 du CIBS (see KB FISC-1). Do not switch the mention before 2027-01-01.
