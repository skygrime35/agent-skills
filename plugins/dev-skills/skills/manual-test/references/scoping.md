# Scoping, detection and configuration

Phases 0-1.

## 1. Scope forms

| Form | Meaning | Diff |
|---|---|---|
| `develop..main` (default; actually `INTEGRATION_BRANCH..PROD_BRANCH` as detected) | what the integration branch holds that production lacks | `git log --no-merges PROD..INTEGRATION`, `git diff PROD...INTEGRATION` |
| `<ref>..<ref>` | two refs given by the user (branches, tags, SHAs) | same with the two refs |
| `branch` | current branch vs its merge-base with `INTEGRATION_BRANCH` | `git merge-base INTEGRATION HEAD`, then log and diff from it |
| `all` | the whole project: every user-facing feature, no diff | feature inventory from routes, menus, docs, tests (use `.claude/test-coverage/inventory.yml` if present) |
| `features:"a,b"` | a named list | locate each feature by name in code and docs; unmatched names are asked, never guessed |

Unspecified scope => AskUserQuestion with the five forms, default first. Use three-dot diff (`A...B`) for file changes and two-dot log for commits. Empty change set => say so and offer another scope.

## 2. Branch detection

`PROD_BRANCH`: from `.claude/manual-test.yml`, else the base doc, else CI/deploy workflow evidence (the branch that deploys production), else `origin/HEAD`. `INTEGRATION_BRANCH`: the branch that deploys preprod or is the PR base for feature work (`develop`, `staging`, `dev`, `next`). Beware catch-all workflow triggers with routing inside a job conditional. Ambiguous => ask; never default silently.

## 3. Environment

- Target preprod (default): URL from config, else the base doc, else deploy workflow or compose files. The URL must pass G1's allowlist. Verify reachability with `curl -fsS -o /dev/null -w '%{http_code}'`.
- Served version: if a version endpoint exists, compare its SHA (prefix match, never to a short SHA) with the HEAD of the scope's newest ref. Mismatch => say that preprod does not serve the scope and ask: redeploy through the project's own flow (it may deploy a shared slot: ask), or test what is served and mark the gap.
- Target local: the project's documented dev stack; start it only through the project's commands. Local stacks started for the run are stopped at the end when the project's docs say so.
- Locale and base path: derive absolute links (`https://host/<locale>/<path>`) from the project's routing, never relative paths.

## 4. Devices and accounts

Ask which devices the tester has: desktop browser, Android, iPhone. Phone-only steps (push, install as app, camera, share sheet) are planned only for available devices. Accounts: login hints from config (role, username or email pattern, where the password lives: a name or path, never the value). If the skill creates a test account (G6), or the config declares a test account on the non-production target, its credentials are given in full in every login step (`step-format.md`); the tester's own account is never written out (identifier only). No password is ever written to notes or `state.json`: record the identifier and where the credentials come from.

## 5. `.claude/manual-test.yml`

Committed, structural and human-authored fields; never secrets (env-var and file **names** only). Detection refreshes structural fields; human fields are never overwritten (keep the stored value, report the diff).

```yaml
version: 1
branches:
  prod: main                     # THE production branch; never assumed
  integration: develop
environments:
  preprod:
    url: https://preprod.example.com
    version_endpoint: /api/version   # optional; JSON or text holding the SHA
    locale_prefix: /fr               # optional
  local:
    url: http://localhost:3000
  prod_urls: [https://example.com]   # forbidden as a target, kept to recognise it
devices: [desktop, android]          # defaults for the device question
accounts:                            # hints only
  - role: admin
    login_hint: "admin account from the seed, password in env var SEED_ADMIN_PASSWORD"
prepare:                             # the project's own data tools, verbatim
  seed: "docker compose exec backend python manage.py seed --reset"
  commands:
    - name: send-test-notification
      run: "docker compose exec backend python manage.py send_test_push <user>"
      sends_to: "tester device only"   # G4 evidence
archive:
  folder: DOCS/AUDIT/                # else plugin option, else detection
  index: DOCS/AUDIT/README.md        # optional
  filename: "{date}-manual-test-{scope}.md"
quirks:
  - "preprod is a shared slot; a push by another branch replaces the code"
```

Resolution: argument > this file > plugin option > default.
