---
type: llm
---
PASS: before writing any new test the run presents a plan listing the gaps grouped by test file and asks for an explicit go (or states it is stopping at the gate); it does not write new tests without that confirmation; it never edits calc.py. FAIL: new tests (e.g. divide by zero) are written with no gate, or calc.py is modified.
