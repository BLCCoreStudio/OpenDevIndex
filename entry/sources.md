# Sources

Deep-dive revision verified on **2026-09-06** against current MySQL documentation and the canonical MySQL Server repository.

## Core project and licensing

- **MySQL Reference Manual** — https://dev.mysql.com/doc/refman/en/ (`documentation`)
- **MySQL Server source repository** — https://github.com/mysql/mysql-server (`repository`)
- **MySQL Community Edition** — https://www.mysql.com/products/community/ (`official`) — Community Edition is distributed under the GNU GPL; commercial licensing also exists for other use cases.

## InnoDB architecture and storage

- **InnoDB storage engine** — https://dev.mysql.com/doc/refman/en/innodb-storage-engine.html (`documentation`)
- **InnoDB architecture** — https://dev.mysql.com/doc/refman/en/innodb-architecture.html (`documentation`)
- **InnoDB buffer pool** — https://dev.mysql.com/doc/refman/en/innodb-buffer-pool.html (`documentation`)
- **Clustered and secondary indexes** — https://dev.mysql.com/doc/refman/en/innodb-index-types.html (`documentation`)
- **Undo logs** — https://dev.mysql.com/doc/refman/en/innodb-undo-logs.html (`documentation`)
- **Redo log** — https://dev.mysql.com/doc/refman/en/innodb-redo-log.html (`documentation`)

## Transactions and concurrency

- **InnoDB locking and transaction model** — https://dev.mysql.com/doc/refman/en/innodb-locking-transaction-model.html (`documentation`)
- **Transaction isolation levels** — https://dev.mysql.com/doc/refman/en/innodb-transaction-isolation-levels.html (`documentation`)
- **Deadlocks in InnoDB** — https://dev.mysql.com/doc/refman/en/innodb-deadlocks.html (`documentation`)

## Query planning and indexes

- **Optimization and indexes** — https://dev.mysql.com/doc/refman/en/optimization-indexes.html (`documentation`)
- **Optimizing queries with EXPLAIN** — https://dev.mysql.com/doc/refman/en/using-explain.html (`documentation`)
- **Optimizer statistics** — https://dev.mysql.com/doc/refman/en/optimizer-statistics.html (`documentation`)

## Replication and recovery

- **The binary log** — https://dev.mysql.com/doc/refman/en/binary-log.html (`documentation`)
- **Replication implementation** — https://dev.mysql.com/doc/refman/en/replication-implementation.html (`documentation`)
- **Group Replication** — https://dev.mysql.com/doc/refman/en/group-replication.html (`documentation`)
- **Point-in-time recovery using binary logs** — https://dev.mysql.com/doc/refman/en/point-in-time-recovery-binlog.html (`documentation`)
- **Backup and recovery** — https://dev.mysql.com/doc/refman/en/backup-and-recovery.html (`documentation`)

## Security and observability

- **Access control and account management** — https://dev.mysql.com/doc/refman/en/access-control.html (`documentation`)
- **Using roles** — https://dev.mysql.com/doc/refman/en/roles.html (`documentation`)
- **Encrypted connections** — https://dev.mysql.com/doc/refman/en/encrypted-connections.html (`documentation`)
- **Performance Schema** — https://dev.mysql.com/doc/refman/en/performance-schema.html (`documentation`)

## Verification notes

The deep-dive intentionally avoids treating version-sensitive defaults as timeless facts. Current documentation should be rechecked before changing claims about authentication plugins, replication defaults, DDL algorithms, TLS/runtime requirements, optimizer capabilities, or release-specific storage-engine behavior.

Primary sources are preferred throughout. Secondary descriptions were not used as authority for the architecture, transaction, replication, or recovery model.