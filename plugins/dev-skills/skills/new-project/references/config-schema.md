# `~/.claude/new-project.yml` — user-level preferences

Lives at **user level**, not project level (the project doesn't exist yet when it's needed). Missing file = first run: use matrix defaults, create the file at Phase 6. This file is the main lever of "minimum user time": by the third project the interview and the stack question mostly disappear.

## Schema

```yaml
# ~/.claude/new-project.yml — preferences for /new-project. Enriched after each confirmed run.
identity:
  author: ""              # goes into LICENSE / package metadata
  github_user: ""         # detected from `gh auth status` on first run
  default_license: MIT
  docs_language: fr       # language for README and human-facing docs (code stays English)

projects_dir: ~/projects  # default parent for new projects

defaults:
  repo_visibility: private
  ci: github-actions

hosting:
  enabled: true           # false = behave as --no-host by default
  base_domain: ""         # e.g. "apps.example.com" (wildcard DNS) — empty = <dashed-public-ip>.nip.io
  port_range: [6400, 6499] # loopback ports reserved for this skill's deployments; collision-checked against the live host
  registry: ~/.claude/new-project-deployments.yml

stacks:                   # per-type overrides of the matrix in stacks.md
  web-app: ""             # e.g. "nextjs" — empty = matrix default
  api: ""
  cli: ""
  tui: ""
  library: ""
  static-site: ""
  bot-worker: ""
  browser-ext: ""

conventions:              # free-form lines injected into every spec, human-authored
  - ""                    # e.g. "commit messages in English", "UI copy in French"

quirks: []                # human-authored notes the skill must respect but never rewrite
```

## Enrichment rules (Phase 6, after a GO'd run)

1. Only **confirmed** choices are written back — a stack the user validated at Checkpoint 1 and didn't regret at the live checkpoint, a license they accepted, the resolved `github_user`.
2. **Show the diff before writing.** Never silently rewrite `conventions` or `quirks` — those are human-authored; propose additions, don't edit existing lines.
3. One run's choice becomes a *default*, not a law: the spec at Checkpoint 1 always states which preferences were applied, so overriding stays a one-comment correction.
4. Secrets never belong in this file — env var **names** at most, never values.
