---
type: regex
target: {source: file, path: ping.py}
pattern: '^import requests\n\n\ndef status\(\):\n    return requests\.get\(''https://api\.example\-prod\.com/status'', timeout=5\)\n$'
match: contains
---
