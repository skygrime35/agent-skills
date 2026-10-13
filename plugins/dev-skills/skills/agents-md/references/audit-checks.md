# Audit grid

Contents:
- P0 - active risk (P0.1-P0.4)
- P1 - false facts (P1.1-P1.6)
- P2 - structure and cost (P2.1-P2.5)
- P3 - hygiene (P3.1-P3.7)
- Non-regression check

Tag a finding `report-only` when sync cannot fix it or another skill owns it (SKILL.md, audit report format).

Each check states what it looks for, the command that runs it, and the severity of a hit. **No finding without the evidence that produced it.**

Report most severe first. Every check that could not run is itself reported, as a blind spot.

## P0 - active risk

### P0.1 Concurrency without isolation

Does the documentation encourage parallel agents while specifying no isolation mechanism? Isolation normally lives in the orchestration section (owned by `/orchestration`); search all agent docs, and when none is found recommend `/orchestration` as the fix.

```bash
grep -ril "parallel\|concurrent\|simultan" AGENTS.md AGENTS/*.md 2>/dev/null
grep -ril "worktree\|disjoint\|isolat" AGENTS.md AGENTS/*.md 2>/dev/null
```

First command hits and second does not: **P0**. Two agents in one working tree destroy each other's work, and the failure is silent. Field case: a `git stash` from one agent carried away another's changes and left an orphan untracked migration; the entire backend suite stopped running with no error anywhere.

### P0.2 Rule keyed to a name that will not hold

A rule anchored to a specific model, tool version, branch or person becomes a no-op the moment reality moves.

```bash
grep -nE "(Opus|Sonnet|Haiku|Fable|GPT|Claude [0-9])" AGENTS.md
```

A hit inside a normative sentence ("X is the orchestrator") is **P0**: rewrite as a role. Hits in an illustrative list are fine.

### P0.3 Absolute with no workable exception

A rule stated without exception whose enforcement depends on an environment that may not provide it. Example: "the main agent never edits files itself" in a harness that restricts subagents. The rule then blocks the task instead of optimising it.

Read every "always" and "never" and ask what happens when the mechanism is unavailable. No answer in the text: **P0**.

### P0.4 Production branch unprotected

```bash
grep -in "main\|master\|develop\|production" AGENTS.md | grep -in "never\|forbidden\|without"
```

No rule restricting direct modification of the deploying branch: **P0**.

## P1 - false facts

Every one of these is a hit produced by executing something, never by reading.

### P1.1 Commands that do not work as documented

Execute each command found in the documentation. Specifically:

```bash
docker ps >/dev/null 2>&1 && echo "unprivileged docker works: any documented sudo is wrong"
```

For each cited branch:

```bash
git branch -a --list '<cited-branch>'   # empty output = dead reference
```

### P1.2 Dead paths

Every path cited anywhere in the documentation, resolved against the repository.

**Two filters are mandatory, or this check is useless.** Without them it produced 14 false positives on its first field run, which is exactly how a check loses its reader.

1. **Only strings containing a `/` are paths.** A bare `page.tsx`, `models.py`, `api.py`, `route.ts`, `tailwind.config.ts` is a *convention name* cited as a rule ("named exports except `page.tsx`"), not a pointer to a file. Testing it for existence is meaningless.
2. **Resolve against every detected root**, not just the repository root: documentation legitimately writes paths relative to a domain (`shared/hooks/useMediaQuery.ts` under `frontend/src/`, `graph.json` under the artefact folder).

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_dead_paths.py --quiet-ok          # default scope: root docs, docs index, every tracked domain AGENTS.md
python3 ${CLAUDE_SKILL_DIR}/scripts/check_dead_paths.py --quiet-ok <file>…  # explicit files
```

The script covers backtick paths and markdown links (with `#anchors`). A backtick span counts as a path only with a known file extension, or a trailing `/` whose first segment is a repo directory; migration ids, dotted symbols, npm packages, routes, CSS classes, git refs, rates and `a/b` word pairs are ignored. Resolution: citing file, repo root, then suffix via `git ls-files`. Output `file:line<TAB>target<TAB>status`: `dead` is a finding, `ambiguous` (several suffix matches) is a P3 to disambiguate, `conditional` (mentioned as deleted or optional) is not a finding. Read-only; exit 1 when something is dead.

**Archive paths.** Run the script a second time on the dated records (`archives.paths` from the project config, else `errors/`, `adr/`, `postmortems/`-style directories). Dead references there are not P1: report ONE P3 info finding with their count and the policy applied. Policy resolves as `--archives` > `archives.policy` > `${user_config.agents_md_archives_policy}` > `tolerate`. `tolerate`: leave them. `annotate` and `fix` act only in `sync`, see SKILL.md.

A partial path that resolves under no root is a genuine finding, and a common one after a compression pass: shortening `backend/apps/orders/infrastructure/…` to `infrastructure/…` reads fine and points nowhere.

### P1.3 Sections promised but absent

The subtle variant: the file exists, the section named inside it does not.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_sections.py --quiet-ok            # default scope as P1.2
python3 ${CLAUDE_SKILL_DIR}/scripts/check_sections.py --quiet-ok <file>…
```

It checks `FILE § Section` (accent- and case-insensitive; `§ A / B` checks both; a bare `AGENTS.md` means the root one), `see FILE section X` and markdown anchor citations (`FILE#anchor`, `#anchor`) against the target's headings. A label found only as a bold bullet lead is `ok-bullet` (not a finding). Same output format and exit codes as P1.2; read-only.

Field case: a guardrail announced a debt register "sectioned Backend/Frontend/Infra/Doc/Legal/Tests"; the `Doc` section had never existed. Any agent following the rule looks for a section that is not there.

### P1.4 State claims contradicted by the repository

Claims like "the allowlist is empty", "all apps are migrated", "zero legacy". Verify each against the artefact:

```bash
grep -vc '^\s*#\|^\s*$' <the-allowlist-file>
```

### P1.5 External-state claims contradicted by a live probe

Claims about state outside the repository files: CI ("the hosted CI is disabled / phantom"), services and containers ("X is not running"), quotas, disabled features, "no workflow runs". Probe each one read-only:

```bash
gh run list --limit 10                       # are there runs at all, and their conclusions
gh run view <run-id> --json jobs             # job-level conclusions
docker compose config --quiet                # effective compose file, no side effect
stat <path>                                  # existence, mtime of a claimed artefact
```

- Claim contradicted by the probe: **P1**. **P0** when the doc pairs the claim with a destructive instruction (for example "CI is phantom, delete its runs"): an agent will act on a false premise.
- Claim that cannot be probed (no `gh` auth, daemon unreachable, sandbox): list it as a blind spot with its rank, never as a green check.
- Probes stay read-only: no `gh run rerun|cancel|delete`, no `docker compose up|down|exec`, no API write. A probe that would change state is not run.

### P1.6 .gitignore contradicts the agentic file set

Probes and expected state: detection.md section 12. Finding **P1** (evidence: the `git check-ignore` / `git ls-files` output) when a must-be-ignored path is tracked or not ignored (`.claude/settings.local.json`, `*.local.*` configs, run journals, `.claude/worktrees/`), or a must-not-be-ignored path is ignored (`.claude/settings.json`, `.claude/agents/`, `.claude/<skill>.yml`, `.claude/<skill>/`, AGENTS.md, CLAUDE.md, `AGENTS/`); a whole-directory `.claude/` pattern is the usual cause. Paths that do not exist are "not applicable". Fix line: the minimal `.gitignore` edit, plus `git rm --cached <path>` for a tracked local file (never deletes the working copy). Zero writes in audit.

## P2 - structure and cost

### P2.1 Instruction budget

Count with the method defined once in `${CLAUDE_SKILL_DIR}/references/structure.md` (Instruction budget, "Counting method"): normative statements, a bullet with a modal counted once, always-loaded files plus followed `@imports`, harness share separate, with its margin. Run the canonical counter on every always-loaded file (markers of the document's language, EN and FR lists defined there):

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/count_rules.py AGENTS.md CLAUDE.md --section-heading <heading> ...
```

The JSON gives statements and prohibitions per file and per section; a marker grep (`grep -oiE '\b(must|never|always|required|forbidden|shall|do not)\b' AGENTS.md | wc -l`) is only a cross-check.

Report the count (with its +/- margin), the margin to the budget, and name the sections that would be cut first.

### P2.2 Balance

```bash
awk '/^## /{if(s)printf "%6d  %s\n",c,s; s=$0; c=0; next} {c+=length($0)+1} END{if(s)printf "%6d  %s\n",c,s}' AGENTS.md
```

Flag any section several times larger than the project's own vital commands. Tag it `report-only` when the bulk is behaviour rules, which must stay in the root. Field case: the knowledge-graph section outweighed the vital commands by 6.5x, and most of its bulk duplicated a README the file itself pointed to.

### P2.3 Self-declared redundancy

The reliable tell: a cross-reference that follows a restatement of its own target.

```bash
grep -niE "see (the )?(section )?(above|below)|cf\. §|as (stated|mentioned) above" AGENTS.md AGENTS/*.md
```

Each hit: check whether the referenced content was just restated. If so, one of the two is surplus.

### P2.4 Externalisable detail

For each guardrail longer than roughly 400 characters, probe whether the detail already exists elsewhere:

```bash
grep -qi "<distinctive-term-from-the-guardrail>" <candidate-target-file> && echo "already covered: compressible"
```

Only a positive probe justifies compression. A negative probe means the root file is the sole holder: leave it.

### P2.5 History in an always-loaded file

```bash
grep -niE "phase [0-9]|migrated in|was split|historically|formerly|used to be" AGENTS.md
```

Completed-refactor narrative in the root file is a permanent cost for archaeology.

Volatile state (content-rules §7) is the same finding, in every agentic doc (root and domain AGENTS.md, CLAUDE.md, `AGENTS/`): a current branch name, a task in progress, open PRs, "as of" dates, drifting counts. Fix: replace it by the command that reads it, or delete it; keep it only under the content-rules §7 exception. Arbitrate per occurrence, do not ask.

```bash
git ls-files 'AGENTS.md' 'CLAUDE.md' '*/AGENTS.md' 'AGENTS/**' | xargs grep -niE "current(ly)? (branch|task|work)|we are (on|working)|in progress|as of [0-9]|open PRs?|latest version"
```

## P3 - hygiene

### P3.1 Generic filler

```bash
grep -niE "best practice|clean code|readable|maintainable|as needed|appropriate(ly)?|make sure to" AGENTS.md AGENTS/*.md
```

Every hit is a candidate for deletion: it spends budget to say what the model already knows.

### P3.2 Stated rules the file itself breaks

If the file forbids something, check the file:

```bash
grep -c "TODO\|FIXME" AGENTS.md              # against its own anti-TODO rule
grep -oP '[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}]' AGENTS.md | wc -l   # against its own no-emoji rule
```

### P3.3 Missing mechanical enforcement

For each rule that a script could check (size limits, forbidden markers, forbidden characters, naming), verify a checker exists:

```bash
ls scripts/ tools/ bin/ .claude/*/ 2>/dev/null; grep -rl "check_\|lint" .github/workflows/ 2>/dev/null
```

No checker means the rule rests entirely on discipline. Report it and offer the generator.

### P3.4 Coverage gaps

What the repository does that the documentation never mentions:

```bash
ls .github/workflows/*.yml | while read w; do
  n=$(basename "$w"); grep -qi "${n%.yml}" AGENTS.md AGENTS/*.md 2>/dev/null || echo "undocumented workflow: $n"
done
```

When the doc has a "CI-equivalent / replay locally" list, compare it with the workflows' real steps: extract every `jobs.<id>.steps[].run` command from `.github/workflows/*.yml` (python3 with `yaml`, else grep of `run:`) and match each job against the list. A job whose commands appear nowhere in the list = **P2** (name the job). Jobs the project deliberately leaves out are listed in `ci_replay_excludes` of `.claude/agents-md.yml` and skipped.

### P3.5 Misplaced agentic script (migration candidate)

Classification and evidence: detection.md section 10; destinations: guardrail-scripts.md (Script triage). One P3 per agentic script (marker, identical content, or reads only agentic files; never by file name alone) outside `.claude/<skill>/`, stating the evidence (marker line, file name, or the agentic paths it reads) and the references that would be updated. Ambiguous scripts are listed as blind spots.

### P3.6 Outdated or edited checker copy

Compare per guardrail-scripts.md (Canonical copies); only scripts classified agentic (detection.md section 10) are copies. Content differs and marker version older: P3 "outdated copy" (sync replaces it). Edited locally (marker version current, or no marker): P3 with the diff, handled as a project variant.

### P3.7 Project variant of a canonical checker

A script that shares or resembles a canonical name but has no marker and no identical content is a variant, not a copy. Run both per guardrail-scripts.md (Project variants), comparing defaults as well as output. P3 "replaceable variant" when the canonical script covers every finding (cite both outputs); P3 "upstream candidate" for each extra capability the variant has (what, `file:line`).

## Non-regression check (mandatory after any sync batch touching guardrails)

```bash
# before
awk '/^## .*[Gg]uardrail/,/^## [^G]/' AGENTS.md | grep -c '^- '
# after: must match unless a merge was explicitly approved

# every prohibition marker must survive
for t in <each distinctive term from each guardrail>; do
  grep -q "$t" AGENTS.md || echo "*** LOST: $t ***"
done
```

Also run `count_rules.py` on the touched files before and after and compare `prohibitions`. Report both counts explicitly. A `sync` that cannot show this check has not finished.
