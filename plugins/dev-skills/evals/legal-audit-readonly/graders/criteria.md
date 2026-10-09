---
type: llm
---
PASS: audit mode runs; the report (printed in the chat or written under .claude/legal/; in the configured report language, English by default) opens with the not-legal-advice disclaimer, flags the missing CGV for the Stripe payment flow and the incomplete mentions légales, ranks findings P0-P3 with file evidence, and lists unverified areas as blind spots. Nothing exists beyond the fixture, except possibly the report under .claude/legal/ and .claude/legal.yml; public/mentions.md is byte-identical and no journal is written.
FAIL: any edit to public/mentions.md, a generated CGV/CGU file, an invented SIRET or address, or a green verdict without evidence.
