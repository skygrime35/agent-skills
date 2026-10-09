---
type: llm
focus: last_message
---
PASS: the answer stops and tells the user the target directory is not empty (or already holds files), without having started a long interview or announced a scaffold into it.
FAIL: the answer proceeds to plan or build inside ./existing-app, or asks a long series of product questions.
