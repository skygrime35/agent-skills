#!/usr/bin/env bash
set -e
git init -q -b main
git config user.name "Eval User"
git config user.email "eval@example.com"
mkdir -p tests
cat > calc.py <<'PY'
def add(a, b):
    return a + b


def divide(a, b):
    return a / b
PY
cat > tests/test_calc.py <<'PY'
from calc import add


def test_add():
    assert add(1, 2) == 3
PY
printf '__pycache__/\n.pytest_cache/\n' > .gitignore
git add calc.py tests/test_calc.py .gitignore
git commit -q -m "Add calc module with add test"
