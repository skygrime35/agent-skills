# claude-skills

Private Claude Code plugin marketplace holding personal skills.

## Install

```bash
claude plugin marketplace add skygrime35/claude-skills
claude plugin install dev-skills@skygrime
```

Restart running Claude Code sessions after installing or updating: a session does not load a plugin installed while it runs.

Skills are then available as `/dev-skills:<skill>` (and by their short name when unambiguous). Defaults are plugin options: change them in `/config`.

## Skills (`plugins/dev-skills/skills/`)

| Skill | Purpose |
|---|---|
| agents-md | Create, audit or repair a project's agentic docs (AGENTS.md, CLAUDE.md pointer, domain docs, ADRs, guardrail scripts) |
| orchestration | Create, audit or sync the agent-orchestration layer: model ladder, delegation, parallelism under isolation, subagent types |
| test-coverage | Grow a test suite toward full-scenario coverage; speed it up without losing a test |
| full-test | Run the full test battery against preprod, with an optional autonomous fix loop |
| safe-merge | Gate a merge into the production branch: backups, migration rehearsal, tests, changelog, go/no-go |
| legal | Audit, build or verify French/EU legal texts (CGU, CGV, legal notices, privacy, cookies, giveaways) |
| new-project | Take an idea to a finished, deployed, pushed project |

## Develop

Always edit this clone, never the installed copy in `~/.claude/plugins/cache/` (it is replaced on every update).

1. Edit the skill in `plugins/dev-skills/skills/<skill>/` (keep everything in English).
2. New or changed default: add or edit the option under `userConfig` in `plugins/dev-skills/.claude-plugin/plugin.json`, then reference it in SKILL.md as `${user_config.<key>}`. Substitution only happens in SKILL.md, never in `references/` or scripts; `${CLAUDE_SKILL_DIR}` behaves the same way.
3. Add or update an eval case in `plugins/dev-skills/evals/<skill>-<case>/` (`prompt.md`, `case.yaml` with `context.scaffold_script: fixture.sh`, `graders/`). Prefer deterministic graders (`tool_used`, `file_exists`, `regex`) over `llm`.
4. Check:
   ```bash
   claude plugin validate ./plugins/dev-skills && claude plugin validate .
   claude plugin eval ./plugins/dev-skills --scaffold --judge-model sonnet   # costs model calls
   ```
   Run a single case by pointing at its directory. The eval sandbox needs `bubblewrap` and, on Ubuntu 24.04, the AppArmor profile `/etc/apparmor.d/bwrap` granting `userns`.
5. Bump `version` in `plugins/dev-skills/.claude-plugin/plugin.json`, commit, push.
6. Update the installed copy, then restart Claude Code sessions:
   ```bash
   claude plugin marketplace update skygrime && claude plugin update dev-skills@skygrime
   ```
