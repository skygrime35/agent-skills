---
name: new-project
argument-hint: "<idea|path-to-spec> [--quick|--auto] [--spec=<file>] [--dir=<path>] [--repo=<ssh-url>] [--no-host] [--teardown=<name>] [--dry-run] [--help]"
description: "Use to start a brand-new project from a raw idea or an existing spec and drive it to a finished, proven, pushed state — including a live, publicly reachable deployment of the COMPLETE application on the user's VPS (docker on loopback + nginx vhost + certbot, no 'demo' anywhere) — in one governed run with minimal human time. Funnel discovery interview, strictly functional, with one technical question: the target medium (website / mobile app / desktop software / CLI); all other choices are derived and justified at the spec checkpoint (--quick for one express salvo). Two human checkpoints: the spec (plan mode, before any code) and the live app (before anything is pushed). Between them fully autonomous: agent waves, lint loops to zero, test loops to green, build, per-type Definition of Done. On GO: agents-md init, basic CI, private GitHub repo + SSH push. Never edits existing vhosts, containers or listeners. Learns tastes in ~/.claude/new-project.yml. Also --dry-run (plan only) and --teardown=<name>."
---

# /new-project

Start a project from **an idea or a spec** and deliver **a finished, live thing**: linted to zero, tested to green, built, **deployed as the complete application with a clickable URL** (for anything web-reachable; artifact + proof otherwise), documented, under CI, committed atomically and pushed to a fresh private GitHub repo — while consuming as little of the user's time as possible.

This skill is **portable across project types**. It classifies the project into a canonical type (web app, API, CLI, TUI, library, static site, bot/worker, browser extension — or off-matrix with explicit blind spots), and that type pilots everything downstream: default stack, scaffold command, applicable linters, artifact form, and what counts as proof.

## Usage

```
/new-project <idea or path to spec>   # normal run: frame → spec checkpoint → build → live checkpoint → publish
/new-project --auto <idea>            # skip the spec checkpoint; only the live checkpoint remains
/new-project --quick <idea>           # express interview: one salvo, the rest becomes explicit assumptions
/new-project --repo=<ssh-url>         # push to an existing repo instead of creating one
/new-project --spec=<file>            # explicit spec file; skips the interview entirely
/new-project --dir=<path>             # create the project here instead of the default location
/new-project --no-host                # skip deployment; local artifact + proof only
/new-project --teardown=<name>        # cleanly remove a previously hosted deployment (compose down, vhost, cert)
/new-project --dry-run                # frame, classify, print spec + plan + DoD. Zero writes anywhere
/new-project --help                   # print this Usage block and stop
```

If invoked with `--help`/`-h` and nothing else, print the Usage block above verbatim and stop.

Arguments override questions; anything not passed is resolved by preference file, then detection, then (only if it matters) a question. An argument never overrides a **guardrail** — `--auto` still stops at the live checkpoint; nothing is ever pushed without a GO.

## What this skill is for / non-goals

**For:** greenfield projects — from "an app to track my expenses" to a full written spec — driven end-to-end to a runnable, deployed, pushed, documented state. For web-reachable types the run ends with the project **hosted on the user's VPS** behind its existing nginx — a URL the user can open from anywhere, named after the project itself (`<project>.<base-domain>` — **never a "demo" label, not even in the DNS name**). What is hosted is the **complete application**: real backend, real database, background jobs if any, persistent data — every must-have working end-to-end through the public URL. Never a reduced feature set, a front-only showcase, or mocked data layers.

**Not for:** adding features to an existing codebase (that's ordinary work, or `/graphify` first to understand it). **Not for** production-grade operations — the deployment is real and fully functional, but the slot carries no backups, monitoring, SLA or hardening for third-party users; adding those is a separate decision outside this skill, stated plainly in the final report. **Not for** re-scaffolding or overwriting a non-empty directory: if the target directory exists and is not empty, stop and say so.

## Governing principles (these override any convenience)

1. **The user's minutes go where they buy the most: before the code.** The discovery interview digs deep into expectations — a wrong expectation caught live costs a full build loop; caught in the interview it costs one tick. After the spec GO, **zero questions until the live checkpoint**: never drip mid-build questions; whatever surfaces becomes an assumption or a blind spot in the report. Questions come in grouped salvos with opinionated tick-able options (never one-at-a-time), and never ask what the preference file or detection already answers. Machine time is spent lavishly throughout: agent fan-out, quality loops, research.
2. **"Finished" is a mechanical checklist, not a feeling.** Nothing reaches the live checkpoint until the per-type Definition of Done (`references/done-checklist.md`) passes. An unmet item is either fixed or presented as an explicit, justified exception — never silently dropped.
3. **Proof over claims.** The live checkpoint ships evidence the application **actually works end-to-end**: the live URL first, plus a screenshot through that URL for anything visual, a command transcript for a CLI, real `curl` output for an API. "It compiles" is not proof. The exact artifact path and launch/install command are part of the deliverable.
4. **Fix the code, not the tests** — unless a test is genuinely wrong, and then say so explicitly in the report.
5. **Nothing is published before the GO — except the deployment itself.** No `gh repo create`, no push, no package publishing before the GO. The live app is the *object* of Checkpoint 2: it goes up on the user's own host just before the checkpoint, reachable but unadvertised, so the user validates by clicking, not by reading. Locally, commit early and atomically (git init at scaffold time, never one mega-commit at the end).
6. **Reuse, don't reinvent.** Scaffold with the ecosystem's native generator (`npm create vite`, `cargo new`, `uv init`…). Docs via the **agents-md** skill in init mode. Frontend polish via **impeccable**. Run-proof via **run**. Charts via **dataviz**. Never hand-roll what an existing skill or generator already does well.
7. **Unknown ⇒ explicit blind spot — never a fake green.** An off-matrix platform (mobile, desktop GUI…) doesn't fail the run; it narrows it: pick the closest workable stack, and state plainly what this machine cannot verify (e.g. "iOS build impossible here — artifact is an Expo project + QR code; native build is a blind spot").
8. **First, do no harm — the whole machine is shared and already serving real projects** (preprod deployments run here). Nothing this skill creates may break anything that already exists, and the run must be able to *prove* it didn't (Phase 0 snapshot → Phase 5 diff). Concretely:
   - Existing vhosts, containers, compose projects, listeners, certs, cron jobs and firewall rules are **untouchable** — the skill only ever *creates* new resources, and **every resource it creates is recorded in the deployment registry** (`references/hosting.md`), which is the sole proof of ownership: nothing absent from the registry may ever be modified or removed.
   - This is enforced **mechanically**, not by discipline: `scripts/check-host-safety.sh` snapshots the host in Phase 0 and re-diffs it in Phase 5, allowing only this run's declared resources; **a non-zero exit blocks Checkpoint 2** until explained and fixed.
   - `nginx -t` before any reload; a failed test means remove your own file and reload nothing.
   - **Every** port the run binds — dev server, test server, deployment — is checked free (`ss -tlnp`) first and bound to `127.0.0.1`. Collision ⇒ another port, **never kill the listener**.
   - Toolchains are installed **user-space only** (`uv`, `corepack`/`nvm`, `rustup`). Never `apt install` or any system-wide change without an explicit ask; never edit shared config (`~/.bashrc`, global git config, docker daemon, sysctl, ufw).
   - Hosted containers get **memory and CPU limits** — a leaky app must not be able to starve the host's other services.
   - **Disk headroom** is checked in Phase 0 and before large builds — filling the disk breaks everyone.
   - `sudo` serves only the whitelisted hosting commands (vhost file, `nginx -t`/reload, certbot). No `docker system prune`, no docker-daemon or service restarts.
   Full recipe and guardrails: `references/hosting.md`.

## Tooling

**External CLIs** (Phase 0 preflight tests each): `git`, `gh` (`gh auth status`, `gh repo create`), `ssh` (`ssh -T git@github.com`), plus whichever runtimes the chosen stack needs (`node`/`npx`, `python`/`uv`, `cargo`, `go`, `docker`…) — detect what is installed *before* proposing a stack that needs what isn't. For hosting: `nginx`, `certbot`, `sudo -n`, `ss`, `curl` (see `references/hosting.md`).

**Claude Code capabilities:** **EnterPlanMode/ExitPlanMode** for the read-only framing phases and the spec checkpoint; **TaskCreate/TaskUpdate** to register the phases so the long run stays visible and resumable; the **Agent tool** (or **Workflow**, if the user has opted in) with the dedicated agent types for the orchestration waves; **AskUserQuestion** for the interview salvos and both checkpoints; skills **agents-md**, **impeccable**, **run**, **dataviz** as listed above.

## Reference files (load on demand)

- `references/interview.md` — the funnel: general → precise, strictly functional (one sanctioned technical question: the target medium), the per-feature deep dive down to acceptance criteria, the salvo rules.
- `references/stacks.md` — the canonical project types and the matrix type → default stack → scaffold command → linters → tests → artifact form → proof form; the off-matrix procedure.
- `references/orchestration.md` — how to plan the implementation as an orchestration table (work packages → least-cost-capable model + effort tier, dependency waves, mandatory isolation), validated at Checkpoint 1 and executed in Phase 3.
- `references/done-checklist.md` — the universal Definition of Done and the per-type additions.
- `references/delivery.md` — what "an artifact I can actually access and run" means per type, and how to capture proof on a headless machine.
- `references/hosting.md` — the deployment recipe (docker on loopback + nginx vhost + nip.io/subdomain + certbot), port allocation, the deployment registry, the shared-host guardrails, and teardown.
- `references/config-schema.md` — the `~/.claude/new-project.yml` preference schema and how the skill enriches it after each run.

---

# Procedure

Follow the phases in order. Register them with `TaskCreate` at the start. Keep a journal at `<project>/.claude/new-project/journal.md` from Phase 3 onward (before the project directory exists, journal in the scratchpad) — one line per completed step, so an interrupted run resumes instead of restarting.

**Mode routing (do this first):**
- `--help` → print Usage, stop.
- `--teardown=<name>` → run the teardown procedure from `references/hosting.md` for that deployment (confirm before removing anything), stop.
- `--dry-run` → run **Phases 0 → 2** in read-only form, print the spec, the plan, the DoD instance and the blind spots, stop. **No** directory creation, no scaffold, no repo, no hosting.
- default → **enter plan mode** (EnterPlanMode) unless already in it — Phases 0–2 are read-only by design, and plan mode makes that mechanical. Checkpoint 1 is then delivered *as the plan*: ExitPlanMode presents the spec screen, and the user's plan approval **is** the GO (the interview salvos and the name question still run via AskUserQuestion inside plan mode, before ExitPlanMode). Exception: `--auto` skips Checkpoint 1, so it does not enter plan mode.
- then → all phases.

## Phase 0 — Preflight & preferences

1. **Load preferences** from `~/.claude/new-project.yml` (schema: `references/config-schema.md`). Missing file is normal on the first run — proceed with matrix defaults and create it at the end.
2. **Detect capabilities**, in parallel: `git`, `gh auth status`, `ssh -T git@github.com` (repo creation + push route), which runtimes/toolchains are installed, the **dedicated agent types** (`~/.claude/agents/`: sonnet-quick, sonnet-standard, opus-standard, opus-deep — absent ⇒ orchestration falls back to the Agent tool's `model` parameter), and the **host** (per `references/hosting.md`): reverse proxy present, sudo available, base domain (configured subdomain or `<dashed-ip>.nip.io`), ports already in use, deployment registry. Take the **host-safety snapshot** — mechanically, via the bundled guardrail: `scripts/check-host-safety.sh snapshot <dir>` (scratchpad now, moved into `<project>/.claude/new-project/host-snapshot/` at scaffold time). It records listeners, containers, vhosts and disk; Phase 5 re-runs it in `diff` mode to *prove* nothing pre-existing changed. Insufficient disk headroom for the planned build ⇒ surface it now, before writing anything. Failures here don't stop the run — they constrain choices and become blind spots ("no sudo → hosting unavailable, falling back to `--no-host` behavior — said out loud, not discovered at Phase 5").
3. **Resolve the target directory**: `--dir` if given, else the preference file's `projects_dir`, else `~/projects/<name>` (proposed at the spec checkpoint, not asked separately). If the resolved directory exists and is non-empty → stop (non-goal).
4. **Resume check** (needs the resolved directory): if `<project>/.claude/new-project/journal.md` exists from a previous run, read it and **offer to resume** at the last completed phase (a passed quality loop should not be redone from scratch).

## Phase 1 — Deep discovery interview

Goal: the user's **real expectations**, extracted before any code — a **brief** covering objective, success criterion, users, usage context, killer scenario, out-of-scope, look & feel, data expectations, hosting expectations, and **every must-have as a mini-spec**: the per-feature deep dive (Round 3b) drills each one down to trigger & flow, exact content, variants, empty/error states and **user-confirmed acceptance criteria** — deep enough that the feature's acceptance test could be written from the answers alone.

Two iron rules (detailed in `references/interview.md`): the interview is a **funnel** — it starts very general (why, for whom, what success looks like) and each round gets more precise (down to each feature's exact behavior) — and it is **strictly functional**: zero jargon, and exactly **one** technical question allowed — the target medium (website / mobile app / desktop software / command-line tool), asked plainly in Round 1. Every decision *below* the medium is derived by the skill in Phase 2 from the functional answers, and justified at Checkpoint 1 where the user can veto it.

1. If `--spec=<file>` or the input is already a precise spec: read it, then ask **only** about the expectation dimensions the spec leaves open (often look & feel, success criterion, hosting expectations).
2. Otherwise run the funnel of `references/interview.md`: successive AskUserQuestion salvos (max 4 questions each, opinionated tick-able options, adaptive — each round shaped by the previous answers), digging until a new question would no longer change what gets built. `--quick` → single salvo, remaining unknowns become explicit assumptions.
3. Whatever stays unknown is written into `SPECS.md` as an explicit assumption — cheap to correct at Checkpoint 1, never silently guessed.

## Phase 2 — Classify, stack, spec → **Checkpoint 1**

1. **Classify** the project into a canonical type per `references/stacks.md`. The type pilots everything downstream. Off-matrix → follow the off-matrix procedure (closest workable stack + named blind spots).
2. **Choose the stack**: user's explicit wishes first, then the preference file, then the matrix default, then (off-matrix only) a short research pass. Justify the choice in one paragraph — alternatives are mentioned only if genuinely close.
3. **Name the project.** If the user already named it, keep their name. Otherwise **propose 3–4 candidates** derived from the brief: short, pronounceable, evocative of the objective, usable verbatim as repo name, directory name and subdomain (lowercase, hyphens, no accents). Check each candidate for collisions before proposing it: existing directory in `projects_dir`, existing repo on the user's GitHub account, existing nginx conf or compose project on the host, entry in the deployment registry, and an obvious clash with a well-known project. The user picks at Checkpoint 1 (one of the candidates, or their own via "Other").
4. **Plan the orchestration** per `references/orchestration.md`: decompose the implementation into work packages with disjoint file sets, assign each the **least-cost-capable model and effort tier** (Haiku / sonnet-quick / sonnet-standard / opus-standard / opus-deep — falling back to the Agent tool's `model` parameter if the dedicated types aren't on this machine), and arrange them into **dependency waves** (wave 0 = scaffold + shared contracts, single agent; each later wave runs its packages in parallel). **Trivial scope** (a single small module — a script, one page) ⇒ a one-package table executed by the main loop: the machinery scales down, it is never ceremony for its own sake.
5. **Write `SPECS.md`** (in the scratchpad for now; it moves into the repo at scaffold time): brief, chosen stack with rationale, planned directory tree, the **orchestration table**, the **instantiated DoD checklist**, explicit assumptions, blind spots, name (or candidates), target directory.
6. **Checkpoint 1 — spec validation** (skipped by `--auto`): ask the **name question** first via AskUserQuestion (the 3–4 candidates with a recommended one) when the user hasn't named the project, then present *one screen* — spec summary, stack + rationale, tree, **orchestration table** (how many agents, which models/efforts, which waves — vetoable like any other spec item), DoD, assumptions — **via ExitPlanMode when in plan mode** (the plan approval is the GO; a rejection or edit request is the corrections loop), or via AskUserQuestion otherwise. Corrections loop within this phase; GO moves on. This is the cheapest moment to be wrong — that is why it exists. With `--auto`, the recommended name candidate is used and stated in the report.

## Phase 3 — Scaffold & implement

1. **Scaffold** with the ecosystem's native generator from the matrix. `git init` immediately; first commit = scaffold. Move `SPECS.md` in. Set up linters, test framework and `.gitignore` **now**, not at the end — the quality loops must have something to run against from the first module.
2. **Implement per the validated orchestration table** (`references/orchestration.md`): wave by wave, each wave's packages launched in parallel on their assigned model/effort tier, isolation respected (disjoint file sets — worktrees when overlap is unavoidable), each wave integrated (compiles, lints, committed atomically) before the next starts. A dependency the table missed ⇒ update the table in `SPECS.md` + journal line, never silent improvisation.
3. For anything with a UI, invoke **impeccable** before calling the implementation done — a generic-looking UI is not "abouti".

## Phase 4 — Quality loops

1. **Lint loop:** run every linter applicable to the stack (matrix column + anything the scaffold configured). Fix every error. Repeat until zero. Warnings: fix the cheap ones, list the rest in the report.
2. **Test loop:** run the suite; on failure **fix the code, not the tests** (principle 4). Repeat until green. If coverage of a must-have is missing, write the test — the DoD requires must-haves to be tested.
3. **Build:** produce the artifact in the canonical form for the type (`references/delivery.md`). A build failure loops back to implementation, not to excuses.

## Phase 5 — Deploy, prove, walk the DoD → **Checkpoint 2**

1. **Run the artifact for real** — via the **run** skill where it applies — and **capture proof** per `references/delivery.md`: screenshot, transcript, or curl output.
2. **Deploy the application** (web-reachable types, unless `--no-host` or Phase 0 declared hosting unavailable): follow `references/hosting.md` — allocate a free port, run the **complete stack** via docker compose bound to `127.0.0.1:<port>`, create the `<project>` nginx vhost on the base domain, apply the **privacy gate** (private/sensitive data + no in-app authentication ⇒ HTTP basic auth on the vhost by default, credentials delivered at the checkpoint), TLS via certbot, record everything in the deployment registry. **Verify from the outside**: `curl` the public URL and screenshot it through the public URL, not localhost. Non-web types keep artifact + transcript as their proof form.
3. **Run the mechanical host-safety check**: `scripts/check-host-safety.sh diff <snapshot-dir> --allow-name <project> --allow-port <port>`. Exit 0 is a DoD prerequisite; a violation **blocks Checkpoint 2** — fix the drift (or, if the drift is legitimate and explainable, document it as a justified exception with the user's eyes on it).
4. **Walk the DoD checklist** (`references/done-checklist.md`) item by item — including the hosting items. Fix what fails; anything left becomes a justified exception in the report — never silently dropped.
5. **Checkpoint 2 — live validation** (never skippable): present **the live URL first** (with the basic-auth credentials when the privacy gate applied), then the artifact path, the exact launch/install command, the proof, the DoD result, the blind spots, and the proposed repo name. GO / KO via AskUserQuestion. The user should be able to click the URL and try the thing before answering.
   - **KO** → collect what's wrong, loop to Phase 3, then redo Phases 4 and 5 — the deployment is **updated in place** (same URL) so re-validation is one click.
   - **GO** → Phase 6.

## Phase 6 — Docs, CI, publication

1. **Agentic docs:** invoke the **agents-md** skill in **init** mode. The canonical target shape is the **DebriefLab model** (`~/projects/DebriefLab`), scaled down to the new project's size: a thin `CLAUDE.md` that only does `@AGENTS.md` + states the hierarchy; root `AGENTS.md` as the transverse source of truth (guardrails, conventions, vital commands); per-domain `AGENTS.md` files only where a real domain exists; an `AGENTS/` folder of on-demand knowledge with `ARCHITECTURE.md` as the living map and an `adr/` subfolder; `DOCS/` for product docs if any. Adopt DebriefLab's convention verbatim: **docs are updated in the same commit as the code that obsoletes them** — write it into the root AGENTS.md. Then verify README (quickstart must be copy-pasteable and *true* — run it), LICENSE, and that all docs agree with the code as built, not as specced.
2. **Basic CI:** a GitHub Actions workflow running the lint and test commands that just passed locally. This is part of "finished".
3. **Publish:** `gh repo create <name> --private --source . --push` (SSH remote), or push to `--repo=` if given. Verify the push landed (`git ls-remote`).
4. **Final report:** the live URL, artifact path + launch command, repo URL, DoD summary, blind spots and justified exceptions, what the hosting slot does *not* provide (backups, monitoring, hardening for third-party users), the deployment's lifecycle (it stays up — `/new-project --teardown=<name>` removes it cleanly, and the command is also written in the project README), and what to do next.
5. **Enrich preferences:** update `~/.claude/new-project.yml` with the *confirmed* choices of this run (stack per type, license, conventions) per `references/config-schema.md` — show the diff, don't silently rewrite human-authored entries.
