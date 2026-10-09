# Audit grid — checks, finding taxonomy, report contract

Contents: 0 Output contract · 1-9 Domain grids (IDENT, CONSO, RGPD, COOK, DSA, IP, FISC, JEUX) · 10 META cross-cutting checks · 11 Report skeleton

## 0. Output contract

Findings are emitted **in French**, in the project's existing audit style when one exists (harvested in Phase 0), else this canonical block:

```markdown
### [CONSO-MED-01] Médiateur de la consommation publié sans convention d'adhésion active
- **Criticité** : **HAUTE (P1)**
#### Quoi
<one paragraph: the fact, plainly>
#### Où
<file:line paths, URLs, DB tables — the evidence>
#### Pourquoi
<legal basis from knowledge-base entry + concrete sanction/risk>
#### Remédiation
<the minimal fix + effort estimate>
```

**ID rules.** Format `DOMAIN-TOPIC-NN`. Before minting, search the project's harvested ID registry (prior audits, legal docs): a persisting issue **reuses its existing ID verbatim** (audits become diffable across time); a new issue **continues the sequence**, never re-assigns a used ID to a different fact.

**Severity ladder.** P0 = active legal exposure (obligation missing while paid production runs — e.g. registre placeholders with Stripe live). P1 = obligation missing, latent exposure with a named sanction (no règlement de jeu; médiateur announced but unsigned at payment opening). P2 = formal non-compliance / mechanical incoherence (version desync, locale parity, placeholder unregistered, doc silent on an actual processing). P3 = preventive / quality / wording (a dormant reCAPTCHA one flag from breaking the cookie regime ships as P3 + a proposed `checks:` entry + a quirk line).

**Evidence rule.** No finding without evidence — a `file:line`, a probe output, or a dated official source. Wave-4 arbitration kills anything that lacks it.

**Accepted risks.** A finding matching an `accepted_risks:` entry is **not** emitted in the main P0–P3 list. It appears only in the dedicated « Risques assumés » section: ID, decision, date, rationale, original severity — plus a ⚠ re-open line **only if** context changed since acceptance (preprod → paid prod; feature scope grew; `review_after` passed). Everywhere outside audit (verify, build, interview) these are silent (WAIVED).

**Disclaimer.** Every report opens with: « Ce document est une analyse générée par un outil d'assistance. Il ne constitue pas un conseil juridique et doit être relu par un professionnel du droit avant toute décision engageante. » Published customer-facing pages never carry this disclaimer.

**ASK-A-PROFESSIONAL findings** name the professional (avocat en droit de la consommation, conseil en propriété industrielle, expert-comptable associatif) and the precise question to bring — never a generated answer.

## 1–9. Domain grids

Each row: verifiable question · how to verify · KB entry · default severity · ID stem. Verify-grid results (audit work package 1) feed SYNC-* findings directly.

### IDENT — mentions légales
| Q | Verify by | KB | Sev | Stem |
|---|---|---|---|---|
| Page exists, linked from every page footer? | rg footer component; route exists | IDENT-1 | P0 | LCEN-MENTIONS |
| Contains dénomination, forme, siège, SIRET, contact, directeur de la publication, hébergeur (name+address+phone)? | field-by-field read of the published page | IDENT-1 | P1/field | LCEN-MENTIONS |
| Publisher phone present (or consciously waived)? | read + `accepted_risks` | IDENT-1 | P1 | LCEN-MENTIONS |
| B2C: TVA mention + médiateur identity present? | read | IDENT-2, CONSO-6 | P1 | LCEN-MENTIONS |

### CONSO — CGV & selling mechanics
| Q | Verify by | KB | Sev | Stem |
|---|---|---|---|---|
| CGV exist for every paid offer, accepted at checkout (unticked box, logged)? | checkout flow code + consent tables | CONSO-1 | P0 | CONSO-CGV |
| Withdrawal clause: 14 j, how to exercise, model form, immediate-start mechanics (prorata L221-25 or waiver L221-28)? | CGV read + refund path in code | CONSO-2 | P0/P1 | CONSO-RETRACT |
| Order button = « commande avec obligation de paiement » (all locales)? | rg checkout component + i18n keys | CONSO-3 | P1 | CONSO-BTN |
| Cancellation ≤3 clicks from account, CGV clause matches the real flow? | trace the cancel route; E2E if present | CONSO-4 | P1 | CONSO-RESIL |
| Commitment period ⇒ Chatel notice implemented? | billing code + email templates | CONSO-4 | P1 | CONSO-CHATEL |
| Médiateur named AND convention actually signed (ask — never assume from the published text)? | read + ASK | CONSO-6 | P1 | CONSO-MED |
| Prices TTC, trial→paid conversion (date, amount) disclosed before card entry? | pricing page + checkout | CONSO-5, FISC-1 | P1 | CONSO-PRIX |

### RGPD — data protection
| Q | Verify by | KB | Sev | Stem |
|---|---|---|---|---|
| Privacy policy covers every art. 13/14 item; every ACTUAL processing named (AI included)? | policy read × evidence from work package 2 | RGPD-1 | P1 | RGPD-INFO |
| Registre art. 30 exists, matches the policy 2-way, no placeholders? | registre read × policy diff | RGPD-2 | P0 if paid prod | RGPD-REGISTRE |
| Every third-party processor has a DPA + transfer basis recorded? | registre × detected processors | RGPD-1 | P2 | RGPD-SOUSTRAIT |
| Rights implemented: export (art. 20), deletion (art. 17) with real purge/anonymization, and the docs promise only what runs? | code: routes, crons, tasks | RGPD-6 | P1 | RGPD-DROITS |
| Retention durations declared AND enforced by a purge job each? | policy × cron/task inventory | RGPD-6 | P1 | RGPD-CONSERV |
| Minors: age floor enforced at signup, matches the CGU claim, wording readable at 15? | signup code + CGU | RGPD-5 | P1 | RGPD-MINEURS |
| AIPD done or screening documented when 2+ EDPB criteria met (minors, AI, video of people)? | ask + docs | RGPD-3 | P1 | RGPD-AIPD |
| Consent proof: versioned, timestamped, append-only? | models/tables | RGPD-4 | P2 | RGPD-PREUVE |

### COOK — cookies & trackers
| Q | Verify by | KB | Sev | Stem |
|---|---|---|---|---|
| Enumerate cookies/storage actually set on first uncontested visit — every one exempt, or a compliant banner shown? | code probe / headless run × cookies page | COOK-1/2 | P1 | COOK-REGIME |
| Cookie info page lists each cookie, purpose, duration — and matches reality? | page read × enumeration | COOK-1 | P2 | COOK-INFO |
| Dormant trackers one flag from breaking the regime — guarded by a test/check? | `features.dormant` × `checks:` | COOK-1 | P3 | COOK-LATENT |

### DSA — UGC & moderation
| Q | Verify by | KB | Sev | Stem |
|---|---|---|---|---|
| Electronic notice mechanism capturing art. 16 fields, reachable without an account? | report form/route fields | DSA-1 | P1 | DSA-HEBERGEUR |
| Statement of reasons (art. 17) sent on moderation decisions, as the CGU promise? | moderation code + templates | DSA-1 | P2 | DSA-MOTIV |
| T&C describe moderation policy in clear language (art. 14), child-appropriate if minors? | CGU read | DSA-1 | P2 | DSA-CGU |
| Contact points published (authorities + users)? | mentions/CGU read | DSA-1 | P2 | DSA-CONTACT |

### IP — marks & content rights
| Q | Verify by | KB | Sev | Stem |
|---|---|---|---|---|
| Product name cleared against INPI; known conflicts tracked with a decision? | ask + docs; INPI web check if never done | IP-1 | P2 | IP-MARQUE |
| UGC license clause: non-exclusive, purpose-bound, duration-bound; uploader warrants third-party rights (image rights)? | CGU read | IP-2 | P2 | IP-UGC |

### FISC — structure & tax mentions
| Q | Verify by | KB | Sev | Stem |
|---|---|---|---|---|
| Invoices/CGV carry the exact franchise mention, no TVA line anywhere? | invoice templates / Stripe tax config | FISC-1 | P1 | FISCAL-ASSO |
| Association: commercial revenue vs non-lucrativité status reviewed (threshold watch)? | ask + revenue estimate | FISC-1 | ASK-A-PROFESSIONAL | FISCAL-ASSO |

### JEUX — prize draws
| Q | Verify by | KB | Sev | Stem |
|---|---|---|---|---|
| Each real-prize giveaway has a règlement (published or linked at announcement)? | corpus + ask + draw code | JEUX-1 | P1 | JEUX-REGL |
| Free entry preserved (no payment required to win) — gambling boundary intact? | draw eligibility code | JEUX-1/2 | P0 | JEUX-FRONTIERE |
| Minors can win ⇒ parental authorization for prize delivery handled? | règlement + flow | JEUX-1 | P2 | JEUX-MINEURS |

## 10. META — cross-cutting checks (the differentiator)

- **META-1 Promises vs implementation.** Extract every operational commitment from the published French docs (« en 3 clics », « sous X jours », « supprimé après N », « remboursé au prorata », « vous pouvez exporter », « décision motivée ») → find the code counterpart (route, cron, task, guard test). Promise without code = **P1** (pratique commerciale trompeuse); code without promise = P3 (document it).
- **META-2 Placeholder scan.** V3 output, escalated: an unregistered placeholder in a LIVE paid product = P1; in preprod = P2 + register entry.
- **META-3 Version/date coherence.** V1 + V6 output as findings (`SYNC-VERSION-*`, `SYNC-DATE-*`).
- **META-4 i18n parity + primacy.** V2 output (`SYNC-I18N-*`) + every translation carries « Seule la version française fait foi » = P2 if missing.
- **META-5 KB staleness.** Any finding resting on a KB entry with `volatility: moving` or `reviewed_at` > 6 months ⇒ web-refresh before emitting as certain, else tag « à re-vérifier » (blind spot, not a conclusion).

## 11. Report skeleton

```markdown
# Audit légal — <PROJET> — <YYYY-MM-DD> (SHA <SHORTSHA>)
<disclaimer>
Périmètre : <scope> · KB : <area: reviewed_at…> · Blind spots : N
## Synthèse            <5-10 lines, counts per severity, the 3 findings that matter>
## Findings            <P0 → P3, canonical blocks>
## Risques assumés     <from accepted_risks; ⚠ only on context change / review_after>
## Blind spots         <what was NOT verified and what that means>
## Gaps ouverts        <from gaps:, each with what unblocks it>
## Verdict             « Conforme sur le périmètre vérifié » ou la phrase honnête qui s'impose
```

Trailer, fenced, machine-readable (build step B1 parses it, build step B6 updates it):

```yaml
treated: none                      # none | partial | full — stamped by build, never by audit
findings:
  - { id: JEUX-REGL-01, severity: P1, docs: [reglement-jeu], action: create, status: open }
  - { id: SYNC-VERSION-01, severity: P2, docs: [cgv], action: fix-constant, status: open }
  # action: create | amend | fix-constant | fix-code | register-gap | add-check | ask-professional
  # status: open (audit writes only this) | applied | skipped | obsolete — updated by build step B6
```

**Finding lifecycle.** The audit emits every finding `status: open` and `treated: none` — it never marks its own work done. After a build consumes the audit, build step B6 writes the outcome back: per finding, `applied` (fix shipped), `skipped` (human said no at the hard gate — stays actionable next time), or `obsolete` (re-verification showed the issue no longer exists); plus a human-readable `## Traitement` section appended to the report (build date, HEAD SHA, one line per finding) and the `treated:` stamp (`partial` if any `open`/`skipped` remains, `full` otherwise). A later build's worklist = `open` + `skipped` findings only — `applied` work is never re-proposed; a `skipped` finding is re-proposed once, and if refused again the human is offered to move it to `accepted_risks:` (decided once) or drop it to the next audit. A `full`-treated audit stops routing to build: the next sensible step is `verify` or a fresh audit.
