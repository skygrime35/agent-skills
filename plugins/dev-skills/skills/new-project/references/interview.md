# Deep discovery interview — funnel, functional only

Goal: extract the user's **real expectations** before a single line of code. A wrong expectation caught on the live app costs a full build loop; caught here it costs one tick. The interview is a **funnel**: it starts very general and each round gets more precise, shaped by the previous answers. Full autonomy starts after the spec GO, not before.

## The two iron rules

1. **Functional only — never technical.** No question about stack, framework, database, hosting mechanics, architecture or auth implementation. The tech is **the skill's job** (Phase 2), chosen to fit the answers and justified at Checkpoint 1 where the user can still veto it. Every technical decision the skill needs is obtained by translating it into a functional question:
   - not "JWT or sessions?" → "Do people sign in with an account, or is it open?"
   - not "PostgreSQL or SQLite?" → "Should things you enter still be there next time, from another device too?"
   - not "SSR for SEO?" → "Should strangers find it via Google, or is it just for you/your team?"
   - not "which CSS framework?" → "Show me an app whose look you'd want as a cousin of this one."
   Plain language throughout — zero jargon in the questions and options.
   **The one sanctioned exception: the target medium.** "Should this be a website you open in the browser, a mobile app, a desktop program, or a command-line tool?" — asked plainly in Round 1 (with a recommended default inferred from the idea), because it shapes everything and the user genuinely owns that expectation. Everything *below* the medium — language, framework, storage, hosting — remains the skill's call.
2. **General → precise.** Each round narrows: vision → usage → features one by one → fine behaviors. Never open with details; never end without them.

## Form

- **AskUserQuestion salvos**, max 4 questions each, never one-at-a-time dripping.
- Options **concrete and opinionated**, "(Recommended)" default, `multiSelect` where choices aren't exclusive — answering is ticking; "Other" always allows free text.
- **Adaptive**: skip what the input, `--spec` or the learned-tastes file or plugin options already answers; dig where an answer reveals complexity ("several people use it" → next round asks who can see/change what, in functional terms).

## The funnel

**Round 1 — Very general (the why).** What is it, in one sentence? For whom (just you / your team / the public)? What problem does it kill? The **target medium** (website / mobile app / desktop program / command-line tool — the sanctioned exception, with a recommended default inferred from the idea). And the anchor: **"what would make you say: this is exactly what I wanted?"** — the answer becomes the spec's success criterion and arbitrates every later trade-off.

**Round 2 — Usage (the when/how).** Walk the killer scenario step by step ("you open it — then what?"). How often is it used, in what context (at a desk, on the go, in a hurry)? Alone or with others at the same time? What exists today instead (Excel, notes, nothing) and what's unbearable about it?

**Round 3 — Feature inventory (the what).** Must-haves as a multiSelect of plausible features *inferred from rounds 1–2* — the user ticks. Explicit out-of-scope: "what would be wasted effort?"

**Round 3b — Per-feature deep dive (the most important rounds).** For **each** ticked must-have, dig until its behavior is unambiguous — grouped salvos, one feature (or two small related ones) per salvo, as many salvos as the features demand. Per feature, cover in functional terms:
- **Trigger & flow**: how does it start, what does the user see, what happens next ("you add a recipe: by typing it, pasting a link, taking a photo — which ones?");
- **Content**: what exactly is captured/shown, which parts are mandatory ("a recipe here = ingredients + steps? photos? portions? time?");
- **Variants & limits**: the second-most-common path, quantities ("dozens or thousands?"), what's deliberately NOT handled;
- **Empty, error and edge states**: first use with nothing in it, bad input, the thing referenced no longer exists ("a planned meal whose recipe you deleted — what should happen?");
- **The acceptance line**: close each feature with a reformulation the user confirms — "so: <precise behavior>, and it's done when <observable outcome>. Right?"
**A feature is specified when its acceptance test could be written from the answers alone.** These confirmed acceptance criteria go verbatim into the spec and become the DoD's per-must-have tests.

**Round 4 — Fine behaviors & taste (the exactly-how).** The precise end of the funnel, still functional: look & feel via reference apps ("sober like Notion / dense like a trading dashboard / playful?"); UI language; phone, computer or both; do entered things persist and follow the user across devices; is any of the data private or sensitive; who may see or change what; should the hosted app be shareable with someone else to try.

## Stop criterion

Stop when a new question **would no longer change what gets built**. The general rounds (1, 2, 4) are one salvo each; Round 3b takes **as many salvos as the must-haves demand** — depth there is the point, not a cost. A typical run lands between 3 and 7 salvos total. Never re-ask what is known; never ask what the skill decides itself. Whatever remains unknown becomes an **explicit assumption** in `SPECS.md`, corrected at Checkpoint 1 for the cost of one comment.

## `--quick`

One salvo only (the most general four questions), everything else becomes assumptions — for throwaway experiments where the spec checkpoint is safety net enough.

## Output: the brief

```markdown
## Brief
- **Objective:** <one sentence>
- **Success criterion:** <the user's own words from Round 1>
- **Users:** <who, how many, alone/together>
- **Usage context:** <frequency, device, situation>
- **Must-have:** <numbered; each one a mini-spec from Round 3b: trigger & flow, content, variants & limits, empty/error states, and its user-confirmed **acceptance criteria** — these become the DoD's tests>
- **Killer scenario:** <the walked-through flow>
- **Out of scope:** <explicit, from Round 3>
- **Look & feel:** <style + reference apps>
- **Data expectations:** <what persists, follows across devices, privacy/sensitivity, who sees what — functional terms>
- **Hosting expectations:** <shareable or not, wipeable data>
- **Assumptions:** <everything guessed, one line each — corrected at Checkpoint 1>
```

The skill then derives **every** technical choice (type, stack, auth, storage, hosting form) from this brief in Phase 2 — and presents them at Checkpoint 1 with a one-paragraph rationale linking each choice back to an answer.
