# Guardrail scripts: generating and wiring

A rule nobody checks decays. These scripts turn written prohibitions into mechanical ones.

They live in `scripts/` of this skill and are **copied into the target project** (default `scripts/`, or wherever that project keeps its tooling). Pure standard library, no dependency, exit 1 on violation.

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

Hand the human the block for their detected platform. Do not edit the pipeline.

**GitHub Actions**

```yaml
  guardrails:
    name: Guardrails
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: python scripts/check_no_todo.py backend/ frontend/src
      - run: python scripts/check_no_stub.py backend/ frontend/src
      - run: python scripts/check_monolith.py --file 400 --function 75 backend/
      - run: python scripts/check_forbidden_chars.py --chars dashes frontend/src
```

**GitLab CI**

```yaml
guardrails:
  image: python:3.12-slim
  script:
    - python scripts/check_no_todo.py backend/ frontend/src
    - python scripts/check_monolith.py --file 400 backend/
```

**pre-commit**

```yaml
  - repo: local
    hooks:
      - id: no-todo
        name: no deferral markers
        entry: python scripts/check_no_todo.py
        language: system
        pass_filenames: true
```

**Makefile / justfile**

```make
guardrails:
	python scripts/check_no_todo.py backend/ frontend/src
	python scripts/check_monolith.py --file 400 backend/
```

## Wire after clearing, never before

Run each checker against the repository **before** proposing the CI block, and report the current violation count.

If a checker fails today, wiring it makes the pipeline red on day one, and the reliable outcome is that someone disables the check rather than fixing the code. Order of operations:

1. Run the checker, count violations.
2. Zero violations: offer the CI block now.
3. Non-zero: record the count in the debt register with the resorption plan, and offer the CI block **for after** that work. Set `wired: false` in the config with the blocking count.

Observed instance: a forbidden-character rule adopted on a frontend carrying 1 524 existing violations. Wiring it immediately would have blocked every merge; the correct sequence was rule, then debt entry, then resorption, then CI.

## Choosing thresholds

Never invent them. Derive from the repository:

```bash
git ls-files '*.py' | xargs wc -l | sort -rn | sed -n '2,20p'
```

Set the limit slightly above the current healthy majority so the check is meaningful without being immediately red, and record the value in `.claude/agents-md.yml`. A threshold that fails on half the codebase is not a guardrail, it is noise.

## Allowlists

`check_monolith.py --allowlist <file>` accepts a file of tolerated paths (one per line, `#` comments allowed). Use it for genuine legacy, and only with a resorption entry in the debt register.

Report the tolerated count on every run: an allowlist nobody looks at becomes permanent. An empty allowlist that stays empty is the goal.
