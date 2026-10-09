# Risky-migration reference

For each migration in `TARGET..SOURCE`, assess **four** independent axes, not just "is it destructive". The dangerous ones are often not the obvious drops.

## The four axes

1. **Destructive** — irreversibly removes/overwrites data or schema.
2. **Reversible?** — can the migration's own `down`/`reverse` restore the prior schema *and* data? Adding a column is reversible (schema-wise); dropping one is not (the data is gone). Record `reversible | irreversible`.
3. **Backward-compatible with the code still running during rollout?** — migrations frequently apply at container boot *before* the new code is fully serving, and during a rolling deploy old and new code run simultaneously. A migration that renames/removes a column the **old** code still reads breaks live requests mid-deploy. This is the #1 cause of "deploy broke prod" that a destructive-pattern scan alone misses.
4. **Lock / duration under real volume** — will it take a long lock or rewrite a large table? Cross the estimated duration against the DB's `statement_timeout` (and lock timeout). If a migration can exceed the timeout on the real prod row count, it will be **killed mid-way**; a non-transactional one (e.g. `CREATE INDEX CONCURRENTLY`, `atomic=False`) can leave an **INVALID/partial** object not recorded as applied.

Always pull the **real prod row count** for targeted tables (SSH `psql -tAc "select count(*) from <table>"`) — preprod's tiny seeded volume hides duration/lock problems entirely.

## Patterns by ORM

**Django** — flag `RemoveField`, `DeleteModel`, `RenameField`/`RenameModel`, `AlterField` with a type change, `RunPython` (especially value rewrites; check for `reverse_code`), `AddField(null=False)` without a `default`, `CREATE INDEX CONCURRENTLY`/`atomic = False`. Standard-safe: `CreateModel`, nullable/`default=` `AddField`, the split `AddField → RunPython backfill → RemoveField` pattern across separate migrations.

**Rails** — `remove_column`, `rename_column`, `change_column` (type), `drop_table`, data migrations in `up` without a `down`, `add_column ... null: false` without default. Prefer `disable_ddl_transaction!` + `algorithm: :concurrently` for indexes.

**Alembic** — `op.drop_column`, `op.alter_column` (type/nullable), `op.drop_table`, `op.execute(<DML>)` without a paired downgrade, missing `downgrade()`.

**Prisma** — a generated migration containing `DROP COLUMN`, `DROP TABLE`, `ALTER COLUMN ... TYPE`, `ALTER COLUMN ... SET NOT NULL`; note managed-DB providers may apply differently. `prisma migrate deploy` has no automatic down.

**TypeORM / Sequelize / Knex / Drizzle** — `dropColumn`, `changeColumn`, `removeColumn`, raw `ALTER`/`DROP` in `up` with an empty/asymmetric `down`.

**Ecto** — `remove`, `modify` (type), `drop table`, `execute/1` (irreversible unless `execute/2` gives the reverse), non-concurrent index creation on large tables.

**Flyway / Liquibase** — versioned SQL is **forward-only by default**; a `V__` with `DROP`/`ALTER TYPE`/`NOT NULL` has no automatic undo. Liquibase changesets without `rollback` blocks are irreversible.

**golang-migrate / Diesel / EF Core / Laravel** — check the paired `.down.sql`/`down()`/`Down()` actually reverses the `up`; flag `DROP`/type changes/`NOT NULL` additions and empty downs.

**Raw SQL** — grep the diff for `DROP TABLE`, `DROP COLUMN`, `ALTER COLUMN ... TYPE`, `SET NOT NULL`, `TRUNCATE`, `DELETE FROM`, `UPDATE ... SET` (mass rewrites).

## Output to Phase 6

Per migration: `{file, patterns[], reversible, backward_compatible, prod_rows, est_duration, timeout_risk}`. Roll up into the recap's risk flags and, crucially, into **whether the automatic (code-only) rollback is sufficient** — if any migration is destructive/irreversible, Phase 6(D) must state that the **only** data recovery is a backup restore with RPO loss, and Phase 6.5's rollback file must set `db_restore_required: true`.
