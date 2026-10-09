#!/usr/bin/env bash
set -e
git init -q -b main
git config user.name "Eval User"
git config user.email "eval@example.com"
mkdir -p tests
cat > ping.py <<'PY'
import requests


def status():
    return requests.get('https://api.example-prod.com/status', timeout=5)
PY
cat > tests/test_ping.py <<'PY'
from ping import status


def test_status_live():
    resp = status()
    assert resp.status_code == 200
PY
printf '__pycache__/\n.pytest_cache/\n' > .gitignore
git add ping.py tests/test_ping.py .gitignore
git commit -q -m "Add ping script with live test"
