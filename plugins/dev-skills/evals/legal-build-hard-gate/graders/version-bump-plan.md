---
type: regex
target: last_message
pattern: '(version|v)[\s:*]*1\.0[\s\S]{0,200}(1\.1|2\.0|bump)|1\.0\s*(→|->|becomes|to)\s*v?(1\.1|2\.0)|bump[\s\S]{0,200}version'
flags: i
---
