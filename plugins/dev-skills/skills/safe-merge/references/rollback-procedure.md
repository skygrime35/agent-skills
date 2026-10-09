# Rollback-procedure reference

Phase 6.5 writes a durable `.claude/safe-merge/rollback-<TIMESTAMP>.md` **before** the push, so `/safe-merge revert` can restore the pre-merge state even in a fresh session (or by a human reading it). The three-tier strategy below is the model Phase R executes.

## Three recovery tiers (fastest/safest first)

1. **Code/image rollback** — retag the previous release image and recreate containers (e.g. the deploy's `:rollback`→`:latest`), or redeploy the pre-merge SHA. Seconds; **no DB change**. Correct when the deploy failed or the break is code-only. Precondition: the previous-release artifact exists and matches the pre-merge SHA (verified in Phase 3).
2. **`git revert` of the merge commit + push** — creates a revert commit that redeploys the previous code through the normal pipeline. Minutes (a rebuild). Correct for a functional bug the health check didn't catch, when **no migration mutated data incompatibly**.
3. **DB restore from the pre-merge backup** — last resort. Required when a **destructive/irreversible migration** changed data such that old code can't run against the new schema. This is the irreversible `DROP DATABASE`/restore path with **up to RPO of data loss** (every write since the backup). Double-confirm; stop background workers first; restore; restart. **Do NOT re-run migrations after a restore**: the backup already holds the pre-merge schema, and old code expects exactly that.

Pick the **lowest tier that fully restores service.** Never jump to tier 3 if tier 1 suffices.

**Phase R gate.** Every tier is a prod write: Phase R executes nothing until the human explicitly confirms the revert plan (tier, exact commands, impact). That confirmation is Phase R's own gate, equivalent to the Phase 6 go. Tier 3 additionally needs a second, separate confirmation.

## Template for `rollback-<TIMESTAMP>.md`

```markdown
# Rollback plan — merge <SOURCE>→<TARGET> at <TIMESTAMP>

## Pre-merge state
- TARGET pre-merge SHA: <sha>            # revert target
- Prod running SHA before merge: <sha>   # from VERSION_ENDPOINT
- Rollback image/artifact: <tag> present=<yes/no> matches_prod_sha=<yes/no>

## Backups taken (this run)
- prod DB: <path>  sha256=<...>  taken_at=<...>
- preprod DB: <path>  sha256=<...>
- config/infra snapshot: <path>          # prod .env var names+hashes, compose, media backend, flags
- blind spots (NOT recoverable): <object storage / secrets / Redis / ...>

## Migration verdict
- migrations in batch: <list>
- destructive/irreversible: <yes/no>
- db_restore_required: <yes/no>          # if yes, tier-3 is mandatory for data recovery
- statement_timeout risk: <yes/no>

## Recovery commands (fill with the project's real, tested commands)
### Tier 1 — code/image rollback
    <exact command(s)>
### Tier 2 — git revert
    git checkout <TARGET>
    git revert -m 1 <merge-commit-sha>
    git push origin <TARGET>
### Tier 3 — DB restore (last resort, RPO loss)
    <stop workers>
    <restore script> <env> <prod backup path>
    <restart workers>

## Post-recovery verification
- [ ] health endpoint = ok
- [ ] VERSION_ENDPOINT back to <pre-merge SHA>
- [ ] at-risk table counts consistent with pre-merge (<counts>)
- [ ] a real login + a media read succeed
```

## Notes

- Fill every `<...>` with the project's **actual** commands and paths at write time — the file must be runnable without re-derivation.
- Keep the latest file discoverable (Phase R loads the most recent by timestamp).
- If `db_restore_required: true`, Phase 6(D) must have already told the human, at the gate, that the automatic rollback would **not** cover data.
- After a successful revert, write a short incident note next to the rollback file (what broke, which tier was used, data-loss window if any).
