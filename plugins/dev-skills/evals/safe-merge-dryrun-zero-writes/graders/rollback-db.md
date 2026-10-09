---
type: regex
target: last_message
pattern: '(database|DB\b|data|schema|column|migration)[^.\n]{0,200}(roll.?back|revert|restor|recover|undo|reverse)|(roll.?back|revert|restor|recover|undo|reverse)[^.\n]{0,200}(database|DB\b|data|schema|column|migration)'
flags: i
---
The report states that a code-only rollback does not restore the database.
