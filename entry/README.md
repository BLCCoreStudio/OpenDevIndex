# PostgreSQL

> Open-source relational database whose server combines SQL, MVCC transactions, WAL durability, cost-based query planning, extensible types and indexes, replication, and rich operational tooling for transactional and analytical workloads.

PostgreSQL is easiest to reason about as several cooperating systems rather than one monolithic SQL engine:

```text
clients
  |
  v
server processes + authentication
  |
  +--> parser / rewriter / planner / executor
  |
  +--> transaction manager + MVCC snapshots + locks
  |
  +--> shared buffers + relation/index access methods
  |
  +--> WAL durability + checkpoints + crash recovery
  |
  +--> autovacuum / statistics / maintenance
  |
  +--> physical or logical replication
  |
  v
cluster data directory + WAL + tablespaces
```

The central operational idea is that **logical database state, physical row versions, WAL history, planner statistics, and maintenance state all interact**. Many production PostgreSQL incidents are not caused by invalid SQL. They are caused by long-lived transactions, stale statistics, vacuum starvation, lock chains, replication-slot retention, overloaded connection models, unsafe schema migrations, or backup/recovery assumptions that were never tested.

## Product boundary

PostgreSQL itself provides:

- a client/server relational database engine;
- SQL execution and transaction semantics;
- MVCC concurrency control;
- indexes and extensible access methods;
- roles and authentication hooks;
- WAL-based durability and crash recovery;
- physical streaming replication;
- logical replication primitives;
- backup and point-in-time recovery tooling;
- extension infrastructure;
- monitoring statistics and server logs.

PostgreSQL does **not** by itself provide a complete distributed-control plane for automatic multi-node failover, global consensus, connection routing, managed backups, cross-region topology, or elastic sharding. Managed database services and external HA/orchestration systems can provide those capabilities, but their failure semantics are separate from PostgreSQL Core.

## Process architecture

A PostgreSQL server installation operates a database **cluster**: a collection of databases managed by one server instance and one primary data directory.

The main server process accepts connections and starts backend processes for client sessions. PostgreSQL also runs background processes for responsibilities such as:

- checkpointer activity;
- background buffer writing;
- WAL writing;
- autovacuum coordination and workers;
- WAL archiving when configured;
- replication sender/receiver work;
- logical replication workers;
- other version- or extension-specific background work.

A useful mental model is:

```text
one client connection
      |
      v
one backend process
      |
      +--> private memory
      +--> shared memory/buffers
      +--> shared lock tables
      +--> WAL insertion
      +--> relation files
```

This process-per-connection model is one reason connection count is an architectural capacity concern rather than a free scalar.

## Connection lifecycle

A connection roughly passes through:

```text
TCP / Unix socket
  -> SSL negotiation if configured
  -> pg_hba.conf rule selection
  -> authentication
  -> database + role session setup
  -> backend process executes SQL
```

Every long-lived connection consumes server resources. Large fleets of mostly idle application connections can therefore waste memory and process capacity even before query load becomes high.

Connection pooling is commonly used to decouple application concurrency from backend-process count. Pooling changes session semantics, so applications must understand whether the pooler operates in session, transaction, or statement-like modes and whether session-local state is safe to depend on.

## Cluster, database, schema, relation

The word `cluster` in PostgreSQL does not mean an HA cluster. It historically means the set of databases managed by one PostgreSQL server instance/data directory.

Logical hierarchy:

```text
PostgreSQL cluster
  -> database
      -> schema
          -> table / view / sequence / function / type / index / ...
```

A connection is made to one database. Cross-database SQL is not the same as cross-schema SQL; ordinary queries cannot simply reference arbitrary tables in another database by three-part naming.

Schemas are namespaces inside one database. They are useful for ownership and organization but are not independent security sandboxes unless privileges and `search_path` are designed carefully.

## `search_path` is a security boundary

Unqualified names are resolved using `search_path`.

If an untrusted user can create objects in a schema that appears before trusted schemas in another user's `search_path`, name resolution can become dangerous for functions/operators/types in security-sensitive SQL.

For privileged code:

- schema-qualify important objects;
- control `CREATE` privileges on schemas;
- set a safe `search_path` for security-definer functions;
- do not assume the default namespace configuration is suitable for multi-tenant trust boundaries.

## Query pipeline

A SQL statement passes through several conceptual phases:

```text
SQL text
  -> parse tree
  -> semantic analysis / rewrite
  -> planner / optimizer
  -> executable plan tree
  -> executor
  -> access methods / buffer manager
  -> rows
```

The planner estimates alternative costs. It does not search every theoretically possible plan for complex queries; it uses algorithms and heuristics to find a practical plan within planning cost constraints.

The executor then runs the selected plan against the snapshot visible to the transaction.

## Cost-based planning

PostgreSQL's planner uses estimates such as:

- table/index page counts;
- estimated row counts;
- value distributions;
- null fractions;
- distinct-value estimates;
- most-common values;
- histograms;
- extended/multivariate statistics when created;
- configured cost parameters;
- available indexes and join strategies.

Statistics are approximate and can become stale when table contents change significantly.

This means a slow query can be caused by either:

```text
bad plan because estimates were wrong
```

or:

```text
good estimated plan but execution was expensive
```

Those require different fixes.

## `ANALYZE`

`ANALYZE` samples table data and updates planner statistics.

Autovacuum normally performs automatic analyze work based on table change thresholds, but unusual workloads can need table-specific tuning or manual analysis after large bulk changes.

Do not create indexes blindly before checking whether the real problem is a severe cardinality estimate error caused by stale or insufficient statistics.

## Extended statistics

Single-column statistics cannot represent every correlation between columns.

PostgreSQL supports extended statistics objects for cases where estimates depend on relationships such as:

- correlated predicates;
- functional dependencies;
- multi-column distinct counts;
- multi-column most-common-value combinations.

Use them when `EXPLAIN` shows large systematic row-estimate errors that ordinary per-column statistics cannot model.

## `EXPLAIN`

`EXPLAIN` shows the planner's chosen plan without executing the query by default.

```sql
EXPLAIN
SELECT *
FROM orders
WHERE customer_id = 42;
```

A plan is a tree. Common nodes include:

- sequential scan;
- index scan;
- index-only scan;
- bitmap scan;
- nested-loop join;
- hash join;
- merge join;
- sort;
- aggregate;
- materialize;
- gather / parallel nodes.

The cost numbers are planner units, not milliseconds.

## `EXPLAIN ANALYZE`

`EXPLAIN ANALYZE` actually executes the statement and reports observed timing and row counts.

For read-only investigation:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT ...;
```

Be careful with write statements:

```sql
EXPLAIN ANALYZE DELETE ...;
```

executes the deletion.

For risky statements, use a safe test environment or an explicit transaction that is rolled back when that accurately represents the operation.

The most useful comparison is often:

```text
estimated rows vs actual rows
```

Large differences reveal planner-model problems.

## MVCC

PostgreSQL uses Multi-Version Concurrency Control.

Instead of overwriting a row version in place in the simple conceptual model, updates create a new tuple version while old versions remain until no longer needed and later reclaimed by vacuum.

Each statement/transaction sees rows according to a snapshot and transaction visibility rules.

This lets readers and writers avoid many conflicts that would occur in a locking-only design.

Conceptually:

```text
row version A
  xmin = transaction that created A
  xmax = transaction that deleted/replaced A, if any

UPDATE
  -> old version becomes obsolete for future snapshots
  -> new version B created
```

The actual tuple-header and visibility machinery is more detailed, but this model explains why old row versions exist and why vacuum is fundamental.

## Snapshots

A snapshot defines which transactions/tuple versions are visible to a statement or transaction.

Long-running transactions can keep old snapshots alive. That matters because vacuum cannot remove row versions that may still be visible to an active snapshot.

A transaction that appears idle at the application layer can therefore cause storage and maintenance problems if it remains open for hours.

## Transaction isolation

PostgreSQL exposes standard transaction isolation levels with PostgreSQL-specific semantics.

### Read Committed

The default isolation level. Each command sees a snapshot as of the beginning of that command, with rules for concurrent updates.

Two statements in the same transaction can therefore observe different committed data.

### Repeatable Read

The transaction sees a stable snapshot for ordinary reads after its snapshot is established. PostgreSQL's implementation prevents some anomalies beyond the minimum SQL standard requirements, but serialization conflicts can still require transaction retries in appropriate cases.

### Serializable

PostgreSQL implements serializable isolation using Serializable Snapshot Isolation techniques. Transactions can be aborted with serialization failures to preserve behavior equivalent to some serial execution order.

Applications using serializable isolation **must be designed to retry serialization failures**.

### Read Uncommitted

PostgreSQL treats Read Uncommitted as Read Committed because uncommitted tuple versions are not exposed in the usual dirty-read sense.

## Transaction retry discipline

Retries should encompass the full logical transaction, not just the final SQL statement.

Bad:

```text
BEGIN
read data
calculate decision
UPDATE -> serialization failure
retry UPDATE only
COMMIT
```

The calculation was based on a snapshot that no longer applies.

Better:

```text
retry loop:
  BEGIN
  read data
  calculate decision
  write
  COMMIT
```

Deadlocks can also abort a transaction and may require retry depending on the application operation.

## Locks

MVCC does not remove the need for locks.

PostgreSQL uses multiple lock classes, including:

- table-level locks;
- row-level locks;
- page-level internal locks;
- advisory locks;
- lightweight/internal synchronization mechanisms.

DDL often requires stronger table locks than ordinary DML.

A migration that is syntactically simple can therefore block production if it waits for a lock held by a long transaction.

## Row locking

Statements such as:

```sql
SELECT ... FOR UPDATE;
SELECT ... FOR NO KEY UPDATE;
SELECT ... FOR SHARE;
SELECT ... FOR KEY SHARE;
```

can lock selected rows for coordination.

Use them when application invariants require explicit conflict management, but keep the locking transaction short.

## Deadlocks

A deadlock occurs when transactions form a wait cycle.

Example:

```text
T1 holds row A, waits for row B
T2 holds row B, waits for row A
```

PostgreSQL detects deadlocks and aborts one transaction.

Reduce deadlocks by:

- acquiring resources in consistent order;
- keeping transactions short;
- avoiding user/network waits inside transactions;
- locking only what the invariant requires;
- retrying aborted transactions where safe.

## Advisory locks

Advisory locks provide application-defined lock keys not directly tied to one row or table.

They can coordinate operations such as leader-like jobs or migrations, but the database does not understand the business meaning of the key.

Document a global key convention. Two applications accidentally reusing the same advisory-lock key can interfere with each other.

## Heap storage

Ordinary PostgreSQL tables use heap storage managed in relation files divided into pages.

Rows are tuples stored on pages. Indexes store references that ultimately identify heap tuples unless the access path can satisfy an index-only scan using visibility information.

The physical layout is intentionally abstracted from SQL users, but operators need to understand that:

- updates can leave old tuple versions;
- free space is tracked for reuse;
- table and index bloat can develop under some workloads;
- vacuum changes what space can be reused;
- `VACUUM FULL` has very different locking/rewrite behavior from ordinary vacuum.

## TOAST

Large field values can be compressed and/or stored out of line through PostgreSQL's TOAST mechanism when needed.

This makes wide rows practical but means the logical row size seen by an application does not map directly to one inline heap tuple.

Repeatedly reading a small subset of columns can therefore be much cheaper than selecting large toasted columns unnecessarily.

## MVCC tuple churn

An update can create a new row version even when only one logical row appears to change.

High-update workloads therefore create maintenance work proportional to **version churn**, not only current live row count.

Watch:

- dead tuple estimates;
- autovacuum frequency/duration;
- transaction age;
- table/index growth;
- WAL volume;
- replica lag.

## HOT updates

Heap-Only Tuple updates can reduce index maintenance when an update does not change indexed columns and the new tuple version can be placed appropriately on the same heap page.

HOT is a performance optimization, not a semantic guarantee.

Schema/index design and table fill factor can influence whether workloads benefit from HOT behavior.

## VACUUM

`VACUUM` is not optional housekeeping. It is part of normal MVCC operation.

Ordinary vacuum can:

- mark space from dead tuples reusable;
- update visibility information;
- help index cleanup;
- freeze sufficiently old transaction IDs;
- update statistics when `ANALYZE` is requested.

Ordinary vacuum generally does not shrink a table file back to the operating system merely because rows were deleted. It makes space reusable inside the relation.

## Autovacuum

Autovacuum automates vacuum and analyze based on activity thresholds and safety requirements.

Important operational principle:

```text
high-write table
  -> more dead tuples
  -> more vacuum work
  -> may need per-table autovacuum tuning
```

A single global threshold is rarely optimal for both a tiny, intensely updated queue table and a multi-terabyte append-heavy fact table.

## Transaction ID wraparound

PostgreSQL transaction IDs have finite-width semantics and old tuple metadata must be frozen before transaction-age limits become unsafe.

Autovacuum has anti-wraparound behavior for this reason.

Never disable or block vacuum indefinitely on the assumption that disk bloat is the only consequence. Transaction-ID age can become a database availability risk.

Monitor database/table age rather than waiting for emergency anti-wraparound vacuum behavior.

## Long transactions and vacuum

A common chain is:

```text
application opens transaction
  -> holds old snapshot
  -> application waits/forgets to commit
  -> vacuum cannot remove versions still potentially visible
  -> dead tuples accumulate
  -> table/index/WAL pressure grows
  -> query performance degrades
```

Monitor `pg_stat_activity` for long-running and `idle in transaction` sessions.

Set application and database timeouts deliberately rather than allowing abandoned transactions to live indefinitely.

## `VACUUM FULL`

`VACUUM FULL` rewrites a table to compact it and can return space to the operating system, but it requires a strong table lock and extra temporary disk space.

It is not a routine substitute for properly tuned autovacuum.

Before using it on a large production table, plan for:

- blocking duration;
- rewrite I/O;
- WAL generation;
- replica effects;
- extra disk capacity;
- maintenance window.

## Visibility map

PostgreSQL tracks pages known to contain tuples visible to all transactions through the visibility map.

This matters for both vacuum behavior and index-only scans.

An index may contain every column a query needs, but PostgreSQL can still need heap visibility checks unless the relevant heap pages are known all-visible.

Maintenance quality therefore influences read-path performance.

## Write-ahead logging

PostgreSQL uses WAL so changes needed for recovery are recorded before the corresponding data-page modifications must reach durable storage.

Conceptually:

```text
transaction modifies shared buffers
       |
       v
WAL records generated
       |
COMMIT waits for required WAL durability
       |
       v
data pages may be written later
```

After a crash, PostgreSQL can replay WAL from a checkpoint to restore a consistent state.

## WAL is not a backup by itself

WAL provides the change stream needed for crash recovery, replication, and point-in-time recovery, but recoverability requires a valid base backup plus the required WAL history and configuration.

If the base backup is corrupt or the WAL archive has gaps, a nominally configured archive does not provide a usable recovery chain.

Test restore procedures.

## Checkpoints

A checkpoint establishes a recovery boundary and forces dirty-buffer progress toward durable data files.

Checkpoint frequency influences:

- crash recovery duration;
- write I/O patterns;
- WAL volume from full-page images after checkpoints;
- background write pressure.

Very frequent checkpoints can create avoidable I/O spikes. Very infrequent checkpoints can lengthen recovery and require more WAL/storage headroom.

Tune from workload evidence rather than copying one universal value.

## Durability settings

Settings such as `fsync`, `synchronous_commit`, and `full_page_writes` affect durability/performance trade-offs.

Treat durability reductions as explicit data-loss decisions, not ordinary performance knobs.

For example, relaxing synchronous commit for a workload can allow recent committed transactions to be lost on a crash while preserving database consistency. Disabling stronger durability mechanisms can have more severe consequences.

Know the failure model before changing these settings.

## WAL volume

WAL generation grows with write workload and can be amplified by:

- large bulk updates;
- index changes;
- table rewrites;
- full-page images;
- logical decoding needs;
- maintenance operations;
- schema changes that rewrite data.

WAL affects primary disk, archive volume, network replication, replica catch-up, and recovery time.

Capacity planning should include WAL throughput and retention, not only table size.

## Index families

PostgreSQL provides multiple index access methods because no single index structure fits every operator/data distribution.

### B-tree

The default general-purpose index. Strong for equality, ordering, and range predicates supported by the operator class.

Typical:

```sql
CREATE INDEX orders_created_at_idx
ON orders (created_at);
```

### Hash

Designed for equality comparisons.

### GiST

A generalized balanced-tree framework used by data types/operator classes such as geometric, range, nearest-neighbor, and extension-defined searches.

### SP-GiST

Supports space-partitioned structures useful for certain non-balanced search trees and specialized data types.

### GIN

An inverted index suited to composite/multi-valued content such as arrays, full-text search, and common `jsonb` containment/search patterns.

### BRIN

Stores summaries over physical block ranges and can be extremely compact for very large tables whose indexed values correlate with physical row order.

A BRIN index is not a tiny B-tree. It trades precision for compact range summaries.

## Multicolumn indexes

Column order matters.

For a B-tree index:

```sql
CREATE INDEX idx
ON events (tenant_id, created_at);
```

is structurally different from:

```sql
CREATE INDEX idx
ON events (created_at, tenant_id);
```

Design indexes from real predicate, join, ordering, and cardinality patterns rather than creating every permutation.

## Partial indexes

A partial index covers rows satisfying a predicate.

Example:

```sql
CREATE INDEX jobs_ready_idx
ON jobs (scheduled_at)
WHERE state = 'ready';
```

This can be highly efficient when the indexed subset is small and queries use a predicate the planner can prove compatible.

## Expression indexes

Indexes can store expression results:

```sql
CREATE INDEX users_lower_email_idx
ON users (lower(email));
```

Then queries using the corresponding expression can use the index.

Expression indexes add write cost, so treat them like materialized computation maintained on every relevant row change.

## Index-only scans

An index-only scan can answer a query from the index without visiting heap pages for data values, but MVCC visibility still must be proven.

The visibility map allows PostgreSQL to skip many heap visits for all-visible pages.

This is why aggressive churn can reduce the expected benefit of an otherwise covering index until vacuum catches up.

## Too many indexes

Every index adds costs:

- insert/update/delete work;
- WAL volume;
- vacuum/index cleanup work;
- disk space;
- cache pressure;
- planner alternatives;
- rebuild/backup/restore time.

Unused or redundant indexes can make writes slower without improving reads.

Use workload statistics and `EXPLAIN` rather than indexing by intuition alone.

## Constraints and indexes

Primary-key and unique constraints normally create supporting unique indexes.

Foreign keys do not automatically imply every useful index on the referencing side for all workloads.

For frequently updated/deleted referenced rows, indexing foreign-key columns in referencing tables is often important to avoid expensive checks and locking behavior.

## SQL transactions

A transaction groups statements atomically:

```sql
BEGIN;

UPDATE accounts
SET balance = balance - 100
WHERE id = 1;

UPDATE accounts
SET balance = balance + 100
WHERE id = 2;

COMMIT;
```

The application must still define the business invariant correctly. ACID semantics cannot fix an incomplete transaction that omits part of the invariant.

## Savepoints

Savepoints allow partial rollback within a transaction:

```sql
SAVEPOINT before_optional_step;
...
ROLLBACK TO SAVEPOINT before_optional_step;
```

They are useful for controlled recovery from expected sub-operation failures, but excessive nested error handling can make transaction logic hard to reason about.

## Constraints as concurrency tools

Prefer database-enforced invariants when the rule fits relational constraints:

- `PRIMARY KEY`;
- `UNIQUE`;
- `FOREIGN KEY`;
- `CHECK`;
- `NOT NULL`;
- exclusion constraints.

Application-side “check then insert” logic can race under concurrency when the database could enforce the invariant directly.

## Upsert

`INSERT ... ON CONFLICT` provides atomic conflict-aware insertion/update behavior for suitable uniqueness conflicts.

Example:

```sql
INSERT INTO counters (key, value)
VALUES ('downloads', 1)
ON CONFLICT (key)
DO UPDATE SET value = counters.value + 1;
```

The exact concurrency semantics depend on isolation level, unique index inference, and the statement shape. Use the database primitive rather than emulating upsert with a racy select-before-insert sequence.

## Sequences

Sequences generate values independently from ordinary transactional rollback semantics.

A transaction that consumes a sequence value and later rolls back can leave a gap.

Do not design business requirements around gapless sequence-generated IDs unless you implement a different serialization model and accept its cost.

Sequence uniqueness and table uniqueness are different concerns; enforce the table key with an actual constraint.

## Data types

PostgreSQL includes rich built-in types beyond generic strings/numbers, including:

- exact and approximate numerics;
- timestamps/time zones/intervals;
- UUID;
- arrays;
- `json` and `jsonb`;
- ranges and multiranges;
- network addresses;
- geometric types;
- text-search types;
- enumerated types;
- composite/domain types.

Use types to make invalid states harder to represent, but consider compatibility and migration costs before adopting highly specialized types in public interfaces.

## `json` versus `jsonb`

`json` preserves the input text representation. `jsonb` stores a decomposed binary representation optimized for processing and indexing.

For application data that must be queried and indexed, `jsonb` is often the more operationally useful choice.

Do not use JSON as an excuse to discard relational modeling entirely. Frequently filtered/joined fields with strong constraints can be better represented as typed columns.

## JSON indexing

GIN indexes can accelerate common `jsonb` containment/key-style queries depending on operator class.

Before indexing large JSON documents:

- inspect real query operators;
- choose the matching operator class;
- measure index size and write cost;
- consider extracting heavily queried keys into ordinary columns.

## Arrays

Arrays are first-class PostgreSQL values and can be indexed with suitable operator classes.

They are useful when the data is truly an attribute collection of one row.

They are not always a substitute for normalized many-to-many relationships when referential integrity, independent row lifecycle, or complex joins matter.

## Extensions

PostgreSQL is intentionally extensible.

Extensions can add:

- SQL functions;
- procedural languages;
- data types;
- operators;
- index operator classes/access methods;
- background workers;
- foreign data wrappers;
- monitoring capabilities.

`CREATE EXTENSION` installs a packaged extension into a database when privileges and server installation allow it.

Extensions execute inside or alongside a highly privileged database process environment. Treat native-code extensions as server supply-chain dependencies.

## Extension upgrade discipline

Before upgrading PostgreSQL major versions or extension versions:

- inventory installed extensions;
- verify supported target versions;
- test extension upgrade scripts;
- test dump/restore or binary upgrade paths;
- review shared-library compatibility;
- confirm managed-service extension availability if moving platforms.

An application can be portable across PostgreSQL versions while a required extension is not.

## Partitioning

Declarative table partitioning can divide a logical table into child partitions by strategies such as range, list, or hash.

Partitioning can help with:

- pruning irrelevant data ranges;
- lifecycle management of time/range chunks;
- bulk detach/drop operations;
- maintenance boundaries;
- some very large-table access patterns.

It is not an automatic performance upgrade.

Too many partitions can increase planning/metadata overhead, and poor partition keys can make queries touch most partitions anyway.

## Partition pruning

The planner/executor can avoid scanning partitions whose constraints cannot satisfy a query predicate.

Design partition keys around real query and retention boundaries so pruning can work.

A date-partitioned table does not help a query that filters only by unrelated customer attributes unless another access path handles it.

## Unique constraints on partitioned tables

Global uniqueness across partitions has structural restrictions because the database must be able to enforce the constraint using partition-local indexes under supported rules.

Plan identity keys before adopting partitioning; do not discover during migration that a required global uniqueness rule conflicts with the partition key design.

## Logical versus physical backup

### Logical backup

`pg_dump` exports database objects/data into a logical representation that can be restored with PostgreSQL tools.

Advantages:

- selective database/object backup;
- useful across supported version migration scenarios;
- inspectable logical structure.

Trade-offs:

- restore can be CPU/time intensive for very large databases;
- does not capture the entire cluster byte-for-byte;
- global objects require separate handling with tools such as `pg_dumpall --globals-only` where relevant.

### Physical backup

A base backup captures the physical database cluster files in a recovery-consistent manner.

`pg_basebackup` can create a physical base backup from a running server through the replication protocol.

Physical backup is cluster-wide and couples recovery to physical/server compatibility rules.

## Point-in-time recovery

PITR combines:

```text
base backup
+ archived WAL after that base backup
+ recovery target
```

This can restore the cluster to a selected time/transaction boundary supported by recovery configuration.

The archive must contain an unbroken WAL chain covering the target interval.

A backup system should test:

- newest restore;
- historical point-in-time restore;
- missing-WAL detection;
- corrupted backup detection;
- key/certificate availability;
- time required to restore and replay.

## RPO and RTO

Backup design should start with business recovery targets:

- **RPO**: how much committed data can be lost?
- **RTO**: how long can recovery take?

A daily `pg_dump` has a different RPO/RTO profile from continuous WAL archiving plus frequent physical backups and replicas.

Replication is not a replacement for backup because destructive or malicious changes can replicate too.

## Physical streaming replication

Physical replication sends WAL changes from a primary to standby servers.

A standby replays WAL to maintain a physical copy of the cluster.

This supports:

- warm/hot standbys;
- read-only queries on hot standby when configured;
- HA topologies;
- offloading some read workloads.

Replication transport does not by itself choose which standby should be promoted or how clients should discover the new primary.

## Asynchronous replication

In asynchronous replication, primary commit does not wait for a standby to durably acknowledge every transaction.

Benefits:

- lower primary commit latency;
- tolerance of temporarily slow/unavailable replicas.

Trade-off:

- a failover can lose recent committed transactions not yet replicated.

Monitor replication lag in the units that matter: bytes/WAL position, time, and recovery impact.

## Synchronous replication

Synchronous replication can make commits wait for configured standby acknowledgement levels.

This can reduce failover data-loss exposure but adds network/standby health to the commit latency and availability path.

Design quorum/name settings carefully. A synchronous standby outage can stall commits if the configuration requires an acknowledgement that can no longer arrive.

## Replication slots

Replication slots preserve required WAL/data visibility for consumers so the primary does not discard needed history too early.

They are valuable and dangerous.

A disconnected consumer with an unconstrained slot can cause retained WAL to grow until disk fills.

Monitor:

- slot activity;
- retained WAL;
- consumer lag;
- abandoned slots.

Treat slot lifecycle as storage-capacity ownership.

## Hot standby conflicts

Read queries on a standby can conflict with WAL replay when the primary removed or changed data needed by the standby query snapshot.

PostgreSQL can delay replay or cancel conflicting standby queries depending on configuration and conflict type.

This creates a real trade-off:

```text
fresh replica
vs
allow long analytical queries to finish
```

Do not assume a read replica is an unlimited analytical warehouse.

## Logical replication

Logical replication publishes logical table changes and subscribes to them rather than replaying the entire physical cluster byte stream.

Core concepts include:

```text
publisher
  -> publication
  -> logical decoding / WAL
  -> replication protocol
  -> subscriber subscription
  -> apply worker
```

Logical replication is useful for:

- selective table replication;
- some migrations/upgrades;
- data distribution/integration;
- different physical layouts on subscribers.

It has different DDL, sequence, conflict, and operational behavior from physical replication. Do not treat it as a drop-in HA replica without understanding those differences.

## Logical replication and schema changes

Logical replication does not make arbitrary schema evolution automatic across publisher and subscriber.

Coordinate compatible table definitions and DDL changes carefully.

A producer changing column layout/types without compatible subscriber preparation can break replication apply.

## Replication security

Replication connections need powerful capabilities and access to WAL/logical change streams.

Use:

- dedicated replication roles;
- narrow `pg_hba.conf` rules;
- TLS where transport trust requires it;
- network restrictions;
- monitored slots/subscriptions;
- minimal logical publication scope.

Logical replication can expose row data even if application-level row-security assumptions would otherwise limit a normal user.

## Roles

PostgreSQL uses roles for both users and groups of privileges.

A role can have attributes such as:

- login capability;
- database creation;
- role creation;
- replication;
- bypass row-level security;
- superuser.

Prefer group-role patterns:

```text
application_login -> member of app_readwrite
analyst_login     -> member of analytics_read
```

rather than granting many object privileges independently to every human/service account.

## Superuser

PostgreSQL superuser bypasses nearly all permission checks.

Applications should not connect as superuser.

Reserve superuser access for operations that truly require it, and use managed-service administrative roles according to the provider's model when direct superuser is unavailable.

## `pg_hba.conf`

Host-based authentication rules determine which authentication method is used for a connection based on attributes such as connection type, database, role, and client address.

Rules are evaluated in order; the first matching record is used.

This makes file order security-critical.

Avoid broad rules such as all databases/all roles/all networks unless they are intentionally inside a stronger trusted boundary.

## Password authentication

Prefer SCRAM-based password authentication for password use where client compatibility permits.

Store password verifiers, not plaintext database passwords, in PostgreSQL's role catalog. The application still needs a secret-management mechanism for its actual credential.

Rotate database credentials and avoid embedding them in connection strings committed to source control.

## TLS

TLS can protect client/server traffic and authenticate the server when clients validate certificates correctly.

Encryption without certificate verification can still permit connections to an unexpected endpoint.

For high-trust environments, define:

- CA trust;
- hostname verification;
- certificate rotation;
- whether client certificates are used;
- minimum protocol/cipher policy according to current PostgreSQL/OpenSSL/platform guidance.

## Row-level security

Row Security Policies can restrict which rows a role can select or modify.

RLS is useful for some multi-tenant designs, but policy correctness is security-critical.

Important boundaries include:

- table owners normally have special behavior unless forced RLS is used appropriately;
- superusers and roles with `BYPASSRLS` bypass policies;
- security-definer functions and views can change effective privilege context;
- query design and leakproof-function behavior matter to policy evaluation safety.

Test policies under the actual application role, not only as an administrator.

## Privilege defaults

New objects receive privileges based on owner/default privilege configuration, not on what an operator remembers the last project did.

Use explicit migrations to set:

- schema `USAGE` / `CREATE`;
- table privileges;
- sequence privileges;
- function execute privileges;
- default privileges for future objects.

Security drift often appears when a deployment creates new tables under a different owner than expected.

## Security-definer functions

`SECURITY DEFINER` executes with function-owner privileges.

Treat such functions like privileged server-side code:

- use a safe `search_path`;
- schema-qualify sensitive references;
- validate inputs;
- revoke unwanted default `EXECUTE` privileges;
- keep owner privileges minimal.

A small SQL/PLpgSQL function can become a privilege-escalation path if namespace resolution is unsafe.

## Query cancellation and timeouts

Operationally useful timeout controls include transaction/session/statement and lock-related limits depending on version and context.

Use them to bound failure domains:

- runaway analytical query;
- lock wait during deployment;
- abandoned transaction;
- idle client session.

Timeouts should align with application retry semantics. A database cancel does not automatically mean the application operation is safe to repeat.

## Connection storms

A primary can become unhealthy from connection establishment pressure before CPU utilization from useful SQL reaches 100%.

Triggers include:

- autoscaling application fleets;
- pooler restart;
- network flap causing mass reconnect;
- server failover;
- retry loops without jitter/backoff.

Mitigations:

- connection pooling;
- bounded application pools;
- exponential backoff/jitter;
- capacity reserved for administrators/monitoring;
- separate pool policies for interactive and batch workloads.

## Memory model

PostgreSQL memory is not one global cache number.

Important categories include:

- shared memory such as `shared_buffers`;
- per-backend/process memory;
- per-plan-node work memory for sorts/hashes;
- maintenance memory for operations such as index creation/vacuum;
- operating-system cache;
- extension/background-worker memory.

A setting named `work_mem` can be consumed multiple times in one query and across many concurrent sessions.

Capacity reasoning should approximate:

```text
concurrent memory-intensive plan nodes
x work_mem
+ backend overhead
+ shared memory
+ OS/services
```

not simply `max_connections * work_mem` or one copied tuning formula.

## `shared_buffers`

`shared_buffers` controls PostgreSQL's shared buffer cache size.

Larger is not always better. PostgreSQL also relies on the operating-system page cache, and excessively large shared buffers can change checkpoint/write behavior.

Tune with workload measurement and memory headroom.

## `work_mem`

`work_mem` sets a threshold for memory available to individual query operations such as sorts and hashes before they spill or partition work.

One query can use multiple work-memory allocations, and parallel workers can multiply memory use.

Raise it selectively for known analytical workloads when possible rather than globally to a huge value on a high-concurrency OLTP server.

## `maintenance_work_mem`

Maintenance operations such as vacuum and index creation can use separate maintenance memory limits.

Large maintenance memory may speed some operations but multiplies with concurrent workers/tasks. Autovacuum has its own control path for maintenance-memory behavior.

## Query parallelism

PostgreSQL can use parallel query plans when the planner judges them beneficial and the operation is parallel-safe.

Parallelism can reduce latency for large scans/aggregations but consumes additional workers, memory, I/O, and CPU.

On a high-concurrency OLTP system, maximizing parallelism per query can reduce total throughput.

## `pg_stat_activity`

`pg_stat_activity` is a primary live view for sessions/backends.

Use it to inspect:

- connection state;
- active query;
- transaction start time;
- query start time;
- wait event/type;
- application/client identity;
- backend type.

When diagnosing a lock incident, start with blockers and transaction age rather than killing random slow queries.

## Wait events

A session that is “slow” may actually be waiting on:

- a lock;
- disk I/O;
- WAL flush;
- client read/write;
- IPC;
- buffer pin;
- extension/other wait classes.

Wait-event information is often more actionable than CPU percentage alone.

## Database and table statistics

Statistics views expose counters for:

- transactions;
- tuples read/written;
- cache hits;
- scans;
- vacuum/analyze activity;
- dead/live tuple estimates;
- replication;
- WAL and background writer/checkpointer activity in version-specific views.

Treat counters as time-series signals. One snapshot without baseline/rate context can be misleading.

## `pg_stat_statements`

The `pg_stat_statements` extension tracks normalized query execution statistics and is one of the most useful tools for workload-level SQL performance analysis.

It can help identify:

- highest total-time queries;
- high call-count queries;
- queries with high average latency;
- planning/execution patterns depending on configuration/version.

Because it is an extension, enable and configure it deliberately, and understand reset/retention behavior when using it for incident history.

## Slow-query investigation

A disciplined workflow:

1. identify the normalized query and latency distribution;
2. capture parameters/data shape where safe;
3. run `EXPLAIN`;
4. inspect estimated row counts;
5. in a safe context run `EXPLAIN ANALYZE` with buffers;
6. compare estimated vs actual rows;
7. inspect indexes and table statistics;
8. inspect waits and concurrent blockers;
9. check temp-file/spill behavior;
10. check whether plan changed after statistics/schema/version change;
11. fix the data model/query/index/statistics rather than forcing a plan blindly.

## DDL is production work

Schema migration statements can acquire strong locks or rewrite large amounts of data.

Risky categories include:

- table rewrites;
- index builds without online/concurrent strategy where supported;
- adding constraints that validate existing rows;
- changing data types;
- changing partition layout;
- dropping objects;
- long-running `ALTER TABLE` waiting for a lock then suddenly acquiring it.

Test the exact migration on representative data and understand lock levels before production.

## Lock timeout for migrations

For migrations that should fail fast rather than block production indefinitely, a short, deliberate lock timeout can be safer than waiting unbounded for an exclusive lock.

This turns:

```text
deployment waits 40 minutes -> finally acquires lock -> blocks traffic
```

into a controlled migration failure that can be retried during a safer window.

Choose retry semantics carefully; do not loop aggressively and create a lock storm.

## Concurrent index creation

PostgreSQL supports concurrent index build modes that reduce blocking of ordinary writes compared with a normal index build, at the cost of more work/time and additional failure states.

A failed concurrent build can leave an invalid index that must be handled explicitly.

Understand the exact restrictions before using it in automated migrations.

## Constraint rollout pattern

For some large-table constraints, production rollout can be staged so the database begins enforcing new changes and validates existing data separately, where PostgreSQL supports that constraint workflow.

The general engineering principle is:

```text
separate lock-heavy metadata operation
from
long existing-data validation
```

when supported, rather than combining them into one outage-prone step.

## Major-version upgrades

Major PostgreSQL versions can require a migration/upgrade process rather than binary replacement in place.

Common strategies include:

- logical dump/restore;
- `pg_upgrade` with supported source/target versions;
- logical replication migration;
- managed-service provider workflows.

Before upgrade:

- inventory extensions;
- validate client/driver compatibility;
- test application SQL;
- test backup restore;
- benchmark critical queries;
- review release notes and changed defaults;
- plan rollback before state becomes irreversible.

## Query-plan changes after upgrade

A major upgrade can change planner behavior even when SQL semantics remain valid.

Do not define upgrade success only as “server starts and tests pass.”

Capture representative workload/query plans before and after upgrade and watch:

- latency regressions;
- changed join order;
- new/removed parallelism;
- estimate changes;
- index selection;
- extension behavior.

## Backup verification

A backup is only proven when a restore succeeds.

Automated backup verification should periodically:

1. restore into isolated infrastructure;
2. start PostgreSQL;
3. verify expected databases/roles/extensions;
4. run integrity/application smoke checks;
5. verify recovery point/timestamp;
6. measure restore duration;
7. delete the test environment safely.

Keep restore credentials/keys available through a documented disaster path.

## High availability architecture

A typical HA stack has layers:

```text
PostgreSQL primary + standbys
        |
        +-- replication / slots
        |
external failover manager / control plane
        |
load balancer / DNS / proxy / service discovery
        |
clients / poolers
```

Every layer can disagree during failure.

A robust design answers:

- who decides promotion?
- how is split-brain prevented?
- how is the old primary fenced?
- how do clients discover the new primary?
- what RPO is accepted?
- what happens to synchronous replication?
- how are stale writes rejected?
- how is the failed node rejoined safely?

## Failover is not switchover

A planned switchover can wait for replicas to catch up and coordinate client cutover.

An emergency failover occurs under uncertainty and may involve data loss or divergent histories.

Test both paths. A clean switchover test does not prove emergency failover behavior.

## Split brain

If two nodes accept writes after an unsafe failover, PostgreSQL does not automatically merge divergent physical histories.

External HA systems must prevent or fence the old primary before clients can continue safely.

This is why “promote the replica” is not a complete HA design.

## Logical data modeling

PostgreSQL performs best when the schema makes data relationships and invariants explicit.

Use normalization when it reduces duplication and protects consistency, then denormalize selectively when measured workloads justify it.

Schema design dimensions include:

- primary-key width/stability;
- foreign-key relationships;
- nullability;
- uniqueness;
- data type size/semantics;
- update frequency;
- access paths;
- partition/retention boundaries;
- multi-tenant ownership.

Do not choose a UUID, sequence, JSON document, or composite natural key by fashion alone; each affects indexes, locality, migration, and external identity semantics.

## SQL injection boundary

Use parameterized queries through drivers.

Bad application behavior:

```text
"SELECT ... WHERE email = '" + user_input + "'"
```

Correct pattern:

```text
SQL statement structure
+ separately bound parameters
```

Parameterization protects values, not arbitrary SQL identifiers. Dynamic table/column/order expressions require safe allowlisting or driver-specific identifier quoting.

## Least-privilege application role

An application usually needs much less than owner/superuser rights.

Separate roles for:

- schema migration;
- application read/write runtime;
- read-only analytics;
- backup/replication;
- monitoring;
- human administration.

This limits the impact of SQL injection or application compromise.

## Multi-tenant design

Common strategies include:

- tenant ID column plus RLS/application checks;
- schema per tenant;
- database per tenant;
- cluster/service per tenant or group.

Trade-offs include:

- connection count;
- catalog/schema count;
- migration fan-out;
- noisy neighbors;
- backup/restore granularity;
- query-plan skew;
- cross-tenant analytics;
- isolation requirements.

No one model is universally safest or fastest.

## Failure modes

### Long transaction causes bloat

Symptoms:

- dead tuples grow;
- vacuum runs but cannot reclaim expected versions;
- relation size increases;
- transaction age grows.

Response:

- identify oldest transactions/snapshots;
- determine application owner;
- terminate only with understanding of rollback/business impact;
- fix transaction boundaries/timeouts.

### `idle in transaction`

A client issued `BEGIN` or an implicit transaction and then stopped doing useful work without commit/rollback.

This can hold locks and snapshots.

Fix the application lifecycle and set protective idle-transaction timeouts appropriate to the workload.

### Replication slot fills disk

Symptoms:

- inactive/lagging slot;
- retained WAL grows;
- primary WAL disk approaches full.

Response:

- identify consumer/ownership;
- recover consumer if data continuity is required;
- drop/recreate slot only when the data-loss/resync consequence is understood;
- cap retention where architecture permits.

### Autovacuum cannot keep up

Possible causes:

- extremely high update/delete rate;
- thresholds too high for table size/activity;
- long snapshots;
- insufficient worker/cost capacity;
- I/O saturation;
- table-specific skew.

Response:

- inspect vacuum progress/statistics;
- tune per table where appropriate;
- fix transaction age first;
- reduce unnecessary churn.

### Lock queue outage

A DDL or transaction waits for a lock while new queries queue behind it.

Response:

- identify blocker and waiting graph;
- cancel the least harmful participant based on business context;
- add lock-timeout/migration strategy;
- shorten transactions.

### Deadlock storm

Response:

- capture deadlock logs;
- identify inconsistent resource ordering;
- fix transaction ordering rather than merely increasing deadlock timeout.

### Planner chooses bad plan

Investigate:

- stale statistics;
- skew/correlation;
- parameter-sensitive plans;
- missing/redundant index;
- changed data distribution;
- changed cost settings;
- version upgrade;
- query rewrite.

Do not permanently disable planner strategies globally to fix one query unless you fully understand system-wide effects.

### Work memory exhaustion

Many concurrent sorts/hashes multiply per-operation memory and can trigger host OOM or swapping.

Reduce global memory exposure, use workload-specific settings, and control concurrency.

### Connection exhaustion

Symptoms:

- clients cannot connect;
- server spends resources on thousands of mostly idle sessions;
- failover/restart triggers reconnect storm.

Response:

- preserve admin access;
- stabilize pool/retry behavior;
- fix application pool sizes;
- scale based on measured backend capacity rather than only raising `max_connections`.

### Checkpoint I/O spikes

Symptoms:

- periodic write latency;
- WAL/checkpoint counters spike;
- storage saturates around checkpoints.

Response:

- inspect checkpoint frequency/reasons;
- ensure WAL and checkpoint settings fit write rate;
- verify storage latency/throughput;
- smooth writes rather than disabling durability.

### Replica lag

Possible causes:

- network bandwidth;
- standby I/O/CPU;
- replay conflicts;
- large transactions;
- WAL bursts;
- slot/receiver issues.

Measure where the lag occurs: generation, send, receive, flush, or replay.

### Backup exists but restore fails

Causes:

- missing WAL segment;
- corrupt archive;
- missing encryption key;
- extension unavailable;
- wrong PostgreSQL binary/version;
- backup job succeeded before upload was durable;
- restore procedure never tested.

The fix is a continuous restore-testing program, not more optimistic backup alerts.

## Incident triage

For a degraded primary, establish first:

```text
availability: can clients connect?
load: CPU / memory / disk / network
connections: active vs idle vs idle-in-transaction
waits: locks / I/O / WAL / client
transactions: oldest transaction/snapshot
queries: highest current and cumulative load
maintenance: vacuum/analyze progress
storage: data + WAL free space
replication: send/flush/replay lag + slots
checkpoints/WAL: abnormal rate
```

Avoid changing many database parameters during an incident before identifying the bottleneck.

## Lock investigation

Useful questions:

- which PID is waiting?
- what lock type/mode?
- who blocks it?
- how old is the blocker's transaction?
- is the blocker active or idle?
- is a deployment DDL waiting?
- what happens if either side is canceled?

A blocking session can be doing a fast query inside a very old transaction. Query duration and transaction duration are different metrics.

## Disk-full risk

PostgreSQL needs headroom for:

- WAL;
- temporary query files;
- table/index growth;
- vacuum/rewrite operations;
- base backups on local destinations;
- crash recovery;
- replication retention.

A database operating at 99% disk usage is already in an incident-prone state.

Treat WAL and data volume headroom separately where storage architecture separates them.

## Data corruption response

If corruption is suspected:

- stop destructive repair attempts;
- preserve copies/snapshots/logs;
- determine scope: storage, index, heap, WAL, replica;
- check hardware/filesystem/storage health;
- consult version-specific PostgreSQL recovery tooling/documentation;
- prefer restoring or rebuilding from known-good data when correctness cannot be established.

Never use low-level repair options from an internet snippet without understanding what consistency guarantees they discard.

## Upgrade/release cadence

PostgreSQL major releases introduce features and behavior changes. Minor releases contain bug/security fixes and are designed within a major-version maintenance model.

Operations should maintain:

- supported major versions;
- timely minor updates;
- tested extension compatibility;
- client-driver compatibility;
- rehearsed major-upgrade paths.

Use the current PostgreSQL versioning and release-policy documentation rather than assuming historical numbering rules forever.

## Development workflow

For application teams:

```text
schema migration in version control
  -> CI starts representative PostgreSQL
  -> migration applies from supported previous schema
  -> tests run under application role
  -> rollback/forward-recovery strategy tested where needed
  -> query plans tested for critical paths
  -> production migration uses lock/time bounds
```

Do not let ORM-generated migration SQL bypass database-level review for high-risk tables.

## Testing database behavior

Tests should include more than CRUD happy paths:

- concurrent updates;
- unique conflicts;
- transaction retry;
- deadlock-prone ordering;
- failover/reconnect;
- statement timeout;
- migration lock contention;
- replica-read staleness;
- backup restore;
- RLS/permission negative tests.

Database correctness bugs often appear only under concurrency or failure.

## Anti-patterns

Avoid:

- application runtime roles with superuser privileges;
- unlimited application connection pools;
- long business workflows inside open database transactions;
- disabling autovacuum to avoid I/O;
- `VACUUM FULL` as routine maintenance;
- dropping replication slots without understanding consumer recovery;
- relying on replication as backup;
- keeping backups without restore tests;
- changing durability settings as generic tuning advice;
- adding indexes without measuring write cost and query use;
- global planner toggles to fix one query;
- giant unbounded `work_mem` on high-concurrency servers;
- schema migrations that wait indefinitely for exclusive locks;
- unqualified names in privileged security-definer code;
- plaintext database secrets in application repositories;
- assuming logical replication copies every database object/DDL automatically;
- promoting a replica without fencing the former primary;
- treating read replicas as perfectly current;
- treating `EXPLAIN ANALYZE` as read-only.

## Operational checklist

Before a production schema change:

- inspect lock level and rewrite behavior;
- estimate rows/data size;
- test on representative data;
- set deliberate statement/lock time bounds;
- inspect replica/WAL impact;
- ensure disk headroom;
- define cancellation/retry path;
- monitor after deployment.

Before a major upgrade:

- verify backup restore;
- inventory extensions;
- test `pg_upgrade`/logical/dump strategy;
- test critical query plans;
- test drivers and migration tooling;
- define rollback point;
- rehearse failover/cutover.

For ongoing operations:

- monitor oldest transaction;
- monitor autovacuum and transaction age;
- monitor WAL/slot retention;
- monitor replication lag;
- monitor connection saturation;
- monitor disk headroom;
- track top queries and wait events;
- test backups by restoring them;
- apply supported minor updates.

## Learning path

### Beginner

Learn:

- SQL tables, keys, joins, constraints;
- roles and databases/schemas;
- `BEGIN` / `COMMIT` / rollback;
- basic B-tree indexes;
- `EXPLAIN`;
- backup basics;
- connection/authentication basics.

### Intermediate

Learn:

- MVCC snapshots;
- transaction isolation;
- locks/deadlocks;
- vacuum/autovacuum;
- WAL/checkpoints;
- planner statistics;
- index families;
- JSONB/arrays/ranges;
- partitioning;
- physical streaming replication;
- PITR.

### Advanced

Learn:

- tuple visibility and freezing;
- planner estimation internals;
- WAL/recovery internals;
- hot-standby conflicts;
- synchronous replication failure modes;
- replication slots and logical decoding;
- logical replication migrations;
- extension/server-code trust;
- HA fencing and failover control planes;
- large-table migration strategies;
- memory/concurrency capacity modeling;
- corruption/recovery and upgrade engineering.

## Relationships

### MySQL

`database/mysql` is a major alternative client/server relational database. Evaluate SQL semantics, transaction/isolation behavior, indexing/storage architecture, replication, operational tooling, extensibility, ecosystem, and managed-service requirements rather than treating all SQL servers as interchangeable.

### SQLite

`database/sqlite` is a major relational alternative for embedded/local workloads. It runs as a library inside the application process rather than as a PostgreSQL-style multi-process network database server, so deployment, concurrency, operations, and failure domains differ fundamentally.

## Taxonomy

- Kind: `database`
- Domains: `data`
- Deployment: `self-hosted`, `service`
- License: `PostgreSQL`
- Maturity: `deep-dive`

## Primary references

- PostgreSQL documentation: https://www.postgresql.org/docs/current/
- Source repository: https://github.com/postgres/postgres
- License/copyright: https://github.com/postgres/postgres/blob/master/COPYRIGHT
- Architecture: https://www.postgresql.org/docs/current/tutorial-arch.html
- Concurrency/MVCC: https://www.postgresql.org/docs/current/mvcc.html
- Isolation: https://www.postgresql.org/docs/current/transaction-iso.html
- Locks/deadlocks: https://www.postgresql.org/docs/current/explicit-locking.html
- Vacuum/autovacuum: https://www.postgresql.org/docs/current/routine-vacuuming.html
- WAL: https://www.postgresql.org/docs/current/wal-intro.html
- Physical storage: https://www.postgresql.org/docs/current/storage.html
- Index types: https://www.postgresql.org/docs/current/indexes-types.html
- EXPLAIN: https://www.postgresql.org/docs/current/using-explain.html
- Planner statistics: https://www.postgresql.org/docs/current/planner-stats.html
- Backup/restore: https://www.postgresql.org/docs/current/backup.html
- PITR/WAL archiving: https://www.postgresql.org/docs/current/continuous-archiving.html
- Streaming replication: https://www.postgresql.org/docs/current/warm-standby.html
- Logical replication: https://www.postgresql.org/docs/current/logical-replication.html
- Authentication: https://www.postgresql.org/docs/current/client-authentication.html
- `pg_hba.conf`: https://www.postgresql.org/docs/current/auth-pg-hba-conf.html
- Row security: https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- Partitioning: https://www.postgresql.org/docs/current/ddl-partitioning.html
- JSON: https://www.postgresql.org/docs/current/datatype-json.html
- Monitoring: https://www.postgresql.org/docs/current/monitoring-stats.html

## Verification

This deep-dive was reviewed on **2026-09-06** against current PostgreSQL documentation and the canonical PostgreSQL source repository. PostgreSQL major versions evolve planner behavior, replication features, security defaults, monitoring views, SQL features, and operational tooling; verify version-specific behavior against the exact production major/minor documentation before changing database architecture or recovery procedures.

## Maintenance

Prioritize review when:

- PostgreSQL changes MVCC/vacuum or transaction-ID maintenance behavior materially;
- planner/index/partitioning behavior changes across major versions;
- replication or backup/PITR semantics evolve;
- authentication/TLS/RLS defaults or guidance change;
- a major version changes extension compatibility or upgrade paths;
- new monitoring views replace or alter operational signals;
- the PostgreSQL license/copyright text changes.
