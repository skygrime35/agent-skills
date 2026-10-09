---
type: regex
target: {source: file, path: tests/test_health.py}
pattern: '^from app import app\n\n\ndef test_health\(\):\n    client = app\.test_client\(\)\n    resp = client\.get\("/health"\)\n    assert resp\.status_code == 200\n    assert resp\.get_json\(\) == \{"status": "ok"\}\n$'
match: contains
---
