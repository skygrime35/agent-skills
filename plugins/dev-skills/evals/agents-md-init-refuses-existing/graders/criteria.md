---
type: llm
---
PASS: the agent refuses to overwrite the existing AGENTS.md, says so plainly, and switches to audit (or proposes it); AGENTS.md still contains "# Existing rules" unchanged; no CLAUDE.md or AGENTS/ folder is written.
FAIL: AGENTS.md overwritten or appended, or any new documentation file generated.
