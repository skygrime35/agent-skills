---
name: legal
argument-hint: "[audit|build|verify] [--scope=<areas>] [--docs=<list>] [--project=<path>] [--no-web] [--dry-run] [--help]"
description: "Use to set up, update, audit, or repair the LEGAL side of a web project — CGU, CGV, mentions légales, politique de confidentialité, cookies, règlements de jeu-concours — especially when the project takes real payments, opens accounts, hosts user content, or runs giveaways, and the published texts must match what the code actually does. One governed run: detect the legal substrate and the real features, derive the legal MINIMUM they require, analyse against an embedded French/EU knowledge base, interview the human, and write consumer-friendly but legally exact French. Three modes: audit (risk-ranked P0-P3 findings with evidence, writes only its report), build (write or update legal docs through the project's versioning ritual), verify (mechanical consistency checks — version sync, locale parity, placeholders — zero writes). Portable via auto-detection + a .claude/legal.yml config; not a substitute for a lawyer — unknowns become explicit questions or flagged gaps."
---

# /legal

Make a project's legal corpus match what its code actually does — and contain nothing more than its features legally require. The skill audits, builds, and mechanically re-verifies CGU, CGV, mentions légales, privacy/cookie policies, and jeu-concours règlements, in French as the authoritative language, at the wording quality a consumer actually wants to read.

This skill is **portable across any project**. It auto-detects the legal substrate (MDX route groups, i18n JSON keys, plain markdown, or none), the paired version constants, and the legally relevant features on every run, and remembers the non-guessable specifics in a per-project `.claude/legal.yml`.

Its central promise is a negative one: **it never writes a legal statement it cannot source** — from the code, the knowledge base, a dated official web source, or the human. Anything else becomes an explicit placeholder and a registered gap.

## Usage

```
/legal                          # interactive: detect the project, then propose audit, build or verify
/legal audit                    # full legal analysis: code -> applicable law -> P0-P3 findings; writes only its report
/legal build                    # write/update legal docs via the project's versioning ritual (reuses a fresh audit)
/legal verify                   # mechanical consistency checks only — near-free, re-runnable, zero writes
/legal --project=<path>         # target project directory (default: current directory)
/legal --scope=<areas>          # restrict law areas: rgpd,conso,lcen-dsa,structure (default: all applicable)
/legal --docs=<list>            # build only these docs: cgu,cgv,mentions,privacy,cookies,reglement-jeu
/legal --no-web                 # embedded knowledge base only; stale/uncertain points become flagged blind spots
/legal --dry-run                # detect, plan, list what would be asked/researched/written. Zero writes
/legal --help                   # print this Usage block and stop
```

If invoked with `--help`/`-h` and nothing else, print the Usage block above verbatim and stop.

Arguments override questions; anything not passed as an argument is asked interactively. An argument never overrides a **guardrail** — no flag skips the hard gate before touching a published legal text, and `--no-web` never converts an unverified legal point into a confident clause.

## What this skill is for / non-goals

**For:** the minimal legal corpus a real project needs, derived from its detected features, kept mechanically consistent with its code (versions, locales, identity, promises), written in French as the version faisant foi, with consumer-friendly wording that stays legally exact.

**Not for:** legal advice — **this is not a substitute for a lawyer**; every report opens with that disclaimer and the deliverable is a risk-ranked draft with named blind spots, to be reviewed before anything binding. Not for employment contracts, association statutes/PV, fundraising, tax optimization, trademark filings, litigation, or non-French/EU regimes — those emit `ASK-A-PROFESSIONAL` findings naming the right professional, never generated documents. Not for adding legal apparatus the project's features do not require.

## Eight governing principles (these override any convenience)

1. **A wrong clause is worse than a flagged gap.** A published legal text is opposable — to consumers, the CNIL, the DGCCRF. An invented SIRET, médiateur, or retention duration becomes a false statement the éditeur answers for; an explicit `[À COMPLÉTER — GAP-nn]` gets fixed before publication. Unknown ⇒ a question or a registered gap, never plausible filler. Verdicts are **green on what ran** — an unchecked area is a named blind spot, never a pass.
2. **Minimal legal, derived from detected features.** Payments ⇒ CGV; accounts ⇒ CGU + privacy; real-prize giveaways ⇒ règlement de jeu; a bare landing page ⇒ mentions légales and nothing else. Every extra document is a standing obligation the éditeur must then honor — a fictional DPO section is a compliance liability manufactured by zeal.
3. **The code is the oracle for facts; the knowledge base for law; the web only for the gap between them.** Feature claims come from probes of the actual codebase, never from doc prose. Law comes from `references/knowledge-base.md` while its `reviewed_at` is under 6 months; web research is targeted (uncertain, stale, project-specific) and every web claim carries a source URL + date — unfocused legal googling produces confident noise at real cost.
4. **French is the version faisant foi.** All generated legal texts and reports are French; other locales are derived translations regenerated from the frozen French text, never edited independently, each carrying the primacy clause. A corpus where no text is authoritative is exactly the ambiguity a court resolves against the éditeur.
5. **Never degrade an existing legal regime.** A no-cookie-banner design (art. 82 LIL, strictly necessary only), an append-only consent log, an immutable archive are legal decisions the skill works *within*. One "harmless" enabled script (reCAPTCHA) converts a compliant site into a non-compliant one in a single commit — dormant integrations are flagged with their activation consequence, never activated.
6. **Published legal text mutates only behind a hard gate and the project's own versioning ritual.** A silent edit desyncs the consent log from the text users actually accepted. Every write: per-doc diff shown, version bump per the project's documented procedure (read at write time, never from memory), re-consent consequence stated, explicit AskUserQuestion go. `verify` writes nothing, ever.
7. **An accepted risk is decided once, resurfaced only by audit.** When the human knowingly accepts an imperfect position (e.g. no phone in the mentions légales), it is recorded in `accepted_risks:` and never re-litigated by verify, build, or the interview — nagging trains the human to ignore the skill. Only a full audit re-lists accepted risks (dedicated section, original severity kept), and only a context change (accepted in preprod, payments now live) or a passed `review_after` date reopens the question.
8. **Fan out subagents liberally for independent read/analysis/research work; keep all mutating steps single-threaded and gated.** Per-domain analysis, detection probes, and web research parallelize on the least-cost-capable agent (`sonnet-quick` → `sonnet-standard` → `opus-standard` → `opus-deep`). Legal text writing stays in one pair of hands: two agents editing 4-locale parity or paired version constants concurrently produce exactly the desyncs `verify` exists to catch.

## Tooling

External CLIs: `git`, `rg`/`grep`, `jq`, `python3` (JSON key-parity probes), the project's own test runner for guard tests. Claude Code capabilities: **Agent tool** with the machine-local agent types above (detected in Phase 0 under `~/.claude/agents/`; absent ⇒ fall back to the Agent tool's `model` parameter + session effort); **WebSearch/WebFetch** for targeted research (disabled by `--no-web`); **AskUserQuestion** for salvos and hard gates; **TaskCreate/TaskUpdate** for phase tracking and resumability.

## Reference files (load on demand)

| File | When |
|---|---|
| `references/detection.md` | Phase 0 of any mode |
| `references/config-schema.md` | Reading/writing `.claude/legal.yml` (gaps, accepted risks, checks) |
| `references/substrates.md` | Mode verify (the only file it loads); any build write; audit package #1 |
| `references/knowledge-base.md` | Per-area analysis in audit; drafting in build |
| `references/audit-grid.md` | Mode audit — check grid, finding IDs, severity, report template |
| `references/interview.md` | Phase 0 confirmation salvo; build interview |
| `references/wording.md` | Drafting or rewording any user-facing clause |
| `references/doc-templates.md` | Build drafting — minimal-set rule + French skeletons |

---

# Procedure

Follow phases in order. TaskCreate the phases at start; append one line per completed step to `.claude/legal/journal.md` (except in `verify`, which writes nothing). Placeholders are UPPERCASE (`PROJECT_ROOT`, `SUBSTRATE`, `AUDIT_SHA`).

**Mode routing (do this first):**
- `--help` → print the Usage block, stop.
- `verify` → Phase 0 steps 1–3 only (no interview, no config write) → **Mode: verify**. Zero writes anywhere, journal included.
- `--dry-run` → Phase 0 read-only, then print the plan (docs required, questions that would be asked, research points, writes that would happen) and stop.
- `audit` / `build` → Phase 0 → the mode's section.
- bare `/legal` → Phase 0 → propose the sensible mode (no legal corpus ⇒ build; corpus + no fresh audit ⇒ audit; fresh audit with open findings ⇒ build; fresh audit `treated: full` ⇒ verify or a new audit), confirm.

## Phase 0 — Resume, config, detection, profile (all modes)

1. **Resume check.** If `.claude/legal/journal.md` shows an in-progress run, read it and **offer to resume** at the last completed phase rather than blindly restarting.
2. **Load + refresh config.** Read `.claude/legal.yml` (schema: `references/config-schema.md`). **Re-run detection regardless — config goes stale.** On drift between detected and stored values, report it; if the drift touches a human-authored field (`quirks`, `checks` with `origin: human`, `accepted_risks`, interview-answered identity), **show the diff and ask before overwriting**. Secrets policy: env-var **names** only — note that éditeur identity (SIRET, siège, contact) is public legal-notice data and commits freely.
3. **Detection fan-out** (`references/detection.md`) — one `sonnet-quick` per probe family, synthesized by the main loop: substrate + locales; paired version constants and consent/archive machinery; legally relevant features with `confidence` (payments, accounts, UGC, minors, AI, trackers, giveaways) and **dormant integrations** (wired-but-disabled) with their activation consequence; corpus inventory + rot scan (placeholders, prior audits and their finding-ID sequences, binding project conventions, E2E legal invariants).
4. **KB freshness.** Read each area's `reviewed_at` in `references/knowledge-base.md`; older than 6 months ⇒ mark the area "web refresh required" (`--no-web` ⇒ pre-declared blind spot).
5. **Announce + confirm.** One AskUserQuestion salvo (≤4): éditeur identity if unconfirmed, low-confidence feature flags, scope. Skip anything config/args/`accepted_risks` already answer. Write/refresh `.claude/legal.yml` (not in `verify`/`--dry-run`).

## Mode: audit

1. **Required-minimum derivation.** Cross detected features × knowledge-base triggers ⇒ the corpus this project legally needs. Diff against the inventory: each missing document is a finding-in-waiting. One salvo only for feature facts detection couldn't settle that change conclusions (e.g. « les lots des giveaways ont-ils une valeur réelle ? »).
2. **Analysis fan-out** — orchestration table (the cost model; `--scope=` prunes rows 3–6; trivial scope ⇒ a one-package table executed by the main loop):

| # | Work package | Files / area | Agent | Depends on | Wave |
|---|---|---|---|---|---|
| 1 | Mechanical sweep — full verify grid as audit input | substrate map | sonnet-quick | Phase 0 | 1 |
| 2 | Feature evidence — data collected, cookies actually set, payment flows, processors, dormants | backend + frontend | sonnet-standard | Phase 0 | 1 |
| 3 | RGPD / ePrivacy analysis | evidence + KB §RGPD/§COOK | opus-standard | 1, 2 | 2 |
| 4 | Conso — CGV, rétractation, médiateur, renewal, jeux-concours | evidence + KB §CONSO/§JEUX | opus-standard | 1, 2 | 2 |
| 5 | LCEN / DSA — mentions, hébergeur, signalement, modération | evidence + KB §IDENT/§DSA | opus-standard | 1, 2 | 2 |
| 6 | Structure / fiscal — association vs commercial activity | evidence + KB §FISC | opus-standard | 1, 2 | 2 |
| 7 | Web research — one batched package for the uncertain/stale points emitted by 3–6 | web | sonnet-standard | 3–6 | 3 |
| 8 | Risk arbitration — severity, dedupe, kill anything without evidence, write the French report | all findings | opus-deep | 3–7 | 4 |

   Wave-2 agents attach evidence (`file:line` or probe output) to every claim and emit uncertain points as research requests, not conclusions. Wave-3 answers carry source URL + date or degrade to blind spots. Wave 4 is the only `opus-deep` spend — legal risk arbitration is exactly what that tier is for.
3. **Report + registers.** Write `.claude/legal/audit-<YYYY-MM-DD>-<SHORTSHA>.md` in French per `references/audit-grid.md` (findings P0→P3 with Quoi/Où/Pourquoi, **Risques assumés** section from `accepted_risks:`, blind spots, machine-readable trailer for build). Update `gaps:`; propose (gated, diff shown) new `checks:` entries and `knowledge-base.md` refreshes (`reviewed_at` bump + sources — the KB is machine-global, every project benefits). Verdict: « conforme sur le périmètre vérifié ».

## Mode: build

1. **Audit intake.** Load the latest `.claude/legal/audit-*.md`. Fresh = `git diff --name-only AUDIT_SHA..HEAD -- <substrate + feature paths>` is empty ⇒ the `open` + `skipped` findings of its machine-readable trailer become the worklist (`applied` work is never re-proposed; a `treated: full` audit yields an empty worklist — say so and route to interview-driven build or a new audit). Stale/absent ⇒ propose `audit` first (Recommended) or re-verify each consumed finding mechanically before acting — never trust a stale finding.
2. **Interview** (`references/interview.md`). Salvos ≤4, funnel general → precise, skip everything config/detection/`accepted_risks` already answer; stop when a new question would no longer change what gets written. **Every unanswered question ⇒ placeholder + `gaps:` entry** — never a guessed value. A knowingly risky choice ⇒ confirm + record in `accepted_risks:`.
3. **Draft in scratchpad** — nothing touches the repo yet. One `opus-standard` per document (disjoint), per `references/doc-templates.md` + `knowledge-base.md`; then one `opus-deep` pass over the sensitive clauses (rétractation, résiliation, responsabilité, prix, données) per `references/wording.md`.
4. **HARD GATE (before any repo write).** Per doc: rendered French diff vs the published text, version bump plan per the project's own procedure (read it now), re-consent consequence (a CGU bump re-prompts every user — a product event, not a formality), remaining `GAP-nn` placeholders, locales to regenerate, CI interactions. AskUserQuestion: go all / go per-doc / no. Anything other than a clear go ⇒ **stop; nothing is written.**
5. **Write, single-threaded**, per `references/substrates.md`: FR first, locales regenerated from the frozen FR, paired version constants bumped in the same change, archive snapshot when the ritual requires it, project conventions enforced.
6. **Verify + report + audit stamp.** Run the full verify grid + the project's guard tests; fix failures before reporting. **Mark the consumed audit as treated**: update each finding's `status` in its trailer (`applied` / `skipped` / `obsolete`), append a `## Traitement` section (date, HEAD SHA, one line per finding), stamp `treated: partial|full`, and mirror the count into `last_audit.open_findings` — an untreated-looking audit that was already built from re-proposes finished work forever. French report: what was written, versions bumped, gaps still open (each must be resolved before the text is fully opposable), consent-flow implications, follow-ups.

## Mode: verify

Load only `.claude/legal.yml` + `references/substrates.md`. Run the portable grid (V1 version sync, V2 locale parity, V3 placeholder↔gaps bijection, V4 identity coherence, V5 guard tests alive, V6 dates/in-text versions, V7 cross-references, V8 archive immutability) + the config's `checks:`. Main loop or a single `sonnet-quick` — never more. Each check → **PASS / FAIL / WAIVED / BLIND SPOT**, never collapsed: a probe that cannot run is a BLIND SPOT, not a pass; a check covered by `accepted_risks:` is WAIVED, counted in one quiet footer line (« N risques assumés — détail au prochain audit »). Print the table + verdict **green on what ran**. Writes nothing, not even the journal.
