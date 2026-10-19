# Guided step format

Phase 3. The tester reads on a phone or between tasks: every step is short.

## Rules

- **One step per message.** 1 to 3 actions at most. More actions => split into two steps.
- **Single global numbering.** Steps are numbered once for the whole run (`Step <n>/<total>`), the numbering is stored in `state.json` and group-local numbers are never shown. A dropped, merged or reordered step keeps the numbers of the others and `total` is updated. A step validated by another is recorded `validated as a side effect of step <n>`.
- Fixed layout: header `Step <n>/<total> - <feature>` (plus device tag when relevant), **Link** (absolute URL with locale, clickable), **Do** (numbered actions, exact UI labels as displayed), **Expected** (the precise result: text, count, state, position), **Send back** (the evidence: screenshot, yes/no, a value).
- Chat language per `user_config.manual_test_language`; UI labels quoted exactly as on screen. No jargon, no internal identifiers unless the tester must type them.
- **Login steps are self-contained.** A step that logs in with a test account the skill created, or one the project config declares as a test account on the non-production target, gives the exact identifier the login form accepts (read the form code: the email if it takes an email, never a username it rejects) and the full password, in that same step; never "same as above". For the tester's own account, never write a password: "log in with your own account (<identifier>)". Passwords are never written to notes or `state.json` (`scoping.md` § 4).
- **Form values.** Give the exact value for every required field and every field under test; an optional field is either "leave empty" or given a value; do not list irrelevant fields. When a form is exercised several ways, one labelled value set per variant (the one that must fail, the one that must succeed). Record the value set used in `state.json` `values` (no secrets).
- **Grounded expectations.** Each Expected comes from the component code (label, condition, element type), never from the feature's purpose. A conditional result says so ("appears only if ...") or the condition is checked against the prepared data before the step is sent. Overridable values are handled per `analysis.md` § Verification.
- **Links as the app builds them.** Build URLs from the app's own link builders (grep the frontend: uuid vs numeric id, slug, locale prefix), then verify the target entity exists (API or DB read on the non-production target) and that the status is the expected one for the route: protected pages answer 302/401, client-routed pages often answer 200 even for a missing entity, so a bare status check is necessary but not sufficient. A browser automation tool, when available, may replace the check. Fix a failing link before the tester sees it.
- **Asynchronous triggers.** For a step waiting on an event the agent triggers (push, email, webhook, scheduled task), state the server-side trigger time and the expected delay ("sent at 15:02:10, expect it within 30 s") and offer to re-trigger if the tester missed it.
- **Static content** (texts, translations, versions, static assets) is read by the agent and recorded `verified by agent` (G8); the tester only does the light on-screen check of G8.
- Before sending: check the preconditions (served SHA, flag on, data prepared). If the skill prepared state, say it in one line ("I created the order X and sent the notification to your phone").
- After the answer: compare with Expected. Match => record `passed`, next step. Mismatch or doubt => record the observation in `notes.md` (G8), ask at most one precise follow-up question (the screenshot, the exact text), then continue; never debate. A blocker (the step cannot be done) => note it, skip dependent steps (mark them `blocked by #n`), continue with the independent ones.
- The tester can reply `skip`, `stop`, `note: ...`, or send free remarks at any time; free remarks are recorded verbatim as notes (type bug/ux/text/idea/off-scope inferred, confirmed at the end).
- **Any step can be skipped** (no device, no second person, wrong network, no time). A skipped step is recorded `skipped by tester` (never `failed`), with the reason if given, and is offered again in the re-test pass.
- **Clarification during exploration.** Default: at most one precise follow-up question, never a debate. When the tester asks to be questioned, or a remark changes a rule, run a short AskUserQuestion round (2-4 options, recommended first) so the fix is fully specified. Still no code change (G3); record the answer in the notes Decisions section.
- Offer **re-sends** when timing matters: "Notification not received? Say `resend` and I trigger another one." Re-trigger only after G4 re-check.
- Agent suggestions (something noticed while preparing or pre-checking) are recorded as `agent suggestion, to confirm` and put to the tester in one line, never silently turned into findings.
- A phone-only step is sent only if the device was declared. Switching device is announced once ("Desktop steps are done, next 4 steps are on your Android phone").

## Examples

Step with prepared data:

```
Step 3/14 - Order drafts offline
I created the order "manual-test-20261016-1500" (3 items) on preprod.

Link: https://preprod.example.com/fr/orders/<order-uuid>/edit
Do:
1. Open the link, log in with email manual-test-20261016-1500-admin@example.test and password <full password, written out by the skill at send time>.
2. Turn the toggle "Mode hors ligne" on.
3. Turn your Wi-Fi off for 10 seconds, then back on.
Expected: the banner "Hors ligne - les changements seront synchronisés" appears when Wi-Fi is off, and disappears within a few seconds after reconnection.
Send back: a screenshot of the banner while offline.
```

Phone step with a triggered send (G4 verified: the push target is the tester's own device):

```
Step 9/14 - Push notification (Android)
Link: https://preprod.example.com/fr/settings/notifications
Do:
1. Open the link on your phone and accept the permission prompt.
2. Reply "ready"; I send one test notification to this device only and tell you the send time.
Expected: within 30 seconds of the send time a notification titled "Commande expédiée" arrives; tapping it opens the order page.
Send back: yes/no, and a screenshot of the notification. Say "resend" if you missed it.
```

Check-only step:

```
Step 12/14 - API documentation
Link: https://preprod.example.com/fr/developers/api
Do: 1. Open the link. 2. Open the endpoint "GET /v2/orders".
Expected: the page loads in under 3 seconds, the endpoint shows an example response with the field "status".
Send back: yes/no, and the value shown for "status".
```

## Data preparation

1. List what the step needs (account, entity, notification, flag, consent state) from the plan.
2. Find the project's own tool for it (config `prepare:`, seed scripts, management commands, admin, API with a test token). Never write to the database with raw SQL unless the project's docs say that is its way.
3. Assert G1 and G2 for the exact command, G4 if it sends; run it; record it in `state.json` `prepared[]` with the undo.
4. Verify the result (query, HTTP check) before telling the tester it is ready.
5. Cannot prepare safely => ask the tester to prepare it with exact instructions, or mark the step not tested.
