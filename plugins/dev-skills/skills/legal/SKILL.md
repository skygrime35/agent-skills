---
name: legal
argument-hint: "[audit|build|verify] [--scope=<areas>] [--docs=<list>] [--project=<path>] [--no-web] [--dry-run] [--help]"
description: "Audits, builds and verifies the legal side of a web project (CGU, CGV, mentions légales, privacy and cookie policies, giveaway rules) so the published texts match what the code does and contain only what its features require. French/EU knowledge base, risk-ranked findings. Not a substitute for a lawyer."
when_to_use: "CGU, CGV, mentions légales, politique de confidentialité, RGPD, cookies, jeu-concours, terms of service, privacy policy, legal pages out of sync with the code"
---

# /legal

Plugin options appear in this file as their configured value. In reference files they stay as `user_config.<key>` placeholders: use the value this file shows. If a value still shows as a placeholder here (option never configured), use its `default` in `${CLAUDE_SKILL_DIR}/../../.claude-plugin/plugin.json`.

Makes a web project's legal corpus (CGU, CGV, mentions légales, privacy/cookie policies, giveaway rules) match what its code does and contain nothing its features do not legally require. Auto-detects the substrate (MDX route groups, i18n JSON keys, plain markdown, or none), paired version constants and features on every run; stores non-guessable specifics in `.claude/legal.yml`. Central promise: it never writes a legal statement it cannot source (code, knowledge base, dated official web source, or the human); anything else is a placeholder plus a registered gap.

**Not legal advice: not a substitute for a lawyer.** Every report opens with that disclaimer; the deliverable is a risk-ranked draft with named blind spots. Out of scope (employment contracts, association statutes/PV, fundraising, tax optimization, trademark filings, litigation, non-French/EU regimes): emit `ASK-A-PROFESSIONAL` findings naming the professional, never generated documents.

Findings and reports follow `${user_config.legal_report_language}` (default English); published legal texts follow the project audience's language (French for French law, the binding version).

## Usage

```
/legal                          # detect the project, auto-select the mode, print the choice, run it
/legal audit                    # full legal analysis: code -> applicable law -> P0-P3 findings; writes only its report and its own config/state files (.claude/legal.yml, gaps:)
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

## Eight governing principles (these override any convenience)

1. **A wrong clause is worse than a flagged gap.** Unknown means a question or a registered `[À COMPLÉTER — GAP-nn]` placeholder, never plausible filler; verdicts are "green on what ran", unchecked areas are named blind spots.
2. **Minimal legal, derived from detected features.** Payments need CGV, accounts need CGU + privacy, real-prize giveaways need a règlement, a bare landing page needs mentions légales only.
3. **Code is the oracle for facts, `references/knowledge-base.md` for law, the web only for the gap.** Use the knowledge base while an area's `reviewed_at` is under 6 months; every web claim carries source URL + date.
4. **French is the binding version (faisant foi).** Other locales are translations regenerated from the frozen French text, never edited independently, each carrying the primacy clause.
5. **Never degrade an existing legal regime** (e.g. a no-cookie-banner design, an append-only consent log); dormant integrations are flagged with their activation consequence, never activated.
6. **Published legal text mutates only behind a hard gate and the project's own versioning ritual.** Every write: per-doc diff, version bump per the project's documented procedure (read at write time), re-consent consequence stated, explicit go. `verify` writes nothing.
7. **An accepted risk is decided once** and resurfaced only by audit: see `accepted_risks` in `references/config-schema.md` and the skip rules in `references/interview.md`.
8. **Fan out subagents for independent read/analysis/research; keep all mutating steps single-threaded and gated** (concurrent edits desync locale parity and paired version constants).

## Tooling and agent types

External CLIs: `git`, `rg`/`grep`, `find`, `jq`, `python3` (JSON key-parity probes), the project's test runner for guard tests. Capabilities, with degradation (report any degradation in the run plan):
- **Agent tool**: follow the project's orchestration section if present; otherwise use roles `haiku-quick` (mechanical probes), `haiku-standard` (briefed work, evidence-returning probes, verification), `sonnet-standard` (judgment after briefing), `opus-standard` (real reasoning, sensitive work), `opus-deep` (only after `opus-standard` failed or on explicit user request). A missing type falls back to the Agent tool's `model` parameter.
- **WebSearch/WebFetch** for targeted research; disabled by `--no-web`.
- **AskUserQuestion** for blocking questions and hard gates; absent means plain-text questions with the same options.
- **TaskCreate/TaskUpdate** for phase tracking; absent means a checklist in the build journal.

## Defaults and autonomy

Resolution order for every policy answer: command argument > `.claude/legal.yml` > plugin option > recommended option. Ask only blocking cases: missing editor identity facts, a legal-regime change, a guardrail hit, or a published-text write (hard gate). Plugin options (all optional, empty means unset):

| Option | Used for |
|---|---|
| `${user_config.legal_editor_name}`, `${user_config.legal_editor_form}`, `${user_config.legal_editor_siret}`, `${user_config.legal_editor_address}`, `${user_config.legal_editor_publication_director}`, `${user_config.legal_editor_contact_email}` | `editor:` defaults when config and published pages lack them |
| `${user_config.legal_tone}` (reassuring, neutral, formal) | drafting tone (`references/wording.md`) |
| `${user_config.legal_en_bref}` | "En bref" (in brief) summary boxes at the head of each article |
| `${user_config.legal_risk_appetite}` | whether measured risks may be proposed for `accepted_risks` |
| `${user_config.legal_dpo_stance}` | DPO section default |
| `${user_config.legal_mediator_default}` | consumer mediator (médiateur) default when no convention is known |
| `${user_config.legal_min_age}` | minimum age default |
| `${user_config.legal_report_language}` | language of findings and reports (default `en`) |

An option never fills a fact that would be published unverified: an identity value from options is shown in the hard-gate diff, and an empty one becomes a placeholder + gap.

## Reference files (load on demand)

| File | When |
|---|---|
| `${CLAUDE_SKILL_DIR}/references/detection.md` | Phase 0 of any mode |
| `${CLAUDE_SKILL_DIR}/references/config-schema.md` | Reading/writing `.claude/legal.yml` (gaps, accepted risks, checks) |
| `${CLAUDE_SKILL_DIR}/references/substrates.md` | Mode verify (the only file it loads); any build write; audit work package 1 |
| `${CLAUDE_SKILL_DIR}/references/knowledge-base.md` | Per-area analysis in audit; drafting in build |
| `${CLAUDE_SKILL_DIR}/references/audit-grid.md` | Mode audit: check grid, finding IDs, severity, report template |
| `${CLAUDE_SKILL_DIR}/references/interview.md` | Blocking questions in Phase 0; build interview |
| `${CLAUDE_SKILL_DIR}/references/wording.md` | Drafting or rewording any user-facing clause |
| `${CLAUDE_SKILL_DIR}/references/doc-templates.md` | Build drafting: minimal-set rule + French document skeletons |

---

# Procedure

Follow phases in order. TaskCreate the phases at start. Only `build` keeps a journal: append one line per completed write step to `.claude/legal/journal.md` (resumable writes). `audit`, `verify` and `--dry-run` write no journal. Placeholders are UPPERCASE (`PROJECT_ROOT`, `SUBSTRATE`, `AUDIT_SHA`).

**Mode routing (do this first):**
- `--help` → print the Usage block, stop.
- `verify` → Phase 0 steps 1–3 only (no interview, no config write) → **Mode: verify**. Zero writes anywhere, journal included.
- `--dry-run` (or "tell me what you would do / without writing anything") → Phase 0 read-only, then print the plan and stop. The plan has exactly these sections: **Required documents** (derived from detected features, each with its trigger), **Questions I would ask**, **Research points**, **Planned writes** (paths and versions only, no drafted legal text), **Flagged, not written**. Zero writes: no `.claude/legal.yml`, no journal, no repo file. A fixture the user asked to set up beforehand is theirs, not a skill write.
- `audit` / `build` → Phase 0 → the mode's section.
- **Read-only request** (the user says "do not change anything", "read-only", "don't write", "without writing"): treat as `--dry-run` for every write of the skill itself: no `.claude/legal.yml`, no `.claude/legal/` report, no journal, no scratch file in the repo, and no `git add`/`git commit`/stash of any kind, **including when you build a fixture the user asked for: `git init` and create the files, but never `git add` or commit them** (a repo with no commit has no `AUDIT_SHA`: say `uncommitted`; the answer must never admit a commit, staging or any other write). Still run the full analysis (audit mode) and print the complete report in the chat, with the disclaimer first, and say in one line that nothing was written. Never ask permission to write in that case; just do not write. Fixture rule: build the fixture exactly as described (no extra invented content, no `git add`, no commit, not even to obtain a SHA); in the final answer, put the disclaimer first, then the report, and mention the fixture only in a single last line ("Setup: fixture created as requested, nothing staged or committed, nothing else written."). Never run `git commit` in a read-only request. Before answering, run `git status --short` and `git log --oneline -1` and state their result in the last line, showing that the skill created no commit and changed no file.
- bare `/legal` → Phase 0 → auto-select the mode and print the choice with its reason, without asking (no legal corpus ⇒ build; corpus + no fresh audit ⇒ audit; fresh audit with open findings ⇒ build; fresh audit `treated: full` ⇒ verify).

## Phase 0 — Resume, config, detection, profile (all modes)

1. **Resume check** (build only). If `.claude/legal/journal.md` shows an in-progress run less than 7 days old, resume automatically at the last completed step and say so; an older journal is reported and ignored.
2. **Load + refresh config.** Read `.claude/legal.yml` (schema: `references/config-schema.md`). **Re-run detection regardless — config goes stale.** On drift between detected and stored values, report it; if the drift touches a human-authored field (`quirks`, `checks` with `origin: human`, `accepted_risks`, interview-answered identity), **keep the stored value and report the diff**; never overwrite it silently. Secrets: see `references/config-schema.md`.
3. **Detection fan-out** (`references/detection.md`) — one `haiku-quick` per probe family, synthesized by the main loop: substrate + locales; paired version constants and consent/archive machinery; legally relevant features with `confidence` (payments, accounts, UGC, minors, AI, trackers, giveaways) and **dormant integrations** (wired-but-disabled) with their activation consequence; corpus inventory + rot scan (placeholders, prior audits and their finding-ID sequences, binding project conventions, E2E legal invariants).
4. **KB freshness.** Read each area's `reviewed_at` in `references/knowledge-base.md`; older than 6 months ⇒ mark the area "web refresh required" (`--no-web` ⇒ pre-declared blind spot).
5. **Announce + confirm.** Print the profile. Ask (one salvo, ≤4) only blocking points: publisher (éditeur) identity facts missing from config, options and published pages; a change of legal regime; low-confidence feature flags that change the required corpus. Skip anything args, config, plugin options or `accepted_risks` already answer. Write/refresh `.claude/legal.yml` (not in `verify`/`--dry-run`).

## Mode: audit

A report printed in the chat starts with the disclaimer as the very first line of the final answer (before any summary, setup recap or fixture note), then follows the same template and language as the file version (`${user_config.legal_report_language}`, default English, whatever language the user writes in): disclaimer first, findings P0→P3 each with What/Where (`file:line`)/Why, blind spots, verdict "compliant on the verified scope" or the list of failures. Never invent identity facts (SIRET, address, host) to fill a finding: name them as missing.

1. **Required-minimum derivation.** Cross detected features × knowledge-base triggers ⇒ the corpus this project legally needs. Diff against the inventory: each missing document is a finding-in-waiting. One salvo only for feature facts detection couldn't settle that change conclusions (e.g. "do the giveaway prizes have real value?").
2. **Analysis fan-out** — orchestration table (the cost model; `--scope=` prunes rows 3–6; trivial scope ⇒ a one-package table executed by the main loop):

| # | Work package | Files / area | Agent | Depends on | Wave |
|---|---|---|---|---|---|
| 1 | Mechanical sweep — full verify grid as audit input | substrate map | haiku-standard | Phase 0 | 1 |
| 2 | Feature evidence — data collected, cookies actually set, payment flows, processors, dormants | backend + frontend | sonnet-standard | Phase 0 | 1 |
| 3 | RGPD / ePrivacy analysis | evidence + KB §RGPD/§COOK | opus-standard | 1, 2 | 2 |
| 4 | Consumer law — CGV, withdrawal (rétractation), mediator (médiateur), renewal, giveaways | evidence + KB §CONSO/§JEUX | opus-standard | 1, 2 | 2 |
| 5 | LCEN / DSA — legal notices, hosting, reporting, moderation | evidence + KB §IDENT/§DSA | opus-standard | 1, 2 | 2 |
| 6 | Structure / tax — association vs commercial activity | evidence + KB §FISC | opus-standard | 1, 2 | 2 |
| 7 | Web research — one batched package for the uncertain/stale points emitted by 3–6 | web | sonnet-standard | 3–6 | 3 |
| 8 | Risk arbitration — severity, dedupe, kill anything without evidence, write the report | all findings | opus-standard | 3–7 | 4 |

   Wave-2 agents attach evidence (`file:line` or probe output) to every claim and emit uncertain points as research requests, not conclusions. Wave-3 answers carry source URL + date or degrade to blind spots. Wave 4 runs on `opus-standard`; escalate to `opus-deep` only after a failed arbitration or on explicit user request.
3. **Report + registers.** Write `.claude/legal/audit-<YYYY-MM-DD>-<SHORTSHA>.md` in the report language per `references/audit-grid.md` (findings P0→P3 with What/Where/Why, **Accepted risks** section from `accepted_risks:`, blind spots, machine-readable trailer for build). Update `gaps:`; propose (gated, diff shown) new `checks:` entries and `knowledge-base.md` refreshes (`reviewed_at` bump + sources — the KB is machine-global, every project benefits). Verdict: "compliant on the verified scope".

## Mode: build

**B1. Audit intake.** Load the latest `.claude/legal/audit-*.md`. Fresh = `git diff --name-only AUDIT_SHA..HEAD -- <substrate + feature paths>` is empty ⇒ the `open` + `skipped` findings of its machine-readable trailer become the worklist (`applied` work is never re-proposed; a `treated: full` audit yields an empty worklist — say so and route to interview-driven build or a new audit). Stale/absent ⇒ propose `audit` first (Recommended) or re-verify each consumed finding mechanically before acting — never trust a stale finding.

**B2. Interview** (`references/interview.md`). Resolve answers by the defaults order; ask only blocking questions (salvos ≤4, general → precise) and stop when a new question would no longer change what gets written. **Every unanswered question ⇒ placeholder + `gaps:` entry** — never a guessed value. A knowingly risky choice ⇒ confirm + record in `accepted_risks:`.

**B3. Draft in scratchpad**: nothing touches the repo yet. One `opus-standard` per document (disjoint), per `references/doc-templates.md` + `knowledge-base.md`; then one `opus-standard` pass over the sensitive clauses (rétractation, résiliation, responsabilité, prix, données) per `references/wording.md`; escalate to `opus-deep` only after failure or on explicit request.

**B4. HARD GATE (before any repo write).** An instruction such as "do not ask me to confirm", "just do it" or "no questions" never waives this gate: the gate exists because a published legal text binds users. Reply to such an instruction in one line (the gate stays, the diff is what you confirm), still print the full gate content, and call AskUserQuestion. If no answer can be obtained, end the run at the gate with the repo untouched and the exact wording to reply with ("go"). Do not stage, commit or apply anything before the go (a fixture the user asked for is created but not committed either); do not offer to commit in the same step. The final answer must itself contain the gate content (the French diff or full draft CGV text vs the published text, the version bump plan, the re-consent consequence, the remaining `GAP-nn` placeholders, the exact reply wording) as labelled lines `**Version:** <old> -> <new>` and `**Re-consent:** <who must accept again, or why nobody does>` (never omitted, even when no acceptance is recorded), and end with the question "go all / go per-doc / no"; a pointer to a scratch file is not enough, and the CGV file must remain unchanged. Per doc: rendered diff of the French text vs the published text, version bump plan per the project's own procedure (read it now), re-consent consequence (a CGU bump re-prompts every user — a product event, not a formality), remaining `GAP-nn` placeholders, locales to regenerate, CI interactions. AskUserQuestion: go all / go per-doc / no. Anything other than a clear go ⇒ **stop; nothing is written.**

**B5. Write, single-threaded**, per `references/substrates.md`: FR first, locales regenerated from the frozen FR, paired version constants bumped in the same change, archive snapshot when the ritual requires it, project conventions enforced.

**B6. Verify + report + audit stamp.** Run the full verify grid + the project's guard tests; fix failures before reporting. **Mark the consumed audit as treated**: update each finding's `status` in its trailer (`applied` / `skipped` / `obsolete`), append a `## Treatment` section (date, HEAD SHA, one line per finding), stamp `treated: partial|full`, and mirror the count into `last_audit.open_findings` — an untreated-looking audit that was already built from re-proposes finished work forever. Report (in the report language): what was written, versions bumped, gaps still open (each must be resolved before the text is fully opposable), consent-flow implications, follow-ups.

## Mode: verify

Load only `.claude/legal.yml` + `references/substrates.md`. Run the portable grid (V1 version sync, V2 locale parity, V3 placeholder↔gaps bijection, V4 identity coherence, V5 guard tests alive, V6 dates/in-text versions, V7 cross-references, V8 archive immutability) + the config's `checks:`. Main loop or a single `haiku-standard`, never more. Each check → **PASS / FAIL / WAIVED / BLIND SPOT**, never collapsed: a probe that cannot run is a BLIND SPOT, not a pass; a check covered by `accepted_risks:` is WAIVED, counted in one quiet footer line ("N accepted risks — details at the next audit"). Print the table + verdict **green on what ran**. Writes nothing.
