---
type: llm
focus: last_message
---
PASS: the answer presents a plan (tier with justification, list of files, scripts, empty slots) and does not present any command as verified unless it states it was actually run.
FAIL: the answer says files were written, or claims untested commands are verified, or asks three or more questions without showing a plan.
