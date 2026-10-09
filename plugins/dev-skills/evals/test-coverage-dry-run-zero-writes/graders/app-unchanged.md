---
type: regex
target: {source: file, path: app.py}
pattern: '^from flask import Flask, jsonify, request\n\napp = Flask\(__name__\)\n\n\n@app\.get\("/health"\)\ndef health\(\):\n    return jsonify\(status="ok"\)\n\n\n@app\.post\("/login"\)\ndef login\(\):\n    data = request\.get_json\(silent=True\) or \{\}\n    if data\.get\("user"\) == "admin" and data\.get\("password"\) == "secret":\n        return jsonify\(token="abc123"\)\n    return jsonify\(error="invalid credentials"\), 401\n$'
match: contains
---
