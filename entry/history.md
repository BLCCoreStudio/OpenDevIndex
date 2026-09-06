# History

## 2026-09-06 — deep-dive upgrade

- Upgraded `database/sqlite` from a compact schema-v1 overview to a schema-v3 deep technical reference.
- Documented SQLite's embedded-library boundary, SQL-to-VDBE-bytecode execution path, B-tree storage, pager/page-cache responsibilities, and VFS operating-system abstraction.
- Added rowid and `WITHOUT ROWID` storage models, dynamic typing/type affinity, `STRICT` tables, index design, query planning, `EXPLAIN QUERY PLAN`, and planner-statistics maintenance.
- Added transaction modes, savepoints, the single-writer concurrency rule, `SQLITE_BUSY` handling, rollback journals, WAL snapshots, checkpointing, and network-filesystem constraints.
- Added backup API and `VACUUM INTO` guidance, integrity/recovery practices, live auxiliary-file handling, corruption failure modes, and filesystem safety boundaries.
- Added security guidance for untrusted databases and SQL, extension loading, parameter binding, threading modes, mobile/desktop/server-local deployment patterns, capacity considerations, and operational triage.
- Added JSON/FTS5/virtual-table ecosystem coverage without treating optional or build-sensitive capabilities as universal defaults.
- Curated official SQLite documentation and the canonical Fossil source repository as primary sources.
- Recorded SQLite's public-domain dedication, deployment facets, Technology Universe coverage, and typed alternative relationships to PostgreSQL and MySQL.
- Re-verified the module on 2026-09-06.

## 2026-08-31 — v0.1

- Reviewed `database/sqlite` against the current OpenDevIndex catalog and taxonomy.
- Recorded canonical kind `database` and domain facets: data, embedded.
- Re-rendered module documentation from validated source-backed metadata.

## Earlier history

## 2026-08-31

- Added `database/sqlite` to the curated OpenDevIndex v0.1 catalog.
- Created the initial source-backed knowledge module.
- Verified metadata structure and required references with the repository validator.
