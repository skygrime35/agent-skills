# Analysis and plan

Phase 2. Goal: from a change set to an ordered list of short human journeys, cheaply.

## Agent matrix

Follow the project's orchestration section if present. Otherwise:

| Role | Type | Work |
|---|---|---|
| Reader | `haiku-standard` | `git log`/diff reading per commit batch, doc and changelog reading, route and screen mapping, existing test lookup, reporting what exists |
| Grouper / journey deriver | `sonnet-standard` | group commits and files into features, derive user-visible journeys, classify internals, order the plan |
| Arbiter | `opus-standard` | only when grouping is ambiguous after the sonnet pass (cross-cutting refactors, flags interacting) or the diff is large and entangled |
| Plan reviewer | `opus-standard` | one logic review of the whole plan at plan time, before it is shown (see Verification) |
| Group verifier | `sonnet-standard` | code re-check of every step of one group, just before that group is sent (see Verification) |

Fan out readers over disjoint slices (commit ranges, app folders); one sonnet pass per run synthesises. Missing type => the Agent tool `model` parameter. Subagent reports are findings with evidence (commit SHA, file, route), not narratives.

## Steps

1. **Change set** (readers): commits, changed files, changelog or PR descriptions, docs and ADRs touched, tests added. For `all`/`features:`: inventory of user-facing features instead.
2. **Group by feature** (grouper): one group per user-visible capability, not per commit. Commit messages, doc changes and added tests are the strongest hints. Merge-only or refactor commits attach to the feature they serve or to "internal".
3. **Derive journeys** per feature: every screen, button, form, email, notification (push, in-app, chat), admin screen, API doc page, offline or degraded mode a user can reach. Include error and empty states only when the diff changed them. Entry points come from the routing and menu code, never invented.
4. **Classify internals:** pure refactors, dependency bumps, CI changes, DB-only changes already covered by automated tests are listed as `not manually tested, covered by <test file or suite>`; say which test. If nothing covers an internal, flag it as a gap, do not turn it into a manual step unless it has a user-visible symptom.
5. **Order the plan:** highest risk and most visible first (payments, auth, data loss, new headline features), then the rest; **group by device** (all desktop steps, then all phone steps) to avoid back-and-forth; steps within a feature are sequential and respect data dependencies.
6. **Annotate each feature:** risk (high/medium/low), device, step count, data the skill prepares, estimated minutes, flags or settings that must be on.

## Plan format (shown once, then stored in `state.json`)

```
Plan - <scope>, <target> (<url>), devices: <list>
| # | Feature | Risk | Device | Steps | Prepared by the skill | ~min |
...
Not manually tested (covered elsewhere): <item> -> <test>
Not testable with your devices: <item> -> <reason>
```

Ask once: go / adjust (reorder, drop, add). Total duration is stated; the tester may stop at any time.

## Verification (plan time and per group)

Why: in the first real run, steps written from the diff alone had 11 wrong expectations out of 15 in one group and 9 out of 13 in another (invented button placement, auto-save taken for a save button, conditional texts expected unconditionally, wrong link format, missing data precondition). Say this measured value in one short rationale line when presenting the plan.

1. **Plan review (once, before showing the plan).** One strong reviewer (`opus-standard`) re-reads the whole plan for logic: order, data dependencies, interacting features, missing preparation, steps that duplicate or validate each other, the not-tested list. Skipped for small plans (under about 15 steps); the per-group pass below is never skipped.
2. **Group verification (mandatory, before each group is sent).** One `sonnet-standard` verifier re-checks every step of that group in the code: entry point, exact labels, conditions under which the expected result appears, link format, data preconditions, form fields, accepted login identifier. It corrects the steps, reorders them and adds preparation when a precondition is missing, and returns the corrected group with evidence (file, line). Record `verified` (with the served SHA) for the group in `state.json`; a group never starts unverified.
3. **Effective configuration.** For an expected result that depends on an overridable value (timing, limit, flag), read only the specific named keys needed, never dump the environment and never print secret values (non-secret values or presence only), and only when the target's configuration is readable read-only with the access the project documents (for example the environment of the preprod containers). Quote the effective values. Otherwise ask the tester or read the config file, and flag the expectation "default value, may differ on target".
4. **Static content** is read by the verifier from the repo or served HTML and recorded `verified by agent` (G8 limits and the tester's light on-screen check apply).
