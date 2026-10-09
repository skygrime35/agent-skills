---
type: regex
target: last_message
pattern: '(purg|remov|scrub|rewrite|clean|filter)[^.\n]{0,120}(history|commit|branch)|(history|commit)[^.\n]{0,120}(purg|remov|scrub|rewrit|clean)|rotate|revoke'
flags: i
---
The answer says the secret must be purged from history (and rotated) first.
