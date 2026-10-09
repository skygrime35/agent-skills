# Detection

## Contents

1. The branch -> environment mapping
2. Environments and the version endpoint
3. Enumerating preprod-targeting suites
4. The reseed command
5. Dispatchable vs branch-gated workflows
6. Capability preflight

Everything `/full-test` needs to learn about a project before it can act. Fan out subagents, since these probes are independent: `haiku-standard` for probes that return evidence (curl, `gh`, config reads), `Explore` for read-only file location.

## 1. The branch → environment mapping (the critical one)

You must end up able to answer: **which ref deploys production, and which deploys preprod?** Everything else in the skill hangs off this.

**Do not read the trigger and stop.** The trigger tells you *when* a workflow runs, not *what it deploys*. A catch-all trigger with the routing hidden in a conditional is common and is exactly the trap:

```yaml
on:
  push:
    branches: ["**"]              # every branch triggers this
jobs:
  deploy:
    runs-on: ${{ github.ref_name == 'main' && fromJSON('[...prod-runner]') || fromJSON('[...preprod-runner]') }}
```

Here the mapping is `main → prod, everything else → preprod`, and it is invisible from the trigger alone. **Read the whole job**: `runs-on`, `concurrency.group`, `if:` conditions, the environment/`SRV_ROOT`/compose-file/compose-project it computes, and the argument it finally passes to the deploy script.

Where to look, by platform:

| Platform | Files | What carries the mapping |
|---|---|---|
| GitHub Actions | `.github/workflows/*.yml` | `on.push.branches`, plus **conditionals on `github.ref_name`** inside jobs |
| GitLab CI | `.gitlab-ci.yml` | `rules:`/`only:`/`except:`, `environment.name` |
| CircleCI | `.circleci/config.yml` | workflow `filters.branches` |
| Jenkins | `Jenkinsfile` | `when { branch }` |
| Platform-side | `vercel.json`, `netlify.toml`, `render.yaml`, `fly.toml`, `app.json`, `amplify.yml` | often **nothing in the repo** — the mapping lives in the platform dashboard |

**Platform-side deploys are the hard case.** If the repo contains no evidence of the mapping, you cannot infer it. That is a Phase 0 hard stop: ask the human to declare `prod_branch` and the preprod rule in `.claude/full-test.yml`. Guessing "main is prod" is usually right and occasionally catastrophic — which is precisely the wrong trade.

Also record:
- **Concurrency/cancellation semantics.** `cancel-in-progress: true` on the preprod group means a concurrent push (including a bot's) **cancels your deploy and steals the slot**. This drives principle 3 and Phase 7.
- **Whether preprod is a single shared slot** across all non-prod branches, or per-branch/per-PR environments. A shared slot is a race; per-branch is not.
- **Whether tests gate the deploy.** Often they don't — a deploy workflow and a CI workflow can be entirely independent, so preprod may be deployed with no checks at all. Worth stating in the announce.

## 2. Environments and the version endpoint

- `PREPROD_URL`, `PROD_URL` — from the deploy workflow, compose files, nginx config, project docs (`DEPLOYMENT.md` and friends), or the config file.
- `VERSION_ENDPOINT` — **the endpoint that returns the running SHA.** Don't assume from the name. Probe candidates (`/api/health/`, `/api/version/`, `/healthz`, `/__version__`) and **verify a SHA actually comes back**:

```bash
curl -fsS "$PREPROD_URL/api/health/" | jq .
```

Two failure modes to expect:
- **The obvious endpoint withholds the SHA on purpose.** A `/version` that returns `{"environment":"production"}` unauthenticated is a deliberate choice (public repo ⇒ SHA maps to known CVEs), and the SHA hides behind a bearer token or on a *different* endpoint. Probe, don't assume.
- **No endpoint exposes a SHA at all.** Then principle 3 has no proof to stand on. Report it as a **blind spot** in the announce and every report: you can confirm preprod is *healthy*, not that it runs *your code*. Ask whether to proceed on that weaker footing.

**Record how to compare, and compare by prefix.** This is a real trap with a lying symptom. A deploy script that stamps the SHA with `git rev-parse --short HEAD` produces a string whose **length is not stable**: git sizes short SHAs from the repo's object count (`core.abbrev=auto`), so a CI runner's checkout can serve **7** characters for the very commit your local full clone abbreviates to **8**. Compare those directly and the gate fails on every single run — while reporting something that isn't true ("preprod never deployed"), because the environment is in fact serving exactly your code.

So never compare against `git rev-parse --short HEAD`. Take the full SHA and match the served value as a prefix:

```bash
SERVED=$(curl -fsS "$PREPROD_URL/api/health/" | jq -r .version)
FULL=$(git rev-parse HEAD)
[ "$SERVED" = "${FULL:0:${#SERVED}}" ] && echo "up to date"
```

Guard the degenerate cases: an empty `SERVED` matches every prefix, and placeholder values (`dev`, `unknown`, `latest`) mean the SHA was never injected — treat all of these as "no proof", not as a match.

## 3. Enumerating preprod-targeting suites

Cast wide, then filter to what targets a **deployed** environment. Sources:
- CI workflows whose steps hit a URL or run inside deployed containers.
- E2E harness directories (`e2e/`, `tests/e2e/`, `scripts/tests/`), Playwright/Cypress configs — a config with **no `webServer`** is a strong tell that it assumes a deployed target.
- Post-deploy scripts: smoke, SEO, observability/health checkers.
- Load-test wrappers (k6, Locust, Artillery).
- Test docs (`E2E_TESTS.md`, `TESTS.md`, `COMMANDS.md`).

**Exclude** anything that doesn't need a deployed environment (unit tests, typecheck, lint, build) — that is out of scope; see the skill's non-goals.

For each suite, record:

| Field | Why it matters |
|---|---|
| exact command | principle 4 — reuse, never reimplement |
| route: dispatchable workflow / local / SSH | drives Phase 6 execution |
| **mutates preprod data?** | drives serialization (principle 5) |
| **reseeds by itself?** | avoids a double reseed in Phase 5 |
| gating flag (`E2E_DEEP=1`, `--project=…`) | drives the deep option |
| cost class: light / moderate / **costly** | costly is excluded from "everything" |
| log/artifact paths | needed by the report |
| own target guard | must be respected, never bypassed |

**Trust the code over the docs.** Phase counts, module lists and step inventories in docs drift; the runner's imports are the truth. When they disagree, use the code and mention the drift in the report — it's useful signal for the user.

## 4. The reseed command

Find it (`seed*`, `fixtures`, `loaddata`, `reset-db`, management commands) and record **what identifies its target** — that's what guardrail 3 needs:

- the **host** it runs on (an SSH host that only has preprod containers is strong evidence);
- the **compose project / compose file** (`-p myapp-preprod -f docker-compose.preprod.yml`);
- the **database name**;
- the seed's **own scoping** (e.g. deleting only users under a dedicated test email domain is much narrower than a `flush`).

Also record the **mode the project requires**. A full `--reset` is often mandatory rather than an idempotent re-seed: idempotent seeds let state accumulate across runs, which drifts the environment and causes false failures that look like product bugs. If the project documents a reason, carry it into the config as a quirk.

Note any **destructive sibling scripts** you must *not* call (a `reset-db.sh --prod`, a `copy-preprod-to-prod.sh`). Knowing they exist is how you avoid reaching for them.

## 5. Dispatchable vs branch-gated workflows

Determines Phase 3's redeploy route and Phase 6's execution route.

```bash
gh workflow list --all                  # is it registered and active?
gh workflow view <name> --ref <branch>  # what triggers does it expose?
```

- **`workflow_dispatch` present** → preferred: `gh workflow run <name> --ref <branch>`, no history pollution.
- **GitHub constraint:** a workflow is only dispatchable if its file exists **on the default branch**. A workflow file living only on a feature branch cannot be dispatched, whatever its `on:` block says.
- **Branch-gated / marker-gated** (`if: contains(github.event.head_commit.message, '[marker]')`, or `branches: [some-branch]`) → often unusable from the branch you're on. Prefer dispatch; fall back to an empty commit only if nothing else exists.
- **Stale comments lie.** A comment saying "dispatch unusable" may predate the fix. Verify with `gh workflow list` rather than believing the file.

## 6. Capability preflight — along the real path

Never `command -v` on the host for a tool the project only ever invokes elsewhere. Test the actual invocation:

```bash
ssh "$HOST" 'docker compose -p myapp-preprod -f docker-compose.preprod.yml exec -T backend python manage.py help seed_e2e_users' >/dev/null
gh auth status
curl -fsS -o /dev/null -w '%{http_code}' "$PREPROD_URL/api/health/"
git push --dry-run          # only if a push may happen
```

Stop **only** for capabilities genuinely missing along the path the project uses them, and hand back a precise "install/authenticate X" list. A host without `psql` is irrelevant when `psql` only ever runs inside a container; flagging it is a false blocker that costs the user trust.
