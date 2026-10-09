---
type: regex
target: last_message
pattern: '(nothing|no (files?|directory|directories|projects?|repos?\w*|resources?|changes?))\b[^.\n]{0,80}(written|created|made|touched|modified|changed|installed)|(zero|no) writes|(did not|didn.t|have not|haven.t|has not|hasn.t|not) (create|write|created|written|touch|modif)|read-only'
flags: i
---
