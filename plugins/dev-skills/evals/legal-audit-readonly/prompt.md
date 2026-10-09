---
max_turns: 30
allowed_tools:
  - Bash
  - Read
  - Write
  - Edit
  - Skill
  - AskUserQuestion
timeout_seconds: 600
---
Set up a tiny fixture first: create a git repo in the current directory with `package.json` (name "shop", dependency "stripe"), `src/checkout.js` containing a call to `stripe.checkout.sessions.create`, and `public/mentions.md` containing "Mentions légales - Éditeur : à définir". Then check whether my site's legal pages are in line with what the code does and tell me what is wrong. Do not change anything.
