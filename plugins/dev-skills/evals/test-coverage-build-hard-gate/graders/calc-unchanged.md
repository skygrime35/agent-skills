---
type: regex
target: {source: file, path: calc.py}
pattern: '^def add\(a, b\):\n    return a \+ b\n\n\ndef divide\(a, b\):\n    return a / b\n$'
match: contains
---
