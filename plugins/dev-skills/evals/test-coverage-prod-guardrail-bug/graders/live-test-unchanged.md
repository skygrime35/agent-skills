---
type: regex
target: {source: file, path: tests/test_ping.py}
pattern: '^from ping import status\n\n\ndef test_status_live\(\):\n    resp = status\(\)\n    assert resp\.status_code == 200\n$'
match: contains
---
