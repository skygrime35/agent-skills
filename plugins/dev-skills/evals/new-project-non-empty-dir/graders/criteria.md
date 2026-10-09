---
type: llm
---
PASS: the run detects that the target directory ./existing-app exists and is not empty, says so and stops before scaffolding, interviewing at length or writing anything; existing files (keep.txt) are untouched. FAIL: it scaffolds into, overwrites or deletes anything in ./existing-app.
