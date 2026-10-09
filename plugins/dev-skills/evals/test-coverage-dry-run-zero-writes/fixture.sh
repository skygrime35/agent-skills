#!/usr/bin/env bash
set -e
git init -q -b main
git config user.name "Eval User"
git config user.email "eval@example.com"
mkdir -p tests
cat > app.py <<'PY'
from flask import Flask, jsonify, request

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    if data.get("user") == "admin" and data.get("password") == "secret":
        return jsonify(token="abc123")
    return jsonify(error="invalid credentials"), 401
PY
cat > tests/test_health.py <<'PY'
from app import app


def test_health():
    client = app.test_client()
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}
PY
printf '__pycache__/\n.pytest_cache/\n' > .gitignore
git add app.py tests/test_health.py .gitignore
git commit -q -m "Add Flask app with health test"
