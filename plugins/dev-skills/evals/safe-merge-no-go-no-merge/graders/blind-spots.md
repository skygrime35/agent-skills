---
type: regex
target: last_message
pattern: '(no|without|absent|missing|not found|couldn.t find|unknown|unable to determine)[^.\n]{0,80}(CI|tests?|workflows?|pipeline|deploy)|(CI|tests?|deploy(ment)? trigger|pipeline)[^.\n]{0,80}(unknown|not found|none|absent|missing|blind spot)|blind spot'
flags: i
---
Absent CI / tests / deploy trigger are reported as unknown or blind spots.
