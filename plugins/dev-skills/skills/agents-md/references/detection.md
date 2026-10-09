# Detection: measuring an unknown repository

Everything the skill must learn before it can write anything. The probes are independent: fan them out.

**Output rule, absolute:** each probe yields either a verified fact or an explicit unknown. An unknown becomes a question to the human or an empty slot with a note. It never becomes a plausible-sounding sentence.

## 1. Languages and manifests

```bash
git ls-files | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -20
ls package.json pyproject.toml Cargo.toml go.mod pom.xml Gemfile composer.json 2>/dev/null
```

Record: dominant languages by file count, package managers (from the lockfile, not the manifest), pinned runtime versions.

## 2. Real commands (never guessed)

The single highest-value probe. Extract, never invent.

| Source | What to pull |
|---|---|
| `package.json` `scripts` | test, build, lint, typecheck, dev |
| `pyproject.toml` | tool configs, entry points, declared scopes |
| `Makefile`, `justfile`, `Taskfile.yml` | the targets the team actually types |
| CI workflow files | **the authoritative list**: what runs on every push, with exact flags and scope |
| `.pre-commit-config.yaml` | the checks already enforced |

CI is the best source because those commands demonstrably run. Pull the exact invocation including scope: `mypy apps/a apps/b config` is a fact, `mypy .` is a guess.

**Then execute each one.** A command that fails is not documented as if it worked. Note whether a container wrapper is needed, and whether privilege escalation is genuinely required:

```bash
docker ps >/dev/null 2>&1 && echo "docker works unprivileged"
```

A documented `sudo` that is not needed causes permission prompts and root-owned files in the tree. This exact defect survived months in a production project's most-trusted file.

## 3. Domain boundaries (drives the tier)

A domain is a directory with its **own dependency manifest, its own conventions, and its own test command**. A directory that merely groups files is not a domain.

```bash
find . -maxdepth 3 -name 'package.json' -o -maxdepth 3 -name 'pyproject.toml' \
  | grep -v node_modules | grep -v '^\./package.json$'
```

Two or more genuine domains points to tier 3, one domain plus real volume to tier 2.

## 4. Branch-to-environment mapping

Needed for the branch-discipline rule, and it is the probe most often got wrong.

**Do not read the trigger and stop.** The trigger says when a workflow runs, not what it deploys. A catch-all trigger with the routing hidden in a job conditional is common:

```yaml
on: { push: { branches: ["**"] } }
jobs:
  deploy:
    runs-on: ${{ github.ref_name == 'main' && fromJSON('[...prod]') || fromJSON('[...preprod]') }}
```

Read the whole job: `runs-on`, `if:`, `concurrency.group`, the environment or compose project it computes, the argument finally passed to the deploy script.

| Platform | Files | Where the mapping hides |
|---|---|---|
| GitHub Actions | `.github/workflows/*.yml` | conditionals on `github.ref_name` inside jobs |
| GitLab CI | `.gitlab-ci.yml` | `rules:`/`only:`, `environment.name` |
| CircleCI | `.circleci/config.yml` | `filters.branches` |
| Jenkins | `Jenkinsfile` | `when { branch }` |
| Platform-side | `vercel.json`, `netlify.toml`, `render.yaml`, `fly.toml` | often nowhere in the repo |

If the repository holds no evidence, **ask**. Guessing "main is production" is usually right and occasionally catastrophic, which is precisely the wrong trade.

Also resolve the default branch, and confirm every branch cited anywhere in existing documentation still exists:

```bash
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|.*/||'
git branch -a --list '<cited-branch>'
```

## 5. Commit conventions

```bash
git log --format='%s' -100 | grep -cE '^(feat|fix|docs|refactor|chore|perf|test)(\(.+\))?:'
git log --format='%s' -100 | grep -oE '^[a-z]+\(([^)]+)\)' | sed 's/.*(//' | sort | uniq -c | sort -rn
```

Above roughly 70 percent matching, Conventional Commits is in force: document it with the real scope list. Below, do not invent a convention the project does not have.

## 6. Prose language

```bash
git log --format='%s' -100 | grep -icP '[éèêàçùôîûñäöüß]'
```

Combine with a scan of existing docs and code comments. Detection informs the question; it does not settle it. **If the repository states a language rule for documentation, that rule wins over the default and must be surfaced, not silently overridden.**

## 7. Existing quality tooling

```bash
ls .github/workflows/ .pre-commit-config.yaml .editorconfig 2>/dev/null
ls scripts/ tools/ bin/ 2>/dev/null | head -30
```

Look for checks the project already enforces (lint, types, architecture, i18n parity, custom AST scripts). Two purposes: document them as existing guardrails, and avoid generating a checker that duplicates one already there.

## 8. Existing agentic documentation

```bash
ls AGENTS.md CLAUDE.md .cursorrules .github/copilot-instructions.md 2>/dev/null
find . -name 'AGENTS.md' -not -path '*/node_modules/*' | head -20
ls AGENTS/ docs/agents/ 2>/dev/null
```

Anything found sends `init` to `audit`. Also detect a knowledge graph (`graphify-out/`, `.graph.json`) and, if present, its build commit against HEAD.

## 9. Size and history

```bash
git ls-files | wc -l
git ls-files -z | xargs -0 wc -l 2>/dev/null | tail -1
git log --format='%an' | sort -u | wc -l
git log -1 --format='%cr'
```

LOC and file count drive the tier. Author count drives whether concurrency rules matter (they always do where agents are involved, even solo).

## Profile handed to the writing phases

```yaml
languages: [{name, files, share}]
package_managers: []
commands:                      # every entry executed, with its result
  test: {cmd, verified: true|false, note}
  lint: {...}
  build: {...}
  typecheck: {...}
domains: [{path, manifest, own_tests}]
environments: {prod_branch, preprod_rule, platform, evidence}
commit_convention: {enforced, scopes[]}
language: {detected, conflict_with_repo_rule}
existing_tooling: []
existing_docs: []
size: {files, loc, authors}
unknowns: []                   # everything that becomes a question or an empty slot
```

`unknowns` is never empty on a real repository. A run that reports zero unknowns has guessed somewhere.
