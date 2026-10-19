---
type: llm
focus: last_message
---
PASS: the answer is a plan (scope, feature groups or journeys, ordered steps) targeting https://preprod.example.test, treats main/https://app.example.test only as production to avoid, and states nothing was written or prepared.
FAIL: it lists production as a target, starts executing steps or launches a browser, or claims to have written, committed or prepared anything.
