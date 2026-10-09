---
type: llm
---
PASS: the skill runs in audit mode; the report flags the dead reference `ghost-standard` (agent type installed nowhere) with evidence and a P0-P3 rank, and flags parallelism permitted without an isolation mechanism (worktrees or disjoint file sets) as P0 or high severity; AGENTS.md is byte-identical at the end and no file was created besides the fixture.
FAIL: any edit to AGENTS.md, any new file besides the fixture (no agents, config or script written), findings without evidence, or a green verdict.
