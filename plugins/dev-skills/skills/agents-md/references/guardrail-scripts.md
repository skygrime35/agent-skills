# Guardrail scripts: generating and wiring

Contents: The four checkers - Wiring: propose, never do - Wire after clearing, never before - Choosing thresholds - Allowlists

A rule nobody checks decays. These scripts turn written prohibitions into mechanical ones.

They live in `${CLAUDE_SKILL_DIR}/scripts/` and are **copied into the target project** at `<scripts_path>` (resolution in SKILL.md: argument > `guardrail_scripts_path` in config > `user_config.agents_md_guardrail_scripts_path` > tracked-checkers exception > `.claude/agents-md/`), e.g. `cp ${CLAUDE_SKILL_DIR}/scripts/check_{no_todo,monolith,no_stub,forbidden_chars}.py <target>/<scripts_path>` (not `check_dead_paths.py` / `check_sections.py`, which are audit-only). Pure standard library, no dependency, exit 1 on violation.

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

## Wiring: propose, never do

Hand the human the block for their detected platform, with `<scripts_path>` replaced by the resolved path. Do not edit the pipeline.

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
