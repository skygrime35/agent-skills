---
type: regex
target: last_message
pattern: '((propos|chos|choos|select|pick|recommend|go with|use)\w*\s+(a\s+|the\s+)?tier[\s:]*(3|three)\b|\btier[\s]*[:=][\s*]*(3|three)\b)'
flags: i
match: not_contains
---
The plan does not select tier 3 for this tiny repository (mentioning tier 3 only to rule it out is fine).
