# Guardrail scripts: generating and wiring

Contents: The four checkers - Copy and stamp - Canonical copies - Project variants - Script triage - Wiring: propose, never do - Wire after clearing, never before - Choosing thresholds - Allowlists

A rule nobody checks decays. These scripts turn written prohibitions into mechanical ones.

They live in `${CLAUDE_SKILL_DIR}/scripts/` and are **copied into the target project** at `<scripts_path>` (resolution in SKILL.md: `guardrail_scripts_path` in config > `user_config.agents_md_guardrail_scripts_path` > `.claude/agents-md/`; no other exception), copied as described in Copy and stamp (not `check_dead_paths.py` / `check_sections.py`, which are audit-only). Pure standard library, no dependency, exit 1 on violation.

## The four checkers

| Script | Enforces | Key options |
|---|---|---|
| `check_no_todo.py` | No deferral markers in shipped code | `--markers`, `--allow`, `--strict` |
| `check_no_stub.py` | Not implemented means not merged | `--exclude` |
| `check_monolith.py` | Size limits per file/function/class | `--file`, `--function`, `--class`, `--allowlist` |
| `check_forbidden_chars.py` | Forbidden characters in a scope | `--chars`, `--comments-only`, `--code-only` |

All take paths as positional arguments and skip the usual noise (`node_modules`, `.next`, `dist`, `__pycache__`, migrations, lockfiles, minified output).

### Precision matters more than coverage

`check_no_todo.py` defaults to the **conventional deferral forms only**: the marker opens a comment, or is followed by `:` or `(owner):`. Prose citing the debt register ("cf. DOCS/TODO.md", "voir TODO §7") is not a deferral marker.

This is not a detail. The first field run of the naive version produced four hits on a codebase that honoured the rule perfectly, all of them sentences pointing at the register. A checker that cries wolf gets disabled, and then the rule is gone. Use `--strict` only when the project genuinely wants every occurrence.

`check_no_stub.py` exempts `Protocol` bodies, `ABC` subclasses, `@abstractmethod` and `@overload`, and skips `.d.ts`. A `...` in a Protocol is a declaration, not a stub.

`check_monolith.py` uses the Python AST for function and class limits (exact), and file-level line counts elsewhere. It deliberately does **not** brace-count other languages: the false positives are worse than the missed hits. Blank lines and comment-only lines are not counted.

## Copy and stamp

The canonical scripts in `${CLAUDE_SKILL_DIR}/scripts/` carry the placeholder line `# dev-skills: agents-md __PLUGIN_VERSION__` right after the shebang. Read the version from `${CLAUDE_SKILL_DIR}/../../.claude-plugin/plugin.json` (`version`), then:

```bash
V=<plugin version>
for f in no_todo monolith no_stub forbidden_chars; do
  sed "2s/__PLUGIN_VERSION__/$V/" ${CLAUDE_SKILL_DIR}/scripts/check_$f.py > <target>/<scripts_path>/check_$f.py
done
chmod +x <target>/<scripts_path>/check_*.py
```

The marker line is the only difference between canonical and copy. Copies are needed because CI cannot read the plugin cache.

## Canonical copies

On every run, compare each project copy (marker or legacy file name) with the canonical script, marker line excluded:

```bash
diff <(sed 2d <project copy>) <(sed 2d ${CLAUDE_SKILL_DIR}/scripts/check_X.py)
```

| Result | Verdict | Action |
|---|---|---|
| No diff, marker version equals current or older | current | refresh the marker only in sync |
| Diff, marker version older than the plugin version | outdated | sync replaces it (single plan); audit: P3 |
| Diff, marker version equals current, or no marker | edited locally | never overwrite blindly: show the diff in the plan and treat as a project variant |

## Project variants

A project script with the same purpose as a canonical checker (file size / monolith, deferral markers, stubs, forbidden characters, agent references), whatever its name, including a name equal or close to a canonical one (`check_forbidden_chars.py`, `check_no_todos.py`, `check_file_size.py`, ...) when it has no `dev-skills:` marker and is not identical to the canonical script (a file name alone never makes a script agentic), and each locally edited copy. A variant stays where it is and is compared as below. Run both on the project with equivalent options, compare the findings:

- The canonical script finds everything the variant finds, and its thresholds and allowlists are expressible as canonical options or config: propose replacing the variant by the canonical copy in `<scripts_path>`, wiring updated to the equivalent options. Put both runs' outputs in the plan as proof. Output on the current repo is not enough: also compare behaviour (read the canonical script's header and defaults) and note every difference in defaults, for example the exit code when an input directory is absent, options with another meaning, other skipped paths. Adapt the wiring to the canonical defaults in the same plan.
- The variant checks more: keep it, and report each extra capability as an "upstream candidate" (what it checks, `file:line`) so the canonical script can absorb it in the skill repo.
- Never delete a project check without that proof that the replacement covers it. No proof, no replacement.

## Script triage

Classification: detection.md section 10. Ownership: this skill moves or replaces only its four checkers (and their canonical copies) and project-written scripts that read only agentic docs; `check_agent_refs.py` and scripts that only check agent types or orchestration config belong to `/orchestration`, which this skill only reports. Destination: agents-md checkers and project scripts reading only agentic docs go to `<scripts_path>`. Project variants are never moved by classification (see Project variants).

- **audit**: each misplaced agentic script is a P3 finding (migration candidate) with its classification evidence. Zero writes.
- **init / sync**: the moves are part of the single plan confirmation, no separate question. Use `git mv`. Order the batches so that moves come last: a move of a WIRED project-written agentic script is allowed (owner decision) only when every check below passes, otherwise it is reported as a P3 candidate.
- **Before any move or replacement, in this order:**
  1. `git grep -n <script name>` over the WHOLE tracked tree (tests, docs, CI workflows, hooks, pre-commit config, Makefile, package.json, templates, archives; not a fixed file list). Archive and history files follow the archives policy.
  2. Find every test that references the script (for example `scripts/tests_unit/test_<name>.py`).
  3. Moving changes the depth: check how the script computes the repository root (`Path(__file__).parent.parent`, `parents[N]`, relative paths) and adapt it.
- **After**: update every reference found, fix the tests in the same batch, then run every test that references the script, run each moved script from its new location and every updated hook or target that can run locally. A failure stops the batch and is reported.
- Ambiguous script: leave it, list it as a blind spot.

## Wiring: propose, never do

Hand the human the block (the one exception is updating the references of a script the triage moved) for their detected platform, with `<scripts_path>` replaced by the resolved path. Do not edit the pipeline.

The blocks below go in the target project (its CI config), never in this skill.

**GitHub Actions** (in the target project)

```yaml
  guardrails:
    name: Guardrails
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: python <scripts_path>/check_no_todo.py backend/ frontend/src
      - run: python <scripts_path>/check_no_stub.py backend/ frontend/src
      - run: python <scripts_path>/check_monolith.py --file 400 --function 75 backend/
      - run: python <scripts_path>/check_forbidden_chars.py --chars dashes frontend/src
```

**GitLab CI** (in the target project)

```yaml
guardrails:
  image: python:3.12-slim
  script:
    - python <scripts_path>/check_no_todo.py backend/ frontend/src
    - python <scripts_path>/check_monolith.py --file 400 backend/
```

**pre-commit** (in the target project)

```yaml
  - repo: local
    hooks:
      - id: no-todo
        name: no deferral markers
        entry: python <scripts_path>/check_no_todo.py
        language: system
        pass_filenames: true
```

**Makefile / justfile** (in the target project)

```make
guardrails:
	python <scripts_path>/check_no_todo.py backend/ frontend/src
	python <scripts_path>/check_monolith.py --file 400 backend/
```

## Wire after clearing, never before

Run each checker against the repository **before** proposing the CI block, and report the current violation count.

If a checker fails today, wiring it makes the pipeline red on day one, and the reliable outcome is that someone disables the check rather than fixing the code. Order of operations:

1. Run the checker, count violations.
2. Zero violations: offer the CI block now.
3. Non-zero: record the count in the debt register with the resorption plan, and offer the CI block **for after** that work. Set `wired: false` in the config with the blocking count.

Observed instance: a forbidden-character rule adopted on a frontend carrying about 1,500 existing violations. Wiring it immediately would have blocked every merge; the correct sequence was rule, then debt entry, then resorption, then CI.

## Choosing thresholds

Never invent them. Derive from the repository:

```bash
git ls-files '*.py' | xargs wc -l | sort -rn | sed -n '2,20p'
```

Set the limit slightly above the current healthy majority so the check is meaningful without being immediately red, and record the value in `.claude/agents-md.yml`. A threshold that fails on half the codebase is not a guardrail, it is noise.

## Allowlists

`check_monolith.py --allowlist <file>` accepts a file of tolerated paths (one per line, `#` comments allowed). Use it for genuine legacy, and only with a resorption entry in the debt register.

Report the tolerated count on every run: an allowlist nobody looks at becomes permanent. An empty allowlist that stays empty is the goal.
