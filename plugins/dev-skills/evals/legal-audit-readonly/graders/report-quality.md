---
type: llm
focus: last_message
criteria: |
  PASS: the answer is a legal audit report that ranks the missing CGV (terms of sale, needed because of the Stripe payment flow) at P0 or P1, i.e. among the most severe findings, and cites file evidence such as src/checkout.js or public/mentions.md.
  FAIL: the CGV gap is absent or ranked below P2, or no finding cites a file, or the answer only asks questions without a report.
---
