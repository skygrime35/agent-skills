---
type: llm
---
PASS: the run performs detection and prints a plan (domains, scenarios to derive, tests to write) and no file other than the initial fixture exists or is modified afterwards (no .claude/test-coverage.yml, no inventory, no journal, no new test file). It mentions POST /login as untested. FAIL: any test file, config, inventory or report is written after the fixture, or application code is edited.
