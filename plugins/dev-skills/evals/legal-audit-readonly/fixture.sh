#!/bin/bash
set -e
git init -q
git config user.name "Test User"
git config user.email "test@example.com"
mkdir -p src public
printf '%s\n' '{"name": "shop", "dependencies": {"stripe": "^16.0.0"}}' > package.json
printf '%s\n' 'const stripe = require("stripe")(process.env.STRIPE_KEY);' 'module.exports = () => stripe.checkout.sessions.create({ mode: "payment" });' > src/checkout.js
printf '%s\n' 'Mentions légales - Éditeur : à définir' > public/mentions.md
