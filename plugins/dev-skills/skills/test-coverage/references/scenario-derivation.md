# Scenario derivation — the grid, the bounds, the cost classes

Audit wave 4: one `sonnet-standard` per domain turns each FEAT into its complete scenario set. The prompt to each agent contains the relevant `kind` grid below + the bounding rules + the instruction that **every scenario carries an observable `expected_outcome` and evidence** (the code path that produces it). Arbitration kills anything without either.

## 1. The derivation grid, per feature kind

For every feature, derive in this order — the order is the checklist:

1. **Nominal** — the happy path, one scenario per meaningfully distinct input shape (not per input value).
2. **Each expected error** — read the code for every error the feature is *designed* to produce (validation rejections, 4xx branches, thrown/returned errors, non-zero exits, UI error states). Each one is a scenario whose test **proves the error actually occurs with the right observable**. An error branch nobody can trigger is still a scenario (class `edge`) — dead error code is a finding, not a skip.
3. **Canonical edges** — from the table below, keep only those the input surface makes possible.
4. **Chains** — only under the bounding rules (§2).

| kind | Nominal outcomes | Expected errors to hunt in code | Canonical edges |
|---|---|---|---|
| ui-action | resulting view/state change, emitted call | disabled state, validation message, error toast/banner, empty-state | double-click/rapid repeat, stale session, loss of connectivity mid-action, keyboard-only path |
| route (page) | renders with data, renders empty | 404, 403/redirect-to-login, error boundary | direct deep-link (no prior navigation), query-param garbage, unauthenticated visit |
| endpoint | 2xx + body shape + persisted state | each 4xx branch, auth/authz failures, payload validation per field | empty body, oversized payload, unicode/emoji in strings, boundary values (0, -1, max), idempotency/duplicate submit, concurrent mutation |
| cli-command | exit 0 + stdout contract | each non-zero exit path, bad flags, missing args | empty stdin, huge input, no-TTY, interrupted mid-run, `--help` accuracy |
| job | completes + side effect | retry/failure path, poison message handling | double-delivery/idempotency, empty queue, clock edge (DST, month-end) |
| webhook | accepted + processed | bad signature rejected, replay rejected, unknown event ignored | out-of-order delivery, duplicate delivery |
| config-flag | behavior on, behavior off | invalid value handling | flip at runtime (if hot-reloaded), unset/default |

**The expected-error rule** (governing principle 2, operationalized): the scenario's `expected_outcome` names the exact observable — "HTTP 422 with `errors.email`", "exit code 2 + message on stderr", "toast « fichier trop volumineux »". A test that only asserts "it fails" proves nothing; a code path that *should* error but doesn't is precisely the bug this skill exists to surface.

## 2. Bounding rules (what keeps the set finite)

- **Level 1 is exhaustive.** Every isolated action gets its full grid — no sampling, no top-N. This is the non-negotiable floor.
- **Chains require shared state.** A 2-3 action chain is derived **only** when the actions demonstrably share state the isolated tests cannot exercise: login→session-dependent action, add-to-cart→checkout, create→edit→delete of the same resource, upload→process→download. "A then B" with no shared state is two level-1 scenarios, not a chain — derive nothing.
- **Chains are 2-3 links.** A candidate needing 4+ links is minted as **one** scenario of class `chain`, `cost: costly`, with the link list in `description` — listed, priced, never expanded into its combinatorial closure.
- **No cross-product of inputs.** Boundary values are per-field scenarios, not a matrix; a form with 5 fields yields ~5 boundary scenarios plus one all-empty, not 2^5.
- **Dormant features** (`status: dormant`) get their grid derived but every scenario `cost: costly` — testing disabled code paths needs activation, which is a human decision.

## 3. Cost classes

| cost | Meaning | Build behavior |
|---|---|---|
| cheap | unit-testable, milliseconds, no external state | written and run, always in the default worklist |
| moderate | integration/e2e-local, seconds, local DB/emulator | written and run, in the default worklist |
| costly | long chains, dormant activation, heavy fixtures, minutes+ | **listed with its real cost stated, gated behind its own confirmation** — never bundled into "go all" |
| gated-preprod | needs real deployed environment (payments, emails, third parties) | **written** with an env-var-driven target, marked `gated`, executed only via `/full-test`. Never run by this skill |

## 4. Worked examples

**FEAT « Connexion email/mot de passe » (ui-action + endpoint)** → nominal: bons identifiants ⇒ session + redirect. Expected errors: email inconnu ⇒ 401 message générique (identique au cas mot-de-passe faux — anti-énumération, l'outcome le dit) ; mot de passe faux ⇒ 401 même message ; compte verrouillé ⇒ 423 + bannière. Edges: soumission double rapide ⇒ une seule session ; unicode dans l'email ; champ vide ⇒ validation front ET back (deux scénarios — deux couches, deux observables). Chain (état partagé) : login→accès page protégée ; login→logout→page protégée ⇒ redirect.

**FEAT « export CSV » (cli-command)** → nominal: exit 0, fichier au schéma attendu. Expected errors: chemin de sortie non inscriptible ⇒ exit 2 + stderr ; base vide ⇒ exit 0 + fichier en-têtes seuls (le code le prévoit — à prouver). Edges: 100k lignes (cost: moderate) ; interruption mi-export ⇒ pas de fichier partiel corrompu. Pas de chaîne : rien ne partage d'état.

**FEAT « webhook Stripe » (webhook)** → nominal: `checkout.session.completed` ⇒ abonnement activé en base. Expected errors: signature invalide ⇒ 400, rien en base (l'outcome inclut le "rien en base") ; event inconnu ⇒ 200 ignoré. Edges: replay du même event ⇒ idempotent. Le nominal contre le vrai Stripe ⇒ `gated-preprod` ; le nominal contre payload fixture local ⇒ `moderate`. **Les deux existent** — le fixture ne waive pas le réel.
