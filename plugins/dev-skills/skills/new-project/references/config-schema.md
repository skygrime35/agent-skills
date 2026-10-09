# Learned tastes and options

Contents: learned-tastes file, plugin options, enrichment rules.

## Where settings live

- **Plugin options** (`${user_config.<KEY>}`) hold every policy default: UI language, docs language, look and feel baseline, privacy default, auto-name, host domain pattern, port range, deploy host, hosting toggle, disk floor, agents fallback. They are the autonomy levers.
- **`~/.claude/new-project.yml`** is only the **learned-tastes file** (stacks, license, conventions, quirks, projects directory, identity). It lives at user level because the project does not exist yet when it is needed. Missing file = first run: matrix defaults, file created at Phase 6. Resolution order: command argument > this file > plugin option > recommended default.

## Plugin options used by the skill

| Option | Default | Used for |
|---|---|---|
| `new_project_ui_language` | English | language of questions and reports |
| `new_project_docs_language` | English | README and human-facing docs (code stays English) |
| `new_project_look_and_feel` | clean, sober, modern | baseline when the user gives no reference apps |
| `new_project_privacy_default` | basic-auth | `basic-auth` or `open` for the vhost when data is private and no in-app auth exists |
| `new_project_auto_name` | false | use the recommended name without waiting for a choice |
| `new_project_host_domain_pattern` | `<dashed-ip>.nip.io` | base domain of `<project>.<base>`; a real wildcard domain takes precedence |
| `new_project_port_range_start` / `_end` | 6400 / 6499 | loopback ports reserved for deployments |
| `new_project_deploy_host` | localhost VPS | where the app is hosted (only the local VPS is implemented; anything else = `--no-host` plus a blind spot) |
| `new_project_hosting_enabled` | `true` (boolean) | `false` makes every run behave as `--no-host` by default; `--no-host` still applies when `true` |
| `new_project_min_disk_gb` | 3 | free-disk floor, passed to the script as `NP_MIN_DISK_GB` |
| `new_project_agents_fallback` | model-parameter | when dedicated agent types are missing: `model-parameter` uses the Agent tool's `model` argument with session-default effort; `main-loop` runs every package inline |

## Learned-tastes schema

```yaml
# ~/.claude/new-project.yml: learned tastes for /new-project. Enriched after each confirmed run.
identity:
  author: ""              # LICENSE / package metadata
  github_user: ""         # detected from `gh auth status` on first run
  default_license: MIT

projects_dir: ~/projects  # default parent for new projects
registry: ~/.claude/new-project-deployments.yml

stacks:                   # per-type overrides of the matrix in stacks.md; empty = matrix default
  web-app: ""
  api: ""
  cli: ""
  tui: ""
  library: ""
  static-site: ""
  bot-worker: ""
  browser-ext: ""

conventions:              # free-form lines injected into every spec, human-authored
  - ""

quirks: []                # human-authored notes the skill must respect but never rewrite
```

## Enrichment rules (Phase 6, after a GO'd run)

1. Only **confirmed** choices are written back (a stack validated at Checkpoint 1 and not regretted at the live checkpoint, an accepted license, the resolved `github_user`).
2. **Show the diff before writing.** Never rewrite `conventions` or `quirks` (human-authored); propose additions only.
3. A run's choice becomes a default, not a law: the spec states which preferences were applied.
4. Secrets never belong in this file: env var names at most, never values.
