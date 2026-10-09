# Guardrails

Canonical text of G1-G4 (SKILL.md Phase 1 and fix-loop.md only link here), how to *prove* a target is preprod, and the edge cases. Arguments never override G1-G4. This file is the skill's reason to exist: everything else is convenience.

## The shape of the danger

The skill does three kinds of thing that could reach production:

| Action | How it reaches prod | Guard |
|---|---|---|
| `git push` / `gh workflow run` | pushing the prod-deploying branch **deploys production** | G1 — branch check |
| pointing a suite at a URL | a destructive E2E suite against prod **destroys real user data** | G2 — target check |
| running a seed/reset | a reseed against the prod DB **destroys real user data** | G3 — proof of target |

Each guard is asserted in Phase 1 **and re-asserted immediately before the action it protects.** A check performed five minutes and three questions ago is not a check; state can change (a branch switch, a config reload, an argument you forgot).

## G1 — Never write from the prod-deploying branch

```
current branch == PROD_BRANCH  →  STOP. No commit, no push, no dispatch.
```

- Compare against `PROD_BRANCH` **from the config**, resolved in Phase 0 — never a hardcoded `main`. Plenty of projects deploy prod from `master`, `production`, `release/*`, or a tag.
- **Offer** to move to a development branch. **Do not do it.** A test skill that rearranges branches has exceeded its mandate, and the user may have deliberate reasons to be sitting on that branch.
- **No argument lifts this.** `--redeploy=wip` on the prod branch stops the run. Arguments express preferences; guards express invariants.
- **fix-loop's full-auto mode does not lift it either.** Autonomous pushes mean the check runs *more* often, not less: G1 is re-asserted immediately before **every** push of every iteration, and a hit stops the **whole loop**, not just that push. "Full-auto" removes approval questions; it never removes guards.
- **A tag-triggered prod deploy** means the branch check is necessary but not sufficient: also refuse to create or push tags matching the prod release pattern.
- If the mapping is `unknown` (platform-side deploy, no repo evidence), you **cannot** run G1 — that's why Phase 0 hard-stops instead of proceeding.

Reporting a stop is part of the job: say *why* (pushing here would deploy production), not just *that*.

## G2 — Never point a suite at production

- Resolve and compare the **host**, not a substring. `preprod.example.com` contains `example.com`; a naive `case`/`grep` match gets this backwards in one direction or the other. Parse the URL, compare the host, and treat prod-shaped hosts (`www.` variants, bare apex, the prod IP, the prod port) as prod.
- **Prefer an allowlist to a denylist.** "Is it one of the two hosts I know to be preprod or local?" is a question with a safe failure mode. "Is it not prod?" is a question that says yes to anything you forgot.
- **The harness's own guard is authoritative.** Many mature harnesses validate their target themselves — sometimes at module import, which is the strongest form. If a harness refuses your URL, **the URL is wrong, not the guard.** Do not pass a flag, edit a whitelist, or set an env var to get past it. Report the refusal as a finding.
- Read-only suites are **not** exempt. The exemption is a judgement call about someone else's code ("it only reads, probably"), and load tests in particular are read-mostly *and* an outage risk.

## G3 — Prove the reseed target before reseeding

A reseed is the most destructive thing this skill can do. **Proof, not inference.**

Evidence that counts, strongest first:
1. **The command physically cannot reach prod** — the host has no prod containers, no prod database, no prod credentials. **Verify this; never infer it from a migration note.** Decommissionings are routinely left half-done: a prod that "moved" is often still running on the old host, frozen for rollback. Check (`docker ps`, the DB list) and if prod artifacts are colocated, this evidence class **does not apply** — drop to 2 and 3 and say so.
2. **The target is named and it names preprod** — `-p myapp-preprod -f docker-compose.preprod.yml`, a DB named `..._preprod`, an explicit `--env=preprod`. Note what happens when the naming is *omitted* rather than wrong: `docker compose` without `-p` infers the project from the current directory name, which is a coin flip, not a guard.
3. **The seed scopes its own destruction** — e.g. it only deletes users under a dedicated test email domain, so even misaimed it can't touch real accounts. This is the only class that survives a wrong target, which makes it the most valuable one to confirm.

Evidence that does **not** count:
- **A fail-closed check a password lifts.** A seed that refuses to run unless `SEED_PASSWORD` is set is protection against *accident*, not against *intent* — and this skill supplies that password. Never treat it as the reason a reseed is safe.
- `DEBUG`/`ENV` variables the deploy could have set either way.
- "The URL I'm testing is preprod, so the DB must be too." The seed usually runs over a *different* channel (SSH/docker exec) than the tests (HTTPS). They can diverge.

**No proof ⇒ no reseed.** Report it as a blind spot and let the suites run against whatever state exists, or let the user reseed by hand. An unproven reseed is not worth a green run.

## G4 — Never widen a guard to make a run possible

If completing a run requires adding a host to an allowlist, exporting a password to lift a fail-closed check, passing `--prod`/`--force`, or editing a validator — **stop**. That is not an obstacle, that is the system telling you the run is wrong. Report what you would have had to disable; that sentence is usually the most valuable output of the run.

**Extension for fix-loop fix agents.** Fix agents inherit every guard, and G4 gains a specific form there: deleting a test, skipping it, weakening an assertion, marking it expected-failure, or widening a harness guard to make an iteration green is a G4 violation — a failure in disguise. The orchestrator inspects every agent diff for this before committing; a test that "cannot pass without X" is a finding for the needs-user basket, never a candidate for removal.

## Edge cases

**Shared preprod slot.** Where every non-prod branch deploys to one environment, and the CI cancels in-progress deploys, a concurrent push (a bot's, a colleague's) silently replaces the code under test mid-run. This is not hypothetical and it does not announce itself: the environment stays healthy, it just serves someone else's commit. Hence: gate on the **SHA** (Phase 4), re-check it **every tick** (Phase 7), and when it moves, mark results **invalid** — not "failed". A failure means the code is broken; invalid means you learned nothing. Collapsing the two sends the user hunting a bug that doesn't exist.

**Ambiguous mapping.** Two workflows that both look like they deploy; a deploy script taking an env argument you can't trace to a branch; the mapping living in a dashboard. Stop and ask. The cost of asking is one question; the cost of guessing is production.

**Preprod that isn't isolated from prod.** Sometimes preprod shares a database, an object store, a Stripe account, or an email sender with prod. If detection turns this up, say so **loudly before any destructive suite**: a reseed that is technically aimed at preprod can still delete prod data through a shared store, and a test-account email can still reach a real inbox.

**Prod colocated on the preprod host.** The most likely version of the above, and the easiest to miss because the *documentation says otherwise*. After a migration, the old production is commonly left running on the old host — frozen for rollback, still holding real data. Every doc will say prod "moved"; `docker ps` will say prod is right there. **Check, don't read.** When prod is colocated, the "different machine" argument evaporates and the only thing standing between a reseed and real data is an argument on a command line. That is a much thinner guard than a host boundary, and the user deserves to be told which one they're relying on.

**Prod-shaped test credentials.** A seed that creates a known-password superuser is fine on a throwaway preprod and catastrophic anywhere reachable. If preprod is publicly exposed, that's worth one line in the report — not a stop, but the user should know.

**The user asks to test prod.** Say plainly that this skill cannot, and why: its suites mutate and reseed, and its guards exist precisely to make that impossible. Point at read-only alternatives (a public-pages smoke, a health probe) as a *different* activity. Do not improvise a "careful" prod run, and do not offer to disable guards on request — the guards are the product.
