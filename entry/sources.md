# Sources

Deep-dive revision verified on **2026-09-06** against current SQLite documentation and the official SQLite source repository.

## Core project and licensing

- **SQLite documentation** — https://www.sqlite.org/docs.html (`documentation`)
- **SQLite source repository** — https://sqlite.org/src/ (`repository`)
- **SQLite public-domain dedication** — https://www.sqlite.org/copyright.html (`official`)

## Architecture and storage

- **Architecture of SQLite** — https://www.sqlite.org/arch.html (`documentation`)
- **Database file format** — https://www.sqlite.org/fileformat2.html (`documentation`)
- **WITHOUT ROWID tables** — https://www.sqlite.org/withoutrowid.html (`documentation`)

## Transactions, locking, and WAL

- **File locking and concurrency** — https://www.sqlite.org/lockingv3.html (`documentation`)
- **Write-ahead logging** — https://www.sqlite.org/wal.html (`documentation`)
- **WAL-mode file format** — https://www.sqlite.org/walformat.html (`documentation`)
- **Isolation in SQLite** — https://www.sqlite.org/isolation.html (`documentation`)
- **Transaction control** — https://www.sqlite.org/lang_transaction.html (`documentation`)

## Query planning and maintenance

- **Query planning** — https://www.sqlite.org/queryplanner.html (`documentation`)
- **ANALYZE** — https://www.sqlite.org/lang_analyze.html (`documentation`)
- **PRAGMA reference** — https://www.sqlite.org/pragma.html (`documentation`)

## Backup, integrity, and operational safety

- **SQLite backup API** — https://www.sqlite.org/backup.html (`documentation`)
- **Appropriate uses for SQLite** — https://www.sqlite.org/whentouse.html (`documentation`)
- **Implementation limits** — https://www.sqlite.org/limits.html (`documentation`)
- **Threading modes** — https://www.sqlite.org/threadsafe.html (`documentation`)
- **How SQLite databases become corrupt** — https://www.sqlite.org/howtocorrupt.html (`documentation`)

## Security and extensions

- **SQLite security guidance** — https://www.sqlite.org/security.html (`documentation`)
- **JSON functions and operators** — https://www.sqlite.org/json1.html (`documentation`)
- **FTS5 extension** — https://www.sqlite.org/fts5.html (`documentation`)

## Verification notes

SQLite is dedicated to the public domain. The module avoids treating compile-time options, default pragmas, extension availability, and planner implementation details as timeless facts because those can vary by release or embedding environment.

Architecture claims are grounded in SQLite's own documentation: SQL is compiled into VDBE bytecode; database tables and indexes use B-trees; the pager coordinates page caching, locking, and transaction durability; WAL permits concurrent readers with a writer while retaining one writer at a time; and WAL's shared-memory coordination makes ordinary network-filesystem sharing an unsafe architectural assumption.

Primary SQLite documentation and source material are preferred throughout. Secondary sources were not used as authority for the file format, concurrency, durability, security, or recovery model.