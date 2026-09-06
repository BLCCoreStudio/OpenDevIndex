# History

## 2026-09-06 — deep-dive upgrade

- Upgraded `database/mysql` from a compact schema-v1 overview to a schema-v3 deep technical reference.
- Documented the SQL/storage-engine boundary and InnoDB as the primary transactional mental model.
- Added clustered/secondary index behavior, buffer-pool caching, redo/undo, MVCC, isolation, next-key locking, deadlocks, and transaction retry semantics.
- Added optimizer statistics, histograms, `EXPLAIN`, composite-index design, DDL/migration safety, and metadata-locking failure modes.
- Added binary-log semantics, GTIDs, source/replica replication, Group Replication, InnoDB Cluster boundaries, backup, PITR, and recovery testing.
- Added account/role/TLS boundaries, Performance Schema observability, capacity planning, incident triage, common production failures, and learning paths.
- Curated official MySQL documentation and the canonical server repository as primary sources.
- Added typed alternative relationships to PostgreSQL and SQLite plus Technology Universe coverage metadata.
- Re-verified the module on 2026-09-06.

## 2026-08-31 — v0.1

- Reviewed `database/mysql` against the current OpenDevIndex catalog and taxonomy.
- Recorded canonical kind `database` and domain facets: data.
- Re-rendered module documentation from validated source-backed metadata.

## Earlier history

## 2026-08-31

- Added `database/mysql` to the curated OpenDevIndex v0.1 catalog.
- Created the initial source-backed knowledge module.
- Verified metadata structure and required references with the repository validator.
