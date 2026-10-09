#!/usr/bin/env bash
set -e
git init -q -b main
git config user.name "Eval User"
git config user.email "eval@example.com"
mkdir existing-app
echo "do not lose me" > existing-app/keep.txt
git add existing-app/keep.txt
git commit -q -m "add existing app" 
