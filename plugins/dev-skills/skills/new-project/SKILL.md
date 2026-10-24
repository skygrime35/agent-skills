---
name: new-project
description: "Starts a brand-new project from an idea or spec and drives it to a finished, deployed, pushed state: functional interview, spec checkpoint, agent waves, lint and test loops, live VPS deployment of the complete app (docker on loopback, nginx vhost, certbot), private GitHub repo. Two human checkpoints; never touches existing vhosts, containers or listeners. Also --dry-run and --teardown."
when_to_use: "new project, from scratch, I have an idea for an app, bootstrap an app, start a project from this spec, build me an app and host it"
argument-hint: "<idea|path-to-spec> [--quick|--auto] [--spec=<file>] [--dir=<path>] [--repo=<ssh-url>] [--no-host] [--teardown=<name>] [--dry-run] [-h|--help]"
---

# /new-project

Skill directory: `${CLAUDE_SKILL_DIR}`. Reference files mark bundled paths with the CLAUDE_SKILL_DIR variable in dollar-brace form; the shell does not set it, so replace it with this directory before running or copying anything. Plugin options appear in this file as their configured value. In reference files they stay as `user_config.<key>` placeholders: use the value this file shows. If a value still shows as a placeholder here (option never configured), use its `default` in `${CLAUDE_SKILL_DIR}/../../.claude-plugin/plugin.json`.

Start a project from **an idea or a spec** and deliver **a finished, live thing**: linted to zero, tested to green, built, deployed with a clickable URL (web-reachable types; artifact + proof otherwise), documented, under CI, committed atomically and pushed to a fresh private GitHub repo, using as little of the user's time as possible.

The project is classified into a canonical type (web app, API, CLI, TUI, library, static site, bot/worker, browser extension, or off-matrix with explicit blind spots); the type pilots stack, scaffold, linters, artifact form and proof.

**Harness (first step of Phase 0, every mode, dry runs included).** If `${CLAUDE_SKILL_DIR}` still shows as a literal placeholder, the harness is not Claude Code and the skill directory is the folder holding this SKILL.md. Detect the harness per `${CLAUDE_SKILL_DIR}/../orchestration/references/harness.md` (H1) and announce it with the detected profile. **Claude Code**: the agent types, tools and degradations below apply as written; Haiku types are the default for briefed subagents and for every agent launched by a subagent, a higher type being a ceiling for its role, not a start (H2). **Any other harness**: read each agent type below as its role tier (H3: `haiku-*` light, `sonnet-standard` standard, `opus-*` strong), use the harness's own spawn, question, task-list and stop mechanisms, never name a model; without subagents the waves run inline in their planned order with every gate kept, and each degradation is reported (H2, H5). On every harness, close each agent once its report is used and stop stalled ones before moving on (H4).

## Usage

```
/new-project <idea or path to spec>   # frame -> spec checkpoint -> build -> live checkpoint -> publish
/new-project --auto <idea>            # skip the spec checkpoint; only the live checkpoint remains
/new-project --quick <idea>           # express interview: one salvo, the rest becomes assumptions
/new-project --repo=<ssh-url>         # push to an existing repo instead of creating one
/new-project --spec=<file>            # explicit spec file; skips the interview entirely
/new-project --dir=<path>             # create the project here instead of the default location
/new-project --no-host                # skip deployment; local artifact + proof only
/new-project --teardown=<name>        # remove a previously hosted deployment (compose down, vhost, cert)
/new-project --dry-run                # frame, classify, print spec + plan + DoD. Zero writes anywhere
/new-project -h | --help              # print this Usage block and stop
```

`-h`/`--help` alone: print the Usage block verbatim and stop.

**Flag precedence.** `--teardown` excludes every other flag (refuse the combination). `--dry-run` beats anything that writes. `--auto` implies `--quick`-style handling (unknowns become assumptions, no extra interview rounds) but never skips the live checkpoint. `--spec` skips the interview. An argument never overrides a guardrail: nothing is pushed without a GO.

**Resolution order** for every policy answer: command argument > learned-tastes file (`~/.claude/new-project.yml`; there is no project config, the project does not exist yet) > plugin option `${user_config.<KEY>}` (values below) > recommended default. Ask only when no safe default exists or a guardrail is hit.

Plugin options in effect: UI language `${user_config.new_project_ui_language}`, docs language `${user_config.new_project_docs_language}`, look and feel baseline `${user_config.new_project_look_and_feel}`, privacy default `${user_config.new_project_privacy_default}`, auto-name `${user_config.new_project_auto_name}`, host domain pattern `${user_config.new_project_host_domain_pattern}`, port range `${user_config.new_project_port_range_start}`-`${user_config.new_project_port_range_end}`, deploy host `${user_config.new_project_deploy_host}`, hosting enabled `${user_config.new_project_hosting_enabled}` (false = behave as `--no-host` by default), disk floor `${user_config.new_project_min_disk_gb}` GB, agents fallback `${user_config.new_project_agents_fallback}`. Report to the user in the UI language; code, identifiers and commits stay English; README and human docs use the docs language.


## Start menu (bare invocation)

A bare invocation shows status and a menu and never auto-runs a mode: rules, freshness and output format in `${CLAUDE_SKILL_DIR}/../orchestration/references/start-menu.md`. State probes: an unfinished `.claude/new-project/journal.md` in the current or default directory, `~/.claude/new-project.yml` (learned tastes present or first run), `~/.claude/new-project-deployments.yml` (hosted projects, teardown candidates), whether the current directory is empty.

Picks: unfinished run => resume it; otherwise ask for the idea in one plain question and offer `/new-project <idea>`, `/new-project --quick <idea>` and `/new-project --dry-run <idea>`; hosted deployments listed => `/new-project --teardown=<name>` as a non-default pick.

Workflow: 1 `--dry-run` (optional) -> 2 `/new-project <idea>` (spec checkpoint, build, live checkpoint, publish) -> 3 `/manual-test` and `/full-test` on later changes.

## Scope

**For:** greenfield projects, from "an app to track my expenses" to a full written spec, driven to a runnable, deployed, pushed, documented state. Web-reachable types end **hosted on the deploy host** (unless hosting is disabled: `--no-host`, or `${user_config.new_project_hosting_enabled}` false) behind its existing nginx at `<project>.<base-domain>` (the name is the project's own: **never a "demo" label, not even in DNS**). What is hosted is the **complete application** (real backend, database, background jobs, persistent data, every must-have working through the public URL); never a reduced feature set, front-only showcase or mocked data layer. This is stated here once and applies everywhere.

**Not for:** adding features to an existing codebase. **Not for** production-grade operations: the slot carries no backups, monitoring, SLA or hardening for third-party users; the final report says so plainly. **Not for** overwriting a non-empty directory: if the target exists and is not empty, stop and say so.

## Governing principles (these override any convenience)

1. **The user's minutes go before the code.** The interview digs deep into expectations; after the spec GO, **zero questions until the live checkpoint** (whatever surfaces becomes an assumption or blind spot in the report). Questions come in grouped salvos with opinionated tick-able options, and never ask what the learned-tastes file, plugin options, the spec or detection already answers. Machine time is spent lavishly.
2. **"Finished" is a mechanical checklist.** Nothing reaches the live checkpoint until the per-type Definition of Done (`${CLAUDE_SKILL_DIR}/references/done-checklist.md`) passes; an unmet item is fixed or presented as a justified exception, never silently dropped.
3. **Proof over claims.** The live checkpoint ships evidence that the application works end-to-end: live URL first, plus a screenshot through it (visual), a command transcript (CLI), real `curl` output (API). "It compiles" is not proof. Details: `${CLAUDE_SKILL_DIR}/references/delivery.md`.
4. **Fix the code, not the tests**, unless a test is genuinely wrong, and then say so in the report.
5. **Nothing is published before the GO, except the deployment itself.** No `gh repo create`, push or package publishing before the GO. The live app goes up on the user's own host just before Checkpoint 2, reachable but unadvertised. Commit early and atomically (git init at scaffold time, never one mega-commit).
6. **Reuse, don't reinvent.** Native generators (`npm create vite`, `cargo new`, `uv init`), the **agents-md** skill for docs, **impeccable** for frontend polish, **run** for run-proof, **dataviz** for charts.
7. **Unknown means explicit blind spot, never a fake green.** An off-matrix platform narrows the run (closest workable stack, named blind spots such as "iOS build impossible here").
8. **First, do no harm: the host is shared and already serves real projects.** The run must be able to prove it broke nothing (Phase 0 snapshot, Phase 5 diff).
   - Existing vhosts, containers, compose projects and listeners are **untouchable**; the skill only creates, and **every created resource is recorded in the deployment registry** (`${CLAUDE_SKILL_DIR}/references/hosting.md`), the sole proof of ownership: nothing absent from the registry may ever be modified or removed. Certs, cron jobs and firewall rules are never touched either; the snapshot also records their listing (when readable) so the diff proves it.
   - Enforced mechanically: `${CLAUDE_SKILL_DIR}/scripts/check-host-safety.sh` snapshots in Phase 0 and re-diffs in Phase 5, allowing only this run's declared resources; **a non-zero exit blocks Checkpoint 2** until explained and fixed.
   - `nginx -t` before any reload; on failure remove your own file and reload nothing.
   - **Every** port the run binds is checked free (`ss -tlnp`) first and bound to `127.0.0.1`. Collision means another port, **never kill the listener**.
   - Toolchains install **user-space only** (`uv`, `corepack`/`nvm`, `rustup`). Never `apt install` or system-wide changes without an explicit ask; never edit shared config (`~/.bashrc`, global git config, docker daemon, sysctl, ufw).
   - Hosted containers get **memory and CPU limits**. Disk headroom is checked in Phase 0 and before large builds.
   - `sudo` serves only the whitelisted hosting commands (vhost file, `nginx -t`/reload, certbot). No `docker system prune`, no docker-daemon or service restarts.

## Tooling

**External CLIs** (Phase 0 preflight tests each): `git`, `gh` (`gh auth status`), `ssh` (`ssh -T git@github.com`), the runtimes the chosen stack needs (detect before proposing a stack that needs what is missing); for hosting `nginx`, `certbot`, `sudo -n`, `ss`, `curl`.

**Claude Code capabilities** and degradation (every degradation is reported in the final report):
- EnterPlanMode/ExitPlanMode for Phases 0-2 and Checkpoint 1; absent: Checkpoint 1 becomes a plain-text screen plus AskUserQuestion.
- AskUserQuestion for salvos and checkpoints; absent: the same questions as a numbered plain-text list.
- TaskCreate/TaskUpdate for phase visibility; absent: a checklist in the journal.
- Agent tool (or Workflow if the user opted in) for the orchestration waves.
- SendUserFile for screenshots; if unavailable, give the file path.
- Skills: **agents-md**, **orchestration**, **impeccable**, **run**, **dataviz**.

## Reference files

- `${CLAUDE_SKILL_DIR}/references/interview.md`: load in Phase 1. The funnel, the one sanctioned technical question, per-feature deep dive, salvo rules.
- `${CLAUDE_SKILL_DIR}/references/stacks.md`: load in Phase 2. Types, stack matrix, scaffold commands, linters, off-matrix procedure.
- `${CLAUDE_SKILL_DIR}/references/orchestration.md`: load in Phase 2 and 3. The per-wave orchestration table.
- `${CLAUDE_SKILL_DIR}/references/done-checklist.md`: load in Phase 2 (instantiate) and Phase 5 (walk).
- `${CLAUDE_SKILL_DIR}/references/delivery.md`: load in Phase 4-5. Artifact form per type, proof capture on a headless machine.
- `${CLAUDE_SKILL_DIR}/references/hosting.md`: load in Phase 0, Phase 5 and teardown. Deployment recipe, ports, registry, guardrails.
- `${CLAUDE_SKILL_DIR}/references/config-schema.md`: load in Phase 0 and Phase 6. Learned-tastes file, plugin option table, enrichment rules.

---

# Procedure

Register phases with `TaskCreate`. Keep a journal at `<project>/.claude/new-project/journal.md` from Phase 3 on (scratchpad before the directory exists), one line per completed step.

**Mode routing (first):**
- `-h`/`--help`: print Usage, stop.
- `--teardown=<name>`: run the teardown from `${CLAUDE_SKILL_DIR}/references/hosting.md` (**confirm before removing anything**), stop.
- `--dry-run`: Phases 0-2 read-only; print spec, plan, DoD instance and a section titled `Blind spots`, stop. No directory, scaffold, repo or hosting. **In dry-run run no hosting command of any kind: no `sudo` (not even `sudo -n true`), `docker`, `nginx`, `certbot`, `ss`, no reading of `/etc/nginx`, no `gh` or `ssh` calls, no `git init`, no `mkdir`, no host-safety snapshot.** The only allowed probes are `which <tool>` and `df`. Every skipped check (hosting, ports, name clashes, GitHub login) goes into the blind spots as "not probed in dry-run". The final answer must state in one plain sentence that nothing was written or created. 
- default: **enter plan mode** unless already in it (Phases 0-2 are read-only by design). Checkpoint 1 is delivered as the plan: the user's plan approval is the GO. `--auto` skips Checkpoint 1 and does not enter plan mode.
- bare invocation with no idea or spec: Start menu, then ask for the idea in one plain question (no safe default exists).

## Phase 0: Preflight and preferences
0. **Harness.** Detect and announce it first (**Harness** paragraph above, `harness.md` H1); everything below dispatches through the selected profile.

1. **Load** `~/.claude/new-project.yml` (learned tastes, `${CLAUDE_SKILL_DIR}/references/config-schema.md`). Missing is normal on a first run: matrix defaults, file created at the end.
2. **Detect capabilities** in parallel: `git`, `gh auth status`, `ssh -T git@github.com`, installed runtimes, the dedicated agent types (see `${CLAUDE_SKILL_DIR}/references/orchestration.md`; missing ones fall back to the Agent tool's `model` parameter), and the host per `${CLAUDE_SKILL_DIR}/references/hosting.md` (reverse proxy, sudo, base domain from the domain-pattern option, ports in use, registry). Take the **host-safety snapshot**: `NP_MIN_DISK_GB=${user_config.new_project_min_disk_gb} ${CLAUDE_SKILL_DIR}/scripts/check-host-safety.sh snapshot <dir>` (scratchpad now, moved to `<project>/.claude/new-project/host-snapshot/` at scaffold). Insufficient disk for the planned build: surface it now. Failures here constrain choices and become blind spots ("no sudo: hosting unavailable, `--no-host` behavior, said out loud now"). When hosting is disabled (`--no-host` or `${user_config.new_project_hosting_enabled}` false), skip the host detection and the snapshot: nothing on the host is written, so there is nothing to prove.
3. **Resolve the target directory**: `--dir`, else `projects_dir` from the learned-tastes file, else `~/projects/<name>`. Non-empty: stop.
4. **Resume check**: if `<project>/.claude/new-project/journal.md` exists and is under 7 days old, **resume automatically** at the last completed phase and print that it did; an older journal is reported and ignored (never overwrite a non-empty directory).

## Phase 1: Deep discovery interview

Goal: the user's **real expectations**, as a brief covering objective, success criterion, users, usage context, killer scenario, out-of-scope, look and feel, data expectations, hosting expectations, and every must-have as a mini-spec with **user-confirmed acceptance criteria** (`${CLAUDE_SKILL_DIR}/references/interview.md`).

Iron rules: the interview is a **funnel** (general to precise) and **strictly functional**: zero jargon, exactly **one** technical question, the target medium. Every decision below the medium is derived in Phase 2 and justified at Checkpoint 1.

1. **Skip anything already answered**: by the idea text, `--spec`, the learned-tastes file or plugin options (UI/docs language, look and feel baseline, privacy default). A precise spec: ask only about the dimensions it leaves open.
2. Otherwise run the funnel: AskUserQuestion salvos (max 4 questions, opinionated tick-able options, adaptive) until a new question would no longer change what gets built. `--quick`/`--auto`: one salvo.
3. Whatever stays unknown becomes an explicit assumption in `SPECS.md`.

## Phase 2: Classify, stack, spec -> Checkpoint 1

1. **Classify** per `${CLAUDE_SKILL_DIR}/references/stacks.md`; off-matrix follows its procedure.
2. **Choose the stack**: explicit wishes, then learned tastes, then matrix default, then (off-matrix) a short research pass. One justifying paragraph.
3. **Name the project**: always show 3-4 candidates, **recommended one first**. The user's own name, when given, is the first candidate; the others are derived (short, pronounceable, usable verbatim as repo, directory and subdomain: lowercase, hyphens, no accents). Each is collision-checked (directory in `projects_dir`, GitHub repo, nginx conf, compose project, registry, well-known project clash).
4. **Plan the orchestration** per `${CLAUDE_SKILL_DIR}/references/orchestration.md`: work packages with disjoint file sets, agent type per package, dependency waves (wave 0 = scaffold + shared contracts). Trivial scope: a one-package table run by the main loop.
5. **Write `SPECS.md`** (scratchpad; moves into the repo at scaffold): brief, stack + rationale, directory tree, orchestration table, instantiated DoD, assumptions, blind spots, name, target directory, preferences applied.
6. **Checkpoint 1: spec validation** (skipped by `--auto`). One screen: spec summary, stack + rationale, tree, orchestration table, DoD, assumptions, **and the 3-4 name candidates, recommended one first.** The user's reply to Checkpoint 1 is the GO and carries the naming choice: it picks one candidate or gives their own name (checked the same way); rejection or other edits are the corrections loop. Deliver via ExitPlanMode in plan mode, else via AskUserQuestion. With `${user_config.new_project_auto_name}` true or `--auto`, the recommended name is used without waiting and stated in the report.

## Phase 3: Scaffold and implement

1. **Scaffold** with the native generator. `git init` immediately; first commit = scaffold; move `SPECS.md` in. Set up linters, test framework and `.gitignore` now.
2. **Implement per the validated table**: wave by wave, packages in parallel on their assigned agent types, isolation respected (disjoint file sets; worktrees when overlap is unavoidable), each wave integrated (compiles, lints, committed atomically) before the next. A dependency the table missed: update the table in `SPECS.md` + journal line, never silent improvisation.
3. UI: invoke **impeccable** before calling the implementation done; a generic-looking UI is not finished.

## Phase 4: Quality loops

1. **Lint loop** until zero errors; fix cheap warnings, list the rest.
2. **Test loop** until green; fix the code, not the tests (principle 4). A must-have without a test gets one.
3. **Build** the artifact in the canonical form for the type (`${CLAUDE_SKILL_DIR}/references/delivery.md`). A build failure loops back to implementation.

## Phase 5: Deploy, prove, walk the DoD -> Checkpoint 2

1. **Run the artifact for real** (via **run** where it applies) and capture proof per delivery.md.
2. **Deploy** (web-reachable types, unless `--no-host`, hosting disabled by `${user_config.new_project_hosting_enabled}` false, or hosting declared unavailable) per `${CLAUDE_SKILL_DIR}/references/hosting.md`: free port, complete stack via docker compose on `127.0.0.1:<port>`, `<project>` vhost, privacy gate (default `${user_config.new_project_privacy_default}`), certbot, registry entry. **Verify from outside**: `curl` and screenshot through the public URL.
3. **Host-safety check**: `NP_MIN_DISK_GB=${user_config.new_project_min_disk_gb} ${CLAUDE_SKILL_DIR}/scripts/check-host-safety.sh diff <snapshot-dir> --allow-name <project> --allow-port <port>`. Exit 0 is a DoD prerequisite; a violation **blocks Checkpoint 2**: fix the drift or, if legitimate, document it as a justified exception shown to the user.
4. **Walk the DoD** item by item, hosting items included. Fix failures; leftovers become justified exceptions.
5. **Checkpoint 2: live validation** (never skippable): live URL first (with basic-auth credentials if the gate applied), the user should be able to click the URL and try the app before answering, artifact path, exact launch/install command, proof, DoD result, blind spots, proposed repo name. GO/KO via AskUserQuestion. **KO**: collect what is wrong, loop to Phase 3, redo Phases 4-5, updating the deployment in place (same URL). **GO**: Phase 6.

## Phase 6: Docs, CI, publication

1. **Agentic docs**: invoke the **agents-md** skill (`agents-md init`) for the whole doc shape, and the **orchestration** skill (`orchestration init`) for the orchestration section; do not describe or impose a shape here. Then verify README (copy-pasteable quickstart, run it), LICENSE, and that docs match the code as built, not as specced.
2. **Basic CI**: a GitHub Actions workflow running the lint and test commands that just passed locally.
3. **Publish**: `gh repo create <name> --private --source . --push` (SSH remote), or push to `--repo=`. Verify with `git ls-remote`.
4. **Final report** (UI language): live URL, artifact path + launch command, repo URL, DoD summary, blind spots and exceptions, what the hosting slot does not provide (backups, monitoring, hardening), the lifecycle (it stays up; `/new-project --teardown=<name>` removes it, also written in the README), and hand-offs: `/legal` if the app has accounts, payments or personal data; `/test-coverage` to grow the test suite; `/safe-merge` to gate future releases. Screenshots via SendUserFile (fallback: file path).
5. **Enrich the learned-tastes file** with the confirmed choices of this run per config-schema.md: show the diff, never silently rewrite human-authored entries.
