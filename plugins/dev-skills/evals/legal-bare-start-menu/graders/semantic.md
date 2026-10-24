---
type: llm
focus: last_message
criteria: |
  PASS: the answer shows the project's legal status (a CGU exists, no audit was ever run), recommends 2-3 next commands with a one-line reason each (an audit first), gives the recommended order of the workflow, and runs nothing yet.
  FAIL: the answer runs an audit or build, drafts legal text, or gives a static menu with no status of this project.
---
