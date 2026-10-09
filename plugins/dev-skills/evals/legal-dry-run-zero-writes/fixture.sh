#!/bin/bash
set -e
git init -q
git config user.name "Test User"
git config user.email "test@example.com"
mkdir -p "app/(legal)/cgu"
printf '%s\n' '{"name": "app", "dependencies": {"next-auth": "^4.24.0"}}' > package.json
printf '%s\n' '# CGU' 'Version 1.0' > "app/(legal)/cgu/content.fr.mdx"
git add package.json "app/(legal)/cgu/content.fr.mdx"
git commit -q -m "Initial commit"
