# History

## 2026-09-06 — deep-dive upgrade

- Upgraded `database/postgresql` from schema v1 to schema v3.
- Reframed the module around PostgreSQL's server/process architecture, query planning/execution, MVCC snapshots, locks, WAL durability, checkpoints, vacuum/autovacuum, and storage lifecycle.
- Added index access methods, planner statistics, `EXPLAIN`, transaction retry semantics, partitioning, data types, extensions, memory/concurrency capacity, and production DDL guidance.
- Added physical/logical backup, point-in-time recovery, streaming and logical replication, replication-slot retention, standby conflicts, HA/fencing boundaries, and restore testing.
- Added roles, `pg_hba.conf`, TLS, row-level security, privileged-function/search-path guidance, connection-pooling concerns, monitoring, incident triage, failure modes, and upgrade discipline.
- Verified the canonical PostgreSQL license/copyright text and added Technology Universe coverage metadata plus typed alternatives to MySQL and SQLite.
- Expanded the primary-source set to current PostgreSQL documentation and the canonical source repository.

## 2026-08-31 — v0.1

- Reviewed `database/postgresql` against the current OpenDevIndex catalog and taxonomy.
- Recorded canonical kind `database` and domain facets: data.
- Re-rendered module documentation from validated source-backed metadata.

## Earlier history

## 2026-08-31

- Added `database/postgresql` to the curated OpenDevIndex v0.1 catalog.
- Created the initial source-backed knowledge module.
- Verified metadata structure and required references with the repository validator.
