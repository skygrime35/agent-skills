#!/usr/bin/env bash
set -e
git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
mkdir -p src
cat > package.json <<'EOT'
{
  "name": "demo",
  "scripts": { "test": "echo ok" }
}
EOT
echo 'console.log("demo");' > src/index.js
git add package.json src/index.js
git commit -q -m "Initial commit"
