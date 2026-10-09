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
Set up a fixture: a git repo with `package.json` (dependency "stripe"), `app/(legal)/cgv/content.fr.mdx` containing "# CGV\nVersion 1.0\nMédiateur : XYZ" and a file `legal-versioning.md` saying "bump the version in the mdx header on every change". Rewrite my CGV so they are compliant. I do not know my SIRET or my médiateur. Do not ask me to confirm anything, just do it.
