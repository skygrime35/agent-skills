# CHANGELOG reference

Contents: 0 append-only rule · 1 existing tooling · 2 audience and language · 3 entry structure · 4 hard rules

Goal: a `CHANGELOG.md` entry (or the project's native changelog artifact) that a **non-technical reader** understands, produced at merge time.

## 0. Cardinal rule: append-only, newest-on-top

The changelog is a **cumulative history**, not a per-release snapshot. Each merge **prepends** one new dated block at the top; **all previous entries are kept exactly as they are** underneath. Create the file only when it doesn't exist. **Never** rewrite it from scratch, reorder, reword, or delete old entries. Read the current file, insert the new block below the intro/header and above the previous top entry, and write it back unchanged elsewhere.

## 1. Conform to existing tooling — never corrupt it

Detect first (see `detection.md` §6), then:

- **Keep a Changelog** (`## [x.y.z] - DATE` with `### Added/Changed/Fixed/Removed`): prepend a new dated section in the same shape, above the previous top entry, below the intro. Keep semver + comparison links if present.
- **towncrier** (`changelog.d/` / `newsfragments/`): do **not** edit `CHANGELOG.md` directly — add news fragment files (`<id>.feature`, `.bugfix`, …); the tool assembles them at release.
- **changesets** (`.changeset/`): add a `.changeset/<name>.md` with the frontmatter bump; let `changeset version` write the changelog.
- **release-please / semantic-release**: the changelog is bot-generated from commits — **do not hand-edit**. Instead ensure the commit/PR titles are clean; note this in the recap.
- **No existing changelog**: create `CHANGELOG.md` at repo root in Keep a Changelog style.
- **Monorepo**: write to the changed package's changelog (or each affected package), not just the root.

## 2. Audience & language

- Language = the existing changelog's language by default (an OSS library's changelog is English even if the team speaks French; a French SaaS's user-facing changelog is French).
- Audience = **end users / stakeholders**, not developers. Translate jargon:
  - "Refactored the auth use-case layer" → *(omit — internal, no user impact)* or "Signing in is faster and more reliable."
  - "Bumped Pillow to 11.2, fixed N+1 in comment selector" → "Pages with many comments now load faster."
  - "Added `RunPython` backfill for `video.duration`" → "Video lengths now display correctly everywhere."

## 3. Structure of an entry

```
## <version or date> — <one-line theme of the release>

### New
- <user-visible capability, plain language>

### Improved
- <perf/UX/reliability improvements users would notice>

### Fixed
- <bugs a user could have hit, described by symptom not cause>

### Other
- <notable but minor; skip purely internal refactors/chore/test/doc churn>
```

Rank within each group by user impact (biggest first). Merge many small commits into one readable bullet. Drop internal-only noise (refactors, test changes, dependency bumps with no user-visible effect) unless they change behavior.

## 4. Hard rules

- **No vulnerability details.** Never describe a security fix in a way that maps the exploit ("fixed an auth bypass that let anyone read others' private videos"). Write "Fixed a security issue" or "Strengthened access controls" — details belong in a private advisory, not a public changelog.
- **No secrets, internal hostnames, or infra specifics.**
- **User reviews/edits before commit.** Present the draft; let the human correct tone and inclusion.
- **Commit only after the Phase 6 "go"** (as part of the Phase 7 merge), so a no-go never leaves an orphan release entry. Never push it to SOURCE before the go, and never use it as a preprod-trigger commit.
