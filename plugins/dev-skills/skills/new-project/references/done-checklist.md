# Definition of Done: "finished" as a mechanical checklist

Instantiated in `SPECS.md` at Phase 2 (so the user validates *what "done" will mean*), walked item by item at Phase 5 before the live checkpoint. Each item: **pass**, **fixed**, or **justified exception** presented at the checkpoint. Never silently dropped.

## Universal (every project)

- [ ] Every **must-have** from the brief is implemented **and covered by at least one test derived from its user-confirmed acceptance criteria** (interview Round 3b) — including its specified empty/error states.
- [ ] All applicable linters: **zero errors** (cheap warnings fixed; the rest listed in the report).
- [ ] Test suite **green**; no test weakened to pass (principle 4 — if a test was genuinely wrong, the report says which and why).
- [ ] Build succeeds from a clean checkout (what is committed builds — not just the working tree with its uncommitted leftovers).
- [ ] The artifact was **actually run at least once**, and the proof captured.
- [ ] `README.md` with: one-line pitch, **copy-pasteable quickstart that was actually executed**, launch/install command, config/env vars.
- [ ] `LICENSE` present (`identity.default_license` of the learned-tastes file `~/.claude/new-project.yml`, unless the user chose another).
- [ ] `.gitignore` correct; **no secret, no `.env`, no build junk in git** (scan before the live checkpoint, not after the push).
- [ ] `.env.example` if any env var exists.
- [ ] History = **atomic commits** with meaningful messages (not one mega-commit).
- [ ] Errors handled at the boundaries: bad input, missing file/config, unreachable upstream → clear message, not a raw traceback.

## Deployment (web-reachable types, unless --no-host or hosting disabled by `${user_config.new_project_hosting_enabled}`)

- [ ] Application reachable **from outside the VPS** at its URL — `<project>.<base-domain>`, **no "demo" label anywhere, DNS included** (curl through the public route, not localhost).
- [ ] **The whole stack is hosted** — backend, database, workers, every service the app needs — and **every must-have works end-to-end through the public URL** (never a front on a mocked or absent backend).
- [ ] **Data persists across a container restart** (`docker compose restart` → previously entered data still there — named volumes verified).
- [ ] HTTPS working (or HTTP with the certbot rate-limit exception stated in the report).
- [ ] **Host-safety check passes mechanically**: `${CLAUDE_SKILL_DIR}/scripts/check-host-safety.sh diff <snapshot> --allow-name <project> --allow-port <port>` exits 0 — the only host changes are this deployment's own registered resources; nothing pre-existing modified, restarted or removed; disk above the floor.
- [ ] **Privacy gate applied**: private/sensitive data + no in-app auth ⇒ vhost basic auth in place (verified: unauthenticated curl gets `401`, authenticated gets through) and credentials delivered in the report — or the user's explicit "open to anyone" choice is on record.
- [ ] `nginx -t` passed before every reload performed during the run.
- [ ] App port bound to `127.0.0.1` only.
- [ ] Deployment registered in `~/.claude/new-project-deployments.yml`; teardown command written in the README.
- [ ] Nothing secret in the vhost or in git; app data lives in named volumes.

## Per-type additions

- **web-app:** no console errors on key screens; basic responsive (mobile viewport not broken); **impeccable** pass done; production build served (not just dev mode).
- **api:** OpenAPI/docs endpoint works; input validation on every route; sensible HTTP codes; CORS deliberate, not `*`-by-accident.
- **cli:** `--help` complete and accurate; exit codes correct (0 success, ≠0 failure); errors on stderr; installable, not just runnable-from-repo.
- **tui:** clean terminal restore on exit and on Ctrl-C; visible key bindings.
- **library:** public API documented (docstrings/rustdoc); installs in a **fresh** environment; semver 0.1.0; no accidental exports.
- **static-site:** no broken internal links; images sized; meta title/description present.
- **bot-worker:** idempotent or explicitly at-least-once; clean shutdown (SIGTERM); structured logs; retries/backoff on upstream failure.
- **browser-ext:** minimal permissions in manifest; loadable-unpacked verified or declared a blind spot.

## Post-GO items (Phase 6, checked before the final report)

- [ ] Agentic docs produced by `agents-md init` and the orchestration section by `orchestration init` (the shape is theirs to define), docs agreeing with the code as built.
- [ ] CI workflow (lint + test) present and **using the exact commands that passed locally**.
- [ ] Pushed; `git ls-remote` confirms; repo is **private** unless told otherwise.
