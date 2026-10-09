# claude-skills

Private Claude Code plugin marketplace holding personal skills.

## Install

```bash
claude plugin marketplace add skygrime35/claude-skills
claude plugin install dev-skills@skygrime
```

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

Edit in place, then:

```bash
claude plugin validate ./plugins/dev-skills && claude plugin validate .
claude plugin eval ./plugins/dev-skills   # runs evals/ (costs model calls)
```

Bump `version` in `plugins/dev-skills/.claude-plugin/plugin.json` so installed copies update.
