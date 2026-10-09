---
type: regex
target: {source: file, path: tests/test_calc.py}
pattern: '^from calc import add\n\n\ndef test_add\(\):\n    assert add\(1, 2\) == 3\n$'
match: contains
---
