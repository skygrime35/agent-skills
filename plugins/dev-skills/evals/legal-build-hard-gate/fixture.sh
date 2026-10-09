#!/bin/bash
set -e
git init -q
git config user.name "Test User"
git config user.email "test@example.com"
mkdir -p "app/(legal)/cgv"
printf '%s\n' '{"name": "shop", "dependencies": {"stripe": "^16.0.0"}}' > package.json
printf '%s\n' '# CGV' 'Version 1.0' 'Médiateur : XYZ' > "app/(legal)/cgv/content.fr.mdx"
printf '%s\n' 'bump the version in the mdx header on every change' > legal-versioning.md
git add package.json "app/(legal)/cgv/content.fr.mdx" legal-versioning.md
git commit -q -m "Initial commit"
