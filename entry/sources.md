# Sources

Verified for the PostgreSQL deep-dive on **2026-09-06**.

Primary references:

- **PostgreSQL current documentation** — https://www.postgresql.org/docs/current/ (`documentation`)
- **PostgreSQL source repository** — https://github.com/postgres/postgres (`repository`)
- **PostgreSQL license and copyright** — https://github.com/postgres/postgres/blob/master/COPYRIGHT (`repository`)
- **Architectural fundamentals** — https://www.postgresql.org/docs/current/tutorial-arch.html (`documentation`)
- **Concurrency control / MVCC** — https://www.postgresql.org/docs/current/mvcc.html (`documentation`)
- **Transaction isolation** — https://www.postgresql.org/docs/current/transaction-iso.html (`documentation`)
- **Explicit locking and deadlocks** — https://www.postgresql.org/docs/current/explicit-locking.html (`documentation`)
- **Routine vacuuming and autovacuum** — https://www.postgresql.org/docs/current/routine-vacuuming.html (`documentation`)
- **Write-ahead logging** — https://www.postgresql.org/docs/current/wal-intro.html (`documentation`)
- **Physical database storage** — https://www.postgresql.org/docs/current/storage.html (`documentation`)
- **Index types** — https://www.postgresql.org/docs/current/indexes-types.html (`documentation`)
- **Using EXPLAIN** — https://www.postgresql.org/docs/current/using-explain.html (`documentation`)
- **Planner statistics** — https://www.postgresql.org/docs/current/planner-stats.html (`documentation`)
- **Backup and restore** — https://www.postgresql.org/docs/current/backup.html (`documentation`)
- **Continuous archiving and point-in-time recovery** — https://www.postgresql.org/docs/current/continuous-archiving.html (`documentation`)
- **Warm standby / streaming replication** — https://www.postgresql.org/docs/current/warm-standby.html (`documentation`)
- **Logical replication** — https://www.postgresql.org/docs/current/logical-replication.html (`documentation`)
- **Client authentication** — https://www.postgresql.org/docs/current/client-authentication.html (`documentation`)
- **`pg_hba.conf`** — https://www.postgresql.org/docs/current/auth-pg-hba-conf.html (`documentation`)
- **Row security policies** — https://www.postgresql.org/docs/current/ddl-rowsecurity.html (`documentation`)
- **Table partitioning** — https://www.postgresql.org/docs/current/ddl-partitioning.html (`documentation`)
- **JSON types** — https://www.postgresql.org/docs/current/datatype-json.html (`documentation`)
- **Monitoring database activity** — https://www.postgresql.org/docs/current/monitoring-stats.html (`documentation`)

Additional current PostgreSQL documentation was reviewed for base backups, WAL configuration, replication slots, roles, privileges, extensions, index-only scans, HOT updates, sequence behavior, memory/resource settings, and major-version upgrade operations.

Source selection favors the PostgreSQL Global Development Group's current documentation and canonical source repository. Version-specific planner behavior, monitoring views, replication features, authentication defaults, and maintenance settings should be checked against the exact PostgreSQL major/minor version in production.
