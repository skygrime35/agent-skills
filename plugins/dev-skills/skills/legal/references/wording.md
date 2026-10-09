# Wording — legally exact, non-scary French

Load before drafting or rewording any user-facing clause. The point: a clause can be simultaneously valid, honest, and non-frightening. « Abonnement avec obligation d'achat » is legally sound and commercially self-harming; the rewrite keeps the legal effect and drops the fear.

## 1. Doctrine (three rules, in order)

1. **Exact beats reassuring.** A rewrite that changes the legal effect is forbidden, however friendly. Reassuring ≠ hiding obligations.
2. **Say what IS done, not what isn't forbidden.** « Nous ne vendons jamais vos données » (if literally true) + the actual recipient list beats « vos données pourront être transmises à des tiers ».
3. **Never soften an obligation into ambiguity.** Mandated phrases and mandatory items survive verbatim (see red lines); the softening happens *around* them — context, summaries, tone — never *inside* them.

## 2. Rewrite table (scary → reassuring, each with its validity condition)

| Scary / legalese | Reassuring rewrite (FR) | Valid ONLY if |
|---|---|---|
| « Abonnement avec obligation d'achat, reconduction tacite » | « Votre abonnement se renouvelle automatiquement chaque mois. Vous pouvez l'arrêter à tout moment, en trois clics depuis votre compte : vous gardez l'accès jusqu'à la fin de la période déjà payée. » | no commitment period AND the 3-click path really exists (META-1) |
| « Vous renoncez à votre droit de rétractation » | « Vous disposez de 14 jours pour changer d'avis. Si vous choisissez de commencer tout de suite, vous pouvez toujours vous rétracter pendant ces 14 jours : nous vous remboursons alors au prorata des jours non utilisés (art. L221-25 du Code de la consommation). » | the prorata route is used and the refund path exists in code. The FULL waiver framing (L221-28) is only for one-shot digital content, and must then keep the express double acknowledgment |
| « L'éditeur décline toute responsabilité » | « Nous mettons tout en œuvre pour un service fiable. Notre responsabilité ne peut être engagée qu'en cas de faute prouvée de notre part, et dans les limites prévues par la loi. » | never exclude faute lourde/dol or bodily harm; blanket exclusions vs consumers are clauses abusives « noires » (R212-1) — unenforceable AND a finding |
| « Vos données pourront être transmises à des tiers » | « Nous ne vendons jamais vos données. Elles sont partagées uniquement avec les prestataires indispensables au service ({{LISTE_RÉELLE}} : paiement, hébergement…), chacun contractuellement tenu de les protéger. » | literally true; the list comes from the art. 30 register, not from imagination |
| « Le compte pourra être supprimé sans préavis » | « Nous pouvons suspendre un compte en cas de manquement grave aux présentes CGU. Sauf urgence, nous vous prévenons d'abord et vous expliquons notre décision (art. 17 du règlement DSA). » | keep an immediate-suspension carve-out for illegal content; actually send the art. 17 statement |
| « Le présent contrat est régi par le droit français, tout litige relevant des tribunaux compétents » | « Ces conditions sont soumises au droit français. En cas de désaccord, écrivez-nous d'abord ({{EMAIL}}) — la plupart des problèmes se règlent en un échange. Vous pouvez aussi saisir gratuitement notre médiateur de la consommation, puis les tribunaux si nécessaire. » | the médiateur is real and signed; never imply mediation is mandatory before courts |
| « L'essai gratuit se transforme automatiquement en abonnement payant » | « Essai gratuit de {{N}} jours. Le {{DATE_EXACTE}}, votre abonnement démarre à {{PRIX}} €/mois — nous vous le rappelons par email avant, et vous pouvez annuler à tout moment pendant l'essai, en trois clics. » | the reminder email exists and cancellation during trial truly costs nothing |

## 3. Red lines — never softened, never dropped, verbatim or near-verbatim

- Order button: « commande avec obligation de paiement » (L221-14 — courts judge the button text alone).
- The model withdrawal form (annexe à R221-1, version 2022) reproduced or downloadable.
- The legal-conformity guarantee **encadré** for digital services (décret 2022-946) — the boxed summary is mandatory, exact wording per the annex.
- Médiateur: real name + postal address + website (L616-1). No euphemism, no unsigned announcement.
- Prices TTC; while the franchise holds: « TVA non applicable, art. 293 B du CGI » (exact until 2026-12-31; from 2027-01-01 the reference becomes art. L. 233-3 du CIBS — recodification postponed by ordonnance n° 2026-671, see KB FISC-1).
- Pre-contractual L221-5 items (characteristics, price, duration, withdrawal) — an « En bref » box may ADD, never replace.
- RGPD rights list including the right to complain to the CNIL, with URL.
- Primacy clause in every translation: « Seule la version française fait foi. »
- Never claim a certification, approval, or guarantee that doesn't exist.

## 4. Plain-language rules (layered notice, CNIL-endorsed)

Sentences ≤ 25 words. « Vous »/« nous », active voice. One idea per paragraph. Every CGU/CGV/privacy article opens with an « **En bref :** » box of ≤ 2 lines, followed by the full clause. Numbers in digits, dates in full. No Latin, no « nonobstant ». Define each acronym once. Reading target: a 15-year-old understands the CGU (ties to art. 45 LIL and DSA art. 14(3) when minors are served).

## 5. Trap list — phrasings that are themselves illegal (reject at generation time)

- Pre-ticked boxes implying consent or adding paid options (L121-17 C. conso; CJUE *Planet49* for cookie consent).
- « En continuant votre navigation, vous acceptez les cookies » (invalid consent — CNIL délib. 2020-091).
- A cancel path harder than the subscribe path (violates L215-1-1/D215-1 s.; flagged dark pattern).
- « Vos données sont 100 % sécurisées » (unverifiable absolute ⇒ misleading practice).
- Hiding the trial-to-paid conversion date or amount before card entry.
- Mentioning the EU ODR platform (`ec.europa.eu/consumers/odr`) — **closed 2025-07-20** (Reg. (UE) 2024/3228); a dead mandatory-looking link is itself a non-conformity. Remove it wherever found; only the national médiateur mention (L616-1) remains.
- Gambling-flavored vocabulary (« misez », « jackpot », « gagnez de l'argent ») on a free prediction/points product — it undermines the out-of-gambling-scope qualification the product depends on.
