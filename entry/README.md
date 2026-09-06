# MySQL

> Open-source client/server relational database whose SQL layer, pluggable storage-engine architecture, InnoDB transaction system, binary log, replication, and operational tooling support transactional and mixed application workloads.

MySQL is easiest to reason about as a **SQL server layered over storage engines**, with InnoDB providing the transactional storage model used by most production deployments:

```text
clients / connectors
       |
       v
connection + authentication layer
       |
       v
parser -> resolver -> optimizer -> executor
       |
       v
storage-engine API
       |
       +--> InnoDB
       |     +--> buffer pool
       |     +--> clustered + secondary indexes
       |     +--> MVCC + locks
       |     +--> undo + purge
       |     +--> redo + checkpoints + crash recovery
       |
       +--> other supported engines

server-wide binary log
       |
       +--> replication
       +--> point-in-time recovery
```

The important operational distinction is that **InnoDB redo/undo state and the server binary log solve different problems**. Redo is part of InnoDB crash recovery. Undo supports rollback and consistent reads. The binary log records server changes for replication and recovery workflows. Treating those as interchangeable leads to incorrect backup, durability, and replication assumptions.

## Product boundary

MySQL Server provides:

- a networked SQL database server;
- account, privilege, and authentication systems;
- a cost-based optimizer and execution engine;
- a pluggable storage-engine interface;
- InnoDB ACID transactions, MVCC, row/index locking, and crash recovery;
- B-tree and specialized indexing capabilities;
- a transactional data dictionary;
- server binary logging;
- source/replica replication primitives;
- Group Replication for group membership and transaction certification;
- backup and recovery primitives;
- Performance Schema, Information Schema, logs, and diagnostic tooling.

MySQL Server alone does **not** make an application automatically highly available. Routing, topology management, backups, restore testing, failover policy, fencing, cross-region design, connection management, and capacity planning still require explicit engineering. MySQL InnoDB Cluster, MySQL Router, managed database services, orchestrators, proxies, and backup systems can provide higher-level capabilities, but their behavior must be understood separately from the core server.

## SQL layer and storage-engine boundary

MySQL has a server layer that handles work such as:

- client protocols and sessions;
- SQL parsing and name resolution;
- optimization;
- execution coordination;
- privileges;
- stored programs;
- metadata;
- binary logging;
- replication coordination.

Storage engines implement physical table/index behavior behind a common server interface.

That architecture matters because a statement such as:

```sql
SELECT *
FROM orders
WHERE customer_id = 42;
```

is optimized by the SQL layer, but row access, indexes, locking, MVCC visibility, and physical storage behavior depend heavily on the engine backing the table.

For normal transactional systems, the relevant engine is usually **InnoDB**.

## Why InnoDB is the default mental model

InnoDB combines:

- ACID transactions;
- MVCC consistent reads;
- row-level and index-range locking;
- clustered primary-key storage;
- secondary indexes;
- foreign keys;
- a buffer pool;
- redo-based crash recovery;
- undo records and purge;
- background flushing and checkpoint activity.

When troubleshooting a modern MySQL transactional workload, begin with InnoDB semantics unless the table explicitly uses a different engine.

## Connection and session model

A client normally connects over TCP or a local socket, authenticates as an account, and receives a session with its own state.

Session state can include:

- current database;
- transaction state;
- isolation level;
- SQL mode and time zone;
- temporary tables;
- user variables;
- prepared statements;
- session-scoped configuration.

Applications using connection pools must understand that a pooled physical connection can outlive one logical request. Session-local state that is not reset can leak assumptions between requests.

Large connection counts are not free. Even mostly idle sessions consume server and operating-system resources, and bursts of connection creation can become a bottleneck before storage or query execution does.

## Data hierarchy

A simplified logical hierarchy is:

```text
MySQL server instance
  -> database / schema
      -> table / view / routine / trigger / event / ...
          -> indexes / constraints / partitions / ...
```

In MySQL, `DATABASE` and `SCHEMA` are effectively synonyms in SQL syntax.

## Query lifecycle

A query passes through several conceptual stages:

```text
SQL text
  -> parse + resolve
  -> rewrite / simplification where applicable
  -> cost-based optimization
  -> execution plan
  -> executor
  -> storage-engine access
  -> rows
```

The optimizer chooses among access paths and join strategies using statistics, cost estimates, available indexes, predicates, ordering requirements, and other metadata.

A poor query can therefore be slow for different reasons:

```text
bad plan because estimates were wrong
```

```text
reasonable plan but too much data was requested
```

```text
plan was fine but execution waited on locks or I/O
```

```text
server-wide resource pressure made otherwise normal work slow
```

Those are different incident classes and should not be debugged with the same fix.

## `EXPLAIN` and plan inspection

`EXPLAIN` shows how MySQL intends to execute a statement.

```sql
EXPLAIN
SELECT id, created_at
FROM orders
WHERE customer_id = 42
ORDER BY created_at DESC
LIMIT 20;
```

Useful questions include:

- Which table is accessed first?
- Is an index lookup used or is a large scan required?
- How many rows does the optimizer estimate?
- Which predicates are used for index access versus post-filtering?
- Is sorting or temporary-table work required?
- Are joins using selective access paths?

When actual behavior differs materially from estimates, investigate statistics and data distribution before adding indexes blindly.

## Optimizer statistics and histograms

The optimizer depends on statistics about tables and indexes.

`ANALYZE TABLE` updates statistics used for planning. MySQL can also maintain histogram statistics for columns so the optimizer can model non-uniform distributions that ordinary index cardinality estimates do not capture well.

A recurring production pattern is:

```text
skewed data
  -> weak estimate
  -> wrong join order or access path
  -> unexpectedly expensive query
```

Plan quality is therefore partly a data-distribution problem, not only an SQL syntax problem.

## Index model

For InnoDB, the primary key is especially important because the table is organized around a **clustered index**.

Conceptually:

```text
primary-key B-tree
  -> leaf records contain the row

secondary-index B-tree
  -> leaf records contain secondary key + primary-key identity
```

Consequences:

- primary-key choice affects physical row organization;
- wide primary keys make secondary indexes wider;
- random primary-key insertion patterns can increase page churn and fragmentation;
- secondary-index lookups may require a second lookup into the clustered index unless all needed data is available from the secondary index.

If a table lacks a suitable explicit primary key, InnoDB must still maintain an internal row identity. Production schemas should normally define deliberate primary keys rather than relying on implicit behavior.

## Composite indexes and the leftmost-prefix idea

For a B-tree index such as:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at);
```

queries constraining `customer_id` can normally use the ordered index efficiently, and queries constraining both columns can often use a longer prefix of it.

But an index should be designed around actual access patterns, selectivity, ordering, and write cost—not by adding every filtered column to one giant key.

Each additional index increases:

- storage;
- buffer-pool footprint;
- insert/update/delete work;
- redo generation;
- backup size;
- recovery work.

## Specialized indexes

Depending on table definition and workload, MySQL also supports capabilities such as:

- FULLTEXT indexes;
- SPATIAL indexes;
- descending key parts;
- invisible indexes for testing optimizer behavior without immediately dropping an index;
- expression/function-based indexing capabilities in current releases.

Exact support varies by engine, data type, and release. Verify version-specific DDL against the current reference manual.

## Buffer pool

The InnoDB buffer pool caches table and index pages in memory.

A simplified read path is:

```text
query needs page
  -> page already in buffer pool? use memory copy
  -> otherwise read page from storage into buffer pool
```

Writes usually modify pages in memory first. Modified pages become **dirty** and are flushed later according to InnoDB's background algorithms and checkpoint pressure.

This creates an important performance rule:

> Database latency depends not only on the size of a query result, but on whether its working set and index path fit the memory/I/O behavior of the server.

A server can become I/O-bound when active data and indexes exceed effective cache capacity, when background flushing cannot keep up, or when large scans evict hotter pages.

## Redo log and durability

InnoDB redo is a write-ahead log of page changes used for crash recovery.

Conceptually:

```text
transaction changes pages
  -> redo records are generated
  -> required redo is persisted according to durability settings
  -> commit becomes durable
  -> dirty data pages may be flushed later
```

After a crash, InnoDB uses redo to recover changes that were durable in the log but not yet reflected in final data pages.

Durability settings must be chosen intentionally. Reducing synchronous flush behavior can improve throughput on some workloads but changes the failure window. Do not present a benchmark configuration as equivalent to durable production semantics.

## Undo logs, MVCC, and purge

Undo records store information required to roll back changes and reconstruct older row versions for consistent reads.

That supports MVCC:

```text
current row version
  -> older version information in undo
  -> snapshot decides which version is visible
```

Long-running transactions can keep old versions necessary for snapshots and therefore delay purge of historical undo information.

A common failure mode is:

```text
long transaction
  -> old versions remain needed
  -> purge cannot advance normally
  -> undo/history grows
  -> storage + I/O pressure increases
```

This is why transaction age is an operational metric, not merely an application concern.

## Transactions and autocommit

MySQL sessions commonly operate with autocommit enabled.

With autocommit:

```text
statement
  -> transaction starts
  -> statement succeeds
  -> transaction commits
```

Explicit multi-statement transactions group related work:

```sql
START TRANSACTION;

UPDATE accounts
SET balance = balance - 100
WHERE id = 10;

UPDATE accounts
SET balance = balance + 100
WHERE id = 20;

COMMIT;
```

The application must still handle:

- statement errors;
- deadlocks;
- lock wait timeouts;
- connection loss around commit;
- retry safety;
- idempotency where the final transaction outcome may be uncertain to the client.

## Isolation levels

InnoDB supports the standard isolation levels:

- `READ UNCOMMITTED`;
- `READ COMMITTED`;
- `REPEATABLE READ`;
- `SERIALIZABLE`.

The default is `REPEATABLE READ`.

Isolation changes both visibility and locking behavior. It should be selected based on application invariants, not simply changed to remove lock contention.

## Consistent reads versus locking reads

A plain `SELECT` can be a nonlocking consistent read based on an MVCC snapshot.

A statement such as:

```sql
SELECT *
FROM jobs
WHERE id = 7
FOR UPDATE;
```

is a locking read. It participates in the locking rules needed to safely update or coordinate rows.

These two kinds of reads have different concurrency semantics even when the SQL returns the same columns.

## Record, gap, and next-key locking

InnoDB locking is index-oriented.

Depending on isolation level and access path, a write or locking read can lock:

- index records;
- gaps between records;
- combinations known as next-key locks.

This explains a behavior that surprises many developers: a transaction can block an insert of a row that did not previously exist because the operation conflicts with a locked index range.

Indexes therefore influence not only query performance but also **the shape of concurrency**.

## Deadlocks are expected outcomes

Two valid transactions can acquire locks in incompatible order:

```text
Tx A locks row 1
Tx B locks row 2
Tx A waits for row 2
Tx B waits for row 1
```

InnoDB detects deadlocks and rolls back a victim transaction so progress can continue.

Applications should treat deadlocks as retryable transactional outcomes when the business operation is safe to retry.

Reduce deadlocks by:

- touching resources in a consistent order;
- keeping transactions short;
- using selective indexes so statements scan and lock fewer records;
- avoiding user/network waits while a transaction is open;
- breaking oversized write batches into controlled units.

## Foreign keys

InnoDB supports foreign-key constraints.

They protect referential integrity but also participate in locking and DDL constraints. Cascades, large parent/child modifications, and missing supporting indexes can turn an apparently local change into a wider concurrency event.

Use foreign keys intentionally and test the operational behavior of schema migrations involving large related tables.

## DDL and migration safety

Current MySQL releases support atomic and online DDL capabilities for many operations, but the exact algorithm depends on the operation, table definition, engine, and release.

A migration may use behavior equivalent to:

- metadata-only or near-instant change;
- in-place rebuild;
- table copy;
- stronger metadata locking than expected.

Production migrations should be reviewed for:

- metadata-lock duration;
- table rebuild size;
- temporary disk space;
- redo/binlog volume;
- replication lag;
- rollback or forward-fix strategy;
- impact on long-running transactions.

Never assume that the word "online" means "zero impact."

## Binary log

The MySQL binary log records events that change server state.

It is central to:

- replication;
- point-in-time recovery;
- auditing/change-stream integrations in some architectures.

The binary log is a server-level logical change stream and is conceptually distinct from InnoDB redo.

```text
InnoDB redo
  -> crash recovery of the storage engine

binary log
  -> replication + logical history for recovery workflows
```

## Replication

Traditional MySQL replication follows a source/replica model.

A simplified flow is:

```text
source transaction
  -> binary log
  -> replica receives events
  -> relay/apply pipeline
  -> replica data catches up
```

Replication is typically asynchronous unless a stronger configuration is intentionally added. A source can acknowledge a transaction before a replica has applied it.

Therefore:

```text
source committed
```

does not automatically mean:

```text
all replicas are current
```

Applications that read from replicas must define acceptable lag and consistency behavior.

## Row, statement, and mixed logging

MySQL can represent binary-log changes in different formats.

Row-based logging records row changes and is the normal foundation for Group Replication. Statement-based formats can be more sensitive to whether an operation is deterministic and whether execution context matches on replicas.

Choose replication/logging format based on correctness and ecosystem requirements, not only log volume.

## GTIDs

Global Transaction Identifiers give transactions stable identities across a replication topology.

GTIDs simplify many operations because replication can reason about which transactions a server has already executed rather than relying only on file/position coordinates.

They are useful for:

- failover workflows;
- replica provisioning;
- topology changes;
- identifying transaction history gaps.

Operational tooling should understand GTID state before performing reparenting or recovery.

## Replication lag

Replica lag can come from:

- insufficient apply concurrency;
- slow storage;
- one very large transaction;
- lock contention on the replica;
- schema/index differences;
- network delay;
- resource pressure;
- intentionally delayed replication.

A single "seconds behind" number is not a complete health model. Also inspect receive/apply progress, worker state, errors, transaction queues, and workload shape.

## Group Replication

Group Replication adds membership, distributed recovery, and transaction certification across a group of MySQL servers.

At a high level:

```text
transaction executes
  -> writeset / transaction is proposed
  -> group certification checks conflicts/order
  -> transaction is accepted or aborted
  -> members apply committed work
```

It requires InnoDB and binary-log settings compatible with its transaction model.

Group Replication is not equivalent to a magic shared-disk database. Each member maintains its own state, network partitions still exist, certification conflicts can abort transactions, and operational systems still need routing, monitoring, backups, and topology policy.

## InnoDB Cluster boundary

MySQL InnoDB Cluster is a higher-level HA solution around technologies such as:

- MySQL Server;
- Group Replication;
- MySQL Shell;
- MySQL Router.

This distinction is important when reading an incident:

```text
server failure
```

is not the same as:

```text
group membership failure
```

and neither is automatically the same as:

```text
application routing failure
```

Each layer has separate observability and recovery behavior.

## Backup strategy

A backup strategy must define both **what is copied** and **what recovery objective it supports**.

Common classes include:

- logical dumps, which serialize schema/data as logical statements or rows;
- physical backups, which preserve storage-engine files in a recovery-safe way;
- storage snapshots coordinated with database consistency guarantees;
- replicas used as backup sources;
- managed-service snapshots and continuous backup systems.

A backup is not proven until a restore has succeeded in a clean environment.

## Point-in-time recovery

PITR commonly uses:

```text
known-good backup
  + binary logs generated after the backup
  -> restore backup
  -> replay changes until target time/position
```

This means binary-log retention and backup metadata are part of the recovery design.

If the log segment required after the backup has already been purged or lost, that recovery point is gone.

## Recovery testing

Test recovery for scenarios such as:

- accidental table deletion;
- bad deployment that corrupts logical data;
- loss of the primary server;
- loss of an entire availability zone;
- replica divergence;
- operator mistakes during failover;
- expired or missing binary logs.

Record actual restore time. Recovery-time objectives should be based on measured restores, not backup job duration.

## Durability versus replication

These are separate questions:

1. Did the local server durably commit the transaction?
2. Did the binary log durably record the transaction according to configuration?
3. Did a replica receive it?
4. Did a replica apply it?
5. Did enough members confirm it for the application's HA policy?

A system can answer "yes" to one and "no" to another.

## Security model

MySQL accounts are identities such as:

```text
'user'@'host-pattern'
```

Authentication and authorization are separate concerns.

Security design should cover:

- authentication plugin choice;
- TLS for remote connections;
- least-privilege grants;
- roles;
- privilege scope;
- service-account rotation;
- administrative separation;
- secrets storage;
- backup encryption and access;
- local operating-system permissions;
- plugin/component supply chain.

Do not expose a database listener directly to untrusted networks simply because password authentication is enabled.

## Privileges and roles

Grant only the capabilities an application actually needs.

For example, an application account that performs normal CRUD should not automatically receive:

- global administrative privileges;
- account-management privileges;
- filesystem-related privileges;
- replication administration;
- unrestricted routine or plugin administration.

Roles can group privileges so policy is easier to review and rotate than many independent grants.

## Definer-context objects

Views, stored routines, triggers, and events can execute with security semantics influenced by their `DEFINER` and SQL security settings.

Treat these as privileged code:

- use deliberate definers;
- avoid orphaned administrative definers;
- review what underlying objects can be reached;
- include them in migration and restore tests.

## TLS and client verification

Encrypted transport protects database traffic in transit, but encryption alone is not enough if the client does not verify the server identity it intended to reach.

Production connectors should use TLS modes that provide the authentication guarantees required by the threat model, not merely "encryption if available."

## Performance Schema

Performance Schema instruments server execution and resource usage.

It can expose information about areas such as:

- statement execution;
- waits;
- stages;
- transactions;
- locks;
- memory;
- replication;
- threads;
- file and socket activity.

It is one of the core tools for moving from "the database is slow" to a measurable wait or workload hypothesis.

## `sys` schema and Information Schema

The `sys` schema provides human-oriented views over lower-level instrumentation, while Information Schema exposes metadata and server state.

Useful operational questions include:

- Which statements consume the most total time?
- Which tables are scanned heavily?
- Which indexes are unused or ineffective?
- Which sessions are waiting on locks?
- Which objects consume memory or I/O?
- Which replicas are stalled?

## Slow query log

The slow query log can help identify expensive statements over time.

It is most useful when combined with:

- normalized query aggregation;
- execution-plan inspection;
- application request context;
- server resource metrics;
- lock/wait diagnostics.

A slow log entry tells you that a query was slow. It does not by itself explain whether the cause was plan quality, lock waits, cache misses, server overload, or downstream storage latency.

## Capacity model

Important capacity dimensions include:

- active working-set size versus buffer-pool capacity;
- storage throughput and latency;
- redo generation and checkpoint pressure;
- binary-log volume;
- replication apply capacity;
- CPU for query execution;
- connection/thread concurrency;
- temporary-table and sort workload;
- index size and write amplification;
- long-transaction history retention;
- backup and restore bandwidth.

Capacity planning must therefore model the **shape** of workload, not only database size.

## Common performance failure modes

### Missing or ineffective index

Symptoms:

- high rows examined;
- large scans;
- high CPU or storage reads;
- query latency grows with table size.

Check `EXPLAIN`, predicate selectivity, and whether the index ordering matches the access pattern.

### Too many indexes

Symptoms:

- writes become expensive;
- redo/binlog volume rises;
- buffer pool is filled with rarely used index pages;
- DDL/backup operations become larger.

Indexes are not free read accelerators.

### Long transactions

Symptoms:

- lock retention;
- undo history growth;
- purge lag;
- larger recovery/replication pressure;
- schema changes waiting on metadata locks.

### Hot-row contention

Symptoms:

- many sessions serialize around a small set of rows;
- lock wait time rises while CPU may remain moderate.

Scale-out replicas do not solve a write hotspot on one logical row.

### Connection storms

Symptoms:

- CPU spikes during authentication/thread creation;
- memory pressure;
- many short-lived sessions;
- application timeouts even when individual queries are small.

Use sane pooling, connection limits, and admission control.

### Replica lag

Symptoms:

- stale reads;
- failover candidate is behind;
- binary logs accumulate;
- backups from replicas drift from expected freshness.

Fix the cause of receive/apply lag rather than only increasing retention.

### Disk pressure

Disk exhaustion can break:

- data-file growth;
- temporary operations;
- redo behavior;
- binary logging;
- backups;
- replication relay logs.

Monitor both capacity and growth rate.

## Metadata locking

DDL and some metadata operations interact with metadata locks.

A common incident pattern is:

```text
long transaction references table
  -> ALTER TABLE waits for metadata lock
  -> new work queues behind blocked DDL or lock chain
  -> application latency rises broadly
```

The visible blocked statement may not be the original cause. Find the oldest transaction and the full wait chain.

## Operational triage order

When MySQL becomes slow, a useful sequence is:

1. Check whether the server is resource-saturated: CPU, storage latency, memory pressure, disk space.
2. Inspect active sessions and waits.
3. Identify lock chains and long transactions.
4. Check replication receive/apply state if replicas are involved.
5. Find top statements by total time and rows examined.
6. Inspect execution plans for the highest-impact queries.
7. Compare optimizer estimates with actual workload/data distribution.
8. Check buffer-pool, redo, flushing, and temporary-work pressure.
9. Look for a recent schema, configuration, deployment, or traffic change.
10. Only then change indexes or global configuration.

This prevents random tuning from masking the actual failure mode.

## Practical transaction pattern

For a work-queue style operation:

```sql
START TRANSACTION;

SELECT id
FROM jobs
WHERE state = 'ready'
ORDER BY id
LIMIT 1
FOR UPDATE;

UPDATE jobs
SET state = 'running'
WHERE id = ?;

COMMIT;
```

The important lesson is not the exact SQL. It is that **selection and state transition must be designed around concurrency semantics**. Multiple workers can otherwise select the same logical work or block each other unexpectedly. Current releases also provide locking modifiers useful for queue patterns; use them only after understanding starvation and ordering behavior.

## Practical plan workflow

```text
slow request
  -> capture representative SQL + parameters
  -> EXPLAIN
  -> inspect chosen access path and estimates
  -> inspect waits / locks
  -> update statistics if stale
  -> test index/query change with realistic data
  -> measure write and storage cost of the change
```

Do not optimize using only a tiny development dataset.

## Practical backup workflow

A credible recovery plan documents:

```text
backup creation
  -> integrity/metadata verification
  -> retention
  -> off-host or isolated copy
  -> restore into clean environment
  -> replay binary logs if PITR is required
  -> application-level consistency check
  -> measured recovery time
```

The restore step is part of backup engineering, not an optional audit exercise.

## MySQL versus PostgreSQL

Both are mature client/server relational databases, but they differ in ways that affect real systems.

MySQL emphasizes:

- a pluggable storage-engine architecture;
- InnoDB as its dominant transactional engine;
- binary-log-centric replication and recovery workflows;
- a broad ecosystem around MySQL-compatible services and tooling.

PostgreSQL emphasizes a different internal architecture and extensibility model, with its own MVCC, WAL, type/index extension framework, planner behavior, replication primitives, and operational conventions.

Do not choose between them using generic claims such as "faster" or "more scalable." Compare:

- SQL semantics your application depends on;
- indexing and query-planning behavior;
- replication/HA design;
- operational expertise;
- extension requirements;
- migration tooling;
- managed-service constraints;
- licensing and ecosystem compatibility.

## MySQL versus SQLite

SQLite is an embedded database library; MySQL is a networked server.

SQLite is often the better fit for:

- local application state;
- embedded devices;
- single-file distribution;
- low-administration deployments.

MySQL is a better fit when the system needs:

- many network clients;
- server-managed accounts and privileges;
- independent database operations;
- server-side replication and HA tooling;
- centralized resource and concurrency control.

The difference is architectural, not a simple feature-count comparison.

## Managed MySQL-compatible services

Cloud services can expose a MySQL-compatible protocol while changing important operational boundaries such as:

- filesystem access;
- superuser privileges;
- backup implementation;
- replication topology;
- failover behavior;
- extension/plugin availability;
- version cadence;
- parameter control.

Protocol compatibility does not imply identical operational semantics. Read the service-specific documentation in addition to MySQL upstream documentation.

## Common mistakes

- Treating every slow query as an indexing problem.
- Choosing a very wide primary key without accounting for secondary-index amplification.
- Leaving transactions open across user interaction or remote service calls.
- Ignoring deadlock retries.
- Assuming `REPEATABLE READ` behaves like another database's isolation implementation with the same name.
- Treating binary logs as the same thing as InnoDB redo logs.
- Calling a replica "HA" without tested promotion, routing, and fencing.
- Keeping backups without restore drills.
- Purging binary logs without considering PITR and replica requirements.
- Running large DDL without understanding metadata locks and rebuild behavior.
- Giving application users global administrative privileges.
- Scaling connection counts instead of using pooling/admission control.
- Tuning global memory settings without multiplying per-connection/per-operation costs.
- Reading from replicas without defining staleness semantics.

## Learning path

### Beginner

Learn:

1. tables, rows, primary keys, and SQL;
2. transactions and autocommit;
3. basic indexes;
4. users and grants;
5. logical backup and restore;
6. `EXPLAIN`.

### Intermediate

Learn:

1. InnoDB clustered and secondary indexes;
2. buffer-pool behavior;
3. MVCC and isolation levels;
4. locking and deadlocks;
5. optimizer statistics;
6. binary logs and source/replica replication;
7. Performance Schema;
8. online DDL and metadata locking.

### Advanced

Learn:

1. redo, undo, checkpoints, purge, and crash recovery;
2. replication formats and GTIDs;
3. Group Replication certification and failure handling;
4. PITR and disaster-recovery design;
5. optimizer edge cases and histogram/statistics behavior;
6. high-concurrency lock design;
7. capacity modeling from buffer-pool, I/O, redo, binlog, and replica pressure;
8. HA routing/fencing and failure drills;
9. upgrade and compatibility planning.

## What to learn next

- [`database/postgresql`](https://github.com/BLCCoreStudio/OpenDevIndex/tree/database/postgresql/entry) — compare a different client/server relational architecture, MVCC model, WAL system, planner, extensibility model, and replication ecosystem.
- [`database/sqlite`](https://github.com/BLCCoreStudio/OpenDevIndex/tree/database/sqlite/entry) — understand the embedded/single-file database model and its very different concurrency/deployment boundary.
- SQL transaction isolation and serializability concepts — separate database theory from product-specific implementation details.
- B-tree indexing — understand why key order, selectivity, locality, and write amplification affect both performance and locking.
- distributed-systems failure models — essential for reasoning about replication, failover, stale reads, split brain, and fencing.

## Authoritative sources

Primary references for this module include:

- MySQL Reference Manual;
- MySQL Server canonical source repository;
- InnoDB architecture, locking, transaction, redo, and undo documentation;
- optimizer, index, statistics, and `EXPLAIN` documentation;
- binary-log and replication documentation;
- Group Replication documentation;
- backup and point-in-time recovery documentation;
- MySQL account, role, TLS, and security documentation;
- Performance Schema documentation;
- MySQL licensing information.

See [`sources.md`](sources.md) for the curated source list.

## Verification and maintenance

This deep-dive revision was reviewed on **2026-09-06** against current MySQL documentation and the canonical MySQL Server repository.

Facts most likely to age include:

- release/version naming;
- storage-engine and DDL capabilities;
- default settings;
- authentication plugins;
- optimizer features;
- replication defaults;
- Group Replication requirements;
- backup tooling;
- TLS/runtime dependencies;
- upgrade paths and deprecations.

Stable concepts such as the SQL/storage-engine boundary, InnoDB clustered-index model, MVCC/locking interaction, redo/undo distinction, binary-log replication role, and the need for tested recovery should still be rechecked when major architecture changes land.