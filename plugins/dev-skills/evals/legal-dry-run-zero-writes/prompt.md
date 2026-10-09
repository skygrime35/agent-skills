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
Set up a fixture: a git repo with `package.json` (dependency "next-auth") and `app/(legal)/cgu/content.fr.mdx` containing "# CGU\nVersion 1.0". Without writing anything, tell me what you would do to bring my legal pages up to date: which documents are required, what you would ask me and what you would write.
