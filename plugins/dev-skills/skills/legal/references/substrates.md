# Substrates — write rituals + the mechanical verify grid

The file that says *where legal text lives and how to write it* is the same file that says *what must stay true about it*: `verify` loads only this file (plus the config), and `build` cannot break an invariant it never read.

## Write rituals (build step B5 — single-threaded, post-gate only)

### Common rules, all substrates

1. **The project's own versioning doc is the oracle.** If `substrate.versioning_doc` is set (e.g. `docs/LEGAL_VERSIONING.md`), read it **at write time** and follow it verbatim — never a memorized copy; the doc evolves. The ritual below is the default only when a project ships none.
2. **FR first, locales derived.** Edit the authoritative-locale text, freeze it, then regenerate every other locale from the frozen FR — same structure (headings, sections, components/keys), plus the primacy clause (« Seule la version française fait foi. »). Never edit a translation independently.
3. **Paired constants bump together.** Every `version_refs` entry for the touched doc changes in the same commit-sized change — frontend constant, backend constant, in-text version string, last-update date. A partial bump is exactly the V1 failure.
4. **Enforce harvested conventions** (from Phase 0): site language rules, emoji bans, anti-TODO CI (published placeholders are professional French, never TODO/XXX), LOC caps, same-commit domain-doc updates.
5. **Refactors ride separately.** De-hardcoding identity strewn across N files, adding a missing guard test, wiring a parity check — each is proposed as its own gated change, never smuggled into a content edit.

### mdx-routes (route-group MDX shape)

Default ritual: (a) if `substrate.archive` is set and the doc is archivable, snapshot the **current** published version under `archive/vX.Y/<doc>/` first; (b) edit `content.fr.mdx`; (c) regenerate `content.{other}.mdx` from the frozen FR, preserving the MDX component skeleton (`LegalPage`, `LegalSection`, tables); (d) bump the version constants (frontend `company.ts`-style + backend `legal_versions.py`-style) in the same change; (e) run the project's guard tests. Identity values go through constants where the project routes them there; hardcoded occurrences follow rule 5.

### i18n-json (message-catalog shape)

(a) Edit `legal.*` values in the authoritative locale file; (b) mirror the **exact key set** to every other locale file — parity is a check, so it is also a write rule: no missing key, no extra key; (c) bump the in-text version string and the backend constant together; (d) placeholders use professional French compatible with the project's anti-TODO CI; (e) run the key-parity script if the project has one, else the V2 probe.

### markdown / blank regime

`markdown`: edit files in place, keep one file per doc per locale, version + date in a header line. `none` (blank): propose a substrate fitting the stack (Next.js app router ⇒ an `(legal)` MDX route group; server-rendered ⇒ templates; static ⇒ `legal/*.md` + routes), ask, record the choice in `substrate:`, then follow that substrate's ritual. Also propose (separate gated change) the footer links block and, if consent is collected, version constants + a consent-proof note.

## The verify grid

Portable core, parameterized by `substrate:`, `version_refs:`, `editor:`, `gaps:`, `checks:`. Each check → **PASS / FAIL / WAIVED / BLIND SPOT**. A probe that cannot run (missing tool, dead path) is a BLIND SPOT, never a pass. A check whose subject is covered by an `accepted_risks:` entry is WAIVED — silent, counted once in the footer. Verify performs **zero writes**.

| # | Check | Probe | FAIL when |
|---|---|---|---|
| V1 | **Version sync** | extract every `version_refs` entry (rg the constant / jq the key), normalize (`"Version 1.0"` → `1.0`, `v1.2` → `1.2`), group by doc, compare | any two refs for the same doc differ |
| V2 | **Locale parity** | mdx: for each doc dir, a `content.<loc>.mdx` exists per locale and heading counts match FR; i18n-json: `python3` set-diff of `<key_prefix>.*` key paths across locale files | missing file/key, extra key, structural drift vs FR |
| V3 | **Placeholder ↔ gaps bijection** | rg each `gaps[].placeholder` (verbatim) in the corpus; rg the corpus for orphan markers (`À COMPLÉTER`, `A COMPLETER`, `TO COMPLETE`, `POR COMPLETAR`, `AUSZUF`, `TODO`, `XXX`, `lorem`, `en cours de désignation`, `désignation en cours`, `sera publié`, `coming soon`) — real corpora vary the wording, so also read any médiateur/DPO/contact section whose value looks pending | an orphan marker with no `gaps:` entry (unregistered rot), or an `open` gap whose placeholder is gone (stale register) |
| V4 | **Identity coherence** | rg SIRET / legal name / siège / contact email across the corpus; compare to `editor:` | any divergent occurrence (stale identity in one file of many) |
| V5 | **Guard tests alive** | run each guard test from Phase 0 verbosely (`pytest <file> -v`, or the project's runner); a guard must **collect and run** | test SKIPPED, 0 collected, or its watched path dead ⇒ report « guard DEAD », FAIL |
| V6 | **Dates & in-text versions** | rg « dernière mise à jour » + version strings inside doc bodies; compare to constants and to `git log -1 --format=%cs -- <doc files>` | future date; body version ≠ constant; displayed date older than the last substantive commit touching the doc |
| V7 | **Cross-references resolve** | extract inter-doc links/routes from the corpus (+ footer legal links if the footer component is in `substrate` scope); stat the target files/routes | a dead legal link |
| V8 | **Archive immutability** (only if `substrate.archive`) | `git status --porcelain -- <archive>` empty AND `git log --diff-filter=M --oneline -- <archive>` shows no post-creation modification of a snapshot | an archived snapshot was modified after creation |

### Project-specific checks (`checks:`)

Run after V1–V8, one row each, same four states. `origin: human` entries are never edited by the machine; the audit may **propose** `origin: detected` candidates (typically from `features.dormant` — e.g. "reCAPTCHA still inactive") which the human confirms before they join the file.

### Output format

One table (check · state · one-line evidence for FAIL/BLIND SPOT), then:

```
Verdict : green on what ran — N PASS, N FAIL, N BLIND SPOT.
N accepted risks (WAIVED) — details at the next audit.
```

FAIL lines cite the exact values compared (e.g. "CGV: backend `CGV_CURRENT_VERSION` = 1.1 ≠ frontend `legal.cgv.version` = 1.0"). Never collapse a BLIND SPOT into a pass; name what the blind spot *means* ("V5 cannot run: pytest absent — the guards were not proven alive").
