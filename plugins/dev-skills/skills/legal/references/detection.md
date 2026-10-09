# Detection probes (Phase 0, all modes)

Each probe yields either a **verified fact** (with the evidence path/output that proves it) or an **explicit unknown** recorded as such. A probe result never becomes a plausible-sounding sentence. Run probe families as parallel `sonnet-quick` agents; the main loop synthesizes.

Placeholders: `PROJECT_ROOT` = `--project` or cwd. All probes are read-only.

## 1. Substrate — where does legal text live?

Try in order; multiple hits are possible (record all, mark the primary):

```
# MDX route groups (Next.js app router — DebriefLab shape)
fd -g 'content.*.mdx' PROJECT_ROOT --full-path -p | grep -iE '\(legal\)|mentions|cgu|cgv'
# i18n JSON keys (next-intl — evabet shape)
for f in PROJECT_ROOT/frontend/messages/*.json; do jq -r 'paths(..; type=="object") | join(".")' "$f" 2>/dev/null | grep -m1 '^legal$' && echo "HIT $f"; done
# plain markdown / templated HTML
rg -li 'mentions légales|conditions générales' PROJECT_ROOT --glob '*.{md,mdx,html,vue,svelte}' -g '!node_modules'
```

Record: `substrate.kind` (`mdx-routes` | `i18n-json` | `markdown` | `none`), `substrate.paths` (per locale or glob), `substrate.key_prefix` (i18n only), `substrate.locales` + `substrate.authoritative_locale` (from i18n config, `next-intl` setup, or an explicit primacy clause in the texts), `substrate.archive` (an `archive/` dir with version snapshots), `substrate.versioning_doc` (grep `AGENTS/ DOCS/` for a legal-versioning procedure file). `none` ⇒ blank regime: build will propose a substrate fitting the stack and ask.

## 2. Version constants + consent machinery

```
rg -n 'LEGAL_VERSION|CGV_CURRENT_VERSION|CGU_VERSION|LEGAL_VERSIONS|legal_version' PROJECT_ROOT/backend PROJECT_ROOT/frontend -g '!node_modules' -g '!*.lock'
rg -ln 'ConsentLog|consent_log|cgu_accepted_at|cgv_accepted_at|accepted_at.*version' PROJECT_ROOT/backend
rg -n '"version"|lastUpdate|derniere_mise_a_jour|Dernière mise à jour' <substrate files> | head -20
```

Record: every `version_refs` entry — `{doc, ref: file, extract: constant-or-key}` — including the **in-text** version strings inside the published docs themselves. Paired constants (frontend + backend for the same doc) are the highest-value entries: they are V1's raw input. Also record consent-proof machinery (append-only tables, snapshot fields, re-acceptance banners) — build's B4 gate must state the re-consent consequence, which only exists if this machinery does.

## 3. Legally relevant features (each with `confidence: high|low` + evidence)

| Feature | Probe sketch | Legal consequence if present |
|---|---|---|
| payments / subscriptions | `rg -l 'stripe|paddle|lemonsqueezy' backend/ frontend/` + billing app dirs + price/plan fixtures | CGV, rétractation, médiateur, 3-click cancel |
| donations | routes/pages `soutenir|don|donate` + Stripe one-shot flows | don qualification, no tax receipt unless eligible |
| accounts / auth | user model, allauth/oauth configs, register routes | CGU, privacy, consent proof, minors floor |
| UGC hosted | upload endpoints, media models (video/image/audio/comment) | DSA notice&action, UGC license, LCEN takedown |
| minors | age fields, birth-date validation, age checkboxes, CGU age clauses | 15+ floor (art. 45 LIL), AIPD trigger, wording level |
| AI processing | `rg -l 'gemini|openai|anthropic|mistral' backend/` + consent gates | disclosure in privacy, consent basis, transfer |
| trackers / cookies | `rg -l 'matomo|gtag|analytics|posthog|plausible|hotjar|pixel'` frontend + cookie-consent components + what is actually set on first visit | banner regime vs no-banner regime (art. 82 LIL) |
| giveaways / concours | `rg -li 'giveaway|concours|tirage|lot|prize'` models + draw logic | règlement de jeu-concours if prizes are real |
| transactional email | SMTP config, email templates, marketing-send code (`rg -l 'newsletter|campaign'`) | L34-5 CPCE opt-in only if marketing exists |
| ads / sponsored | ad/encart apps, `rel="sponsored"`, mention_legale fields | transparency of commercial content |

Feature facts the code cannot settle (are giveaway prizes real? is a user population under 15 actually served?) become **questions**, never assumptions.

## 4. Dormant integrations (wired but disabled)

```
rg -n 'RECAPTCHA|GTM_ID|GA_MEASUREMENT|SENTRY_DSN|PIXEL_ID' PROJECT_ROOT --glob '!node_modules' -g '!*.lock'
```

For each hit where the key/flag is empty or the loader is behind an env guard: record under `features.dormant` with its **activation consequence** in one sentence (e.g. « activation ⇒ cookie tiers `_GRECAPTCHA` ⇒ bandeau de consentement obligatoire, rupture du régime art. 82 LIL »). Dormants are flagged, proposed as `checks:` candidates, **never activated**.

## 5. Corpus inventory + rot scan

```
# existing legal docs and their word counts / locales
# placeholders in published text
rg -n 'À COMPLÉTER|A COMPLETER|TO COMPLETE|POR COMPLETAR|AUSZUF|TODO|XXX|lorem|en cours de désignation' <substrate files>
# prior audits + their finding-ID sequences (harvest, never re-mint)
rg -l 'Criticité|P0|finding' PROJECT_ROOT/DOCS/AUDIT PROJECT_ROOT/DOCS/legal 2>/dev/null
rg -o '\[[A-Z]+-[A-Z0-9]+-[0-9]+\]' <those files> | sort -u
# binding project conventions (language, emoji ban, anti-TODO CI, LOC caps)
head -80 PROJECT_ROOT/AGENTS.md PROJECT_ROOT/CLAUDE.md 2>/dev/null
# E2E legal invariants (cookie-banner tests, legal-page smoke tests, guard tests)
rg -ln 'cookie_banner|no_cookie|legal|cgu|consent' PROJECT_ROOT/scripts/tests PROJECT_ROOT/**/tests 2>/dev/null | head
```

Record: corpus inventory (doc → locales present), placeholder hits (V3 input), the project's existing finding-ID registry and highest sequence numbers per `DOMAIN-TOPIC` (audit reuses IDs for persisting issues and continues sequences — it never re-mints), binding conventions build must respect, guard tests (V5 input) with the exact command that runs each.

## 6. Runtime capabilities

```
ls ~/.claude/agents/ 2>/dev/null        # sonnet-quick / sonnet-standard / opus-standard / opus-deep present?
```

Absent agent types ⇒ fall back to the Agent tool's `model` parameter + session-default effort, and say so in the run plan. Also confirm `jq`, `rg`, `python3` availability — a missing tool downgrades the affected checks to BLIND SPOT, never silently to pass.

## Synthesis rule

The Phase 0 output is a **profile**: substrate, version_refs, features (+dormants), corpus inventory, conventions, guard tests, prior-audit ID registry, capability set — each entry either evidence-backed or `confidence: low` and queued for the confirmation salvo. Drift vs the stored `.claude/legal.yml` follows the config doctrine (structural fields refresh with a report; human-authored fields — `quirks`, `accepted_risks`, `origin: human` checks — show diff and ask).
