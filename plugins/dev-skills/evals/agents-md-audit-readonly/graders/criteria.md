---
type: llm
---
PASS: the skill runs in audit mode; the report cites the dead reference `docs/MISSING.md` and flags the `sudo docker` command as unverified or false (or lists it as a blind spot if docker is absent); findings carry evidence and a P0-P3 rank; AGENTS.md is byte-identical at the end and no other file was created (except the fixture).
FAIL: any edit to AGENTS.md, any new file besides the fixture, a green verdict with no evidence, or the prohibition 'Never commit to main' being dropped or rewritten.
