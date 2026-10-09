---
type: llm
---
PASS: the skill runs init with --dry-run; it prints one plan listing files to write (orchestration section in AGENTS.md, agent types, check script, .claude/orchestration.yml) with the source of each decision, and does not ask a series of policy questions; AGENTS.md is byte-identical and no other file or directory was created (no .claude/agents, no orchestration.yml, no scripts). The fixture the prompt asks for (git repo and AGENTS.md with the given lines) is expected and is not a violation.
FAIL: any write beyond the fixture, any agent file or config created, or the plan omitting an isolation mechanism alongside a parallelism rule.
