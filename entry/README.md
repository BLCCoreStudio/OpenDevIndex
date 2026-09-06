# SQLite

> Embedded relational database engine that compiles SQL into virtual-machine bytecode and stores transactional B-tree state in ordinary files through a pager, journaling layer, and pluggable VFS—without a separate database server process.

SQLite is easiest to reason about as a **database library inside the application process**, not as a small PostgreSQL or MySQL server:

```text
application
   |
   v
SQLite C API / language binding
   |
   +--> tokenizer + parser + code generator / query planner
   |             |
   |             v
   |        VDBE bytecode
   |             |
   |             v
   |        virtual machine
   |
   +--> B-tree layer
   |       |
   |       v
   |     pager / page cache
   |       |
   |       +--> rollback journal
   |       +--> WAL + checkpointing
   |       +--> file locking
   |
   v
VFS abstraction
   |
   v
local filesystem / database file
```

That architecture creates SQLite's defining trade-off: **there is no network hop or server administration layer, but concurrency, durability, and correctness depend directly on the application's process model and the filesystem beneath the database file**.

## Product boundary

SQLite provides:

- an embedded SQL database engine linked into an application;
- a stable cross-platform database file format;
- ACID transactions;
- B-tree tables and indexes;
- rollback-journal and write-ahead-log transaction modes;
- SQL parsing, query planning, and bytecode execution;
- constraints, triggers, views, generated expressions, and rich SQL features;
- virtual tables and extension APIs;
- JSON and full-text-search functionality in supported builds;
- backup, integrity-check, and maintenance interfaces;
- a C API used by many higher-level language bindings.

SQLite does **not** provide a separate network database daemon, centralized account management, server-side connection routing, multi-node replication, automatic failover, distributed consensus, or a built-in remote-access protocol.

Those are not missing pieces of SQLite's intended architecture. SQLite solves a different problem: reliable local relational storage inside an application or on the same machine as the code issuing SQL.

## Embedded means the database engine runs with your application

With a client/server database, the application sends requests to another process:

```text
application -> network/socket -> database server -> storage
```

With SQLite:

```text
application process
  -> SQLite library call
  -> local filesystem
```

This removes:

- network round trips between application and database engine;
- server deployment and process supervision;
- database listener exposure;
- server account provisioning;
- many operational layers required by remote databases.

But it also means the application itself is responsible for:

- opening and closing connections correctly;
- coordinating local concurrency;
- setting transaction behavior deliberately;
- choosing journal and durability settings;
- protecting database files;
- performing schema migrations;
- taking safe backups;
- handling `SQLITE_BUSY`, I/O errors, disk-full conditions, and corruption signals.

## SQL becomes bytecode

SQLite does not directly interpret a SQL string one operator at a time.

A simplified execution path is:

```text
SQL text
  -> tokenize
  -> parse
  -> resolve names and expressions
  -> query planner / code generator
  -> VDBE bytecode program
  -> sqlite3_step()
  -> rows / completion / error
```

Prepared statements are compiled programs.

Conceptually:

```c
sqlite3_prepare_v2(..., &stmt, ...);
sqlite3_bind_int(stmt, 1, 42);
while (sqlite3_step(stmt) == SQLITE_ROW) {
    /* consume result */
}
sqlite3_finalize(stmt);
```

The exact wrapper syntax differs across languages, but the lifecycle remains useful to understand:

1. prepare SQL;
2. bind values;
3. execute/step;
4. read columns;
5. reset or finalize.

Prepared statements are therefore both an execution mechanism and the normal way to avoid unsafe string concatenation for data values.

## VDBE: the virtual database engine

The bytecode interpreter is called the **Virtual Database Engine** or VDBE.

A query plan eventually becomes VDBE operations that perform work such as:

- opening table or index cursors;
- seeking into B-trees;
- comparing values;
- evaluating expressions;
- constructing result rows;
- inserting or deleting records;
- controlling transactions;
- invoking functions and virtual tables.

`EXPLAIN` can expose the generated virtual-machine program, while `EXPLAIN QUERY PLAN` gives a higher-level view of access strategy.

For normal performance diagnosis, start with `EXPLAIN QUERY PLAN`; use low-level bytecode when the higher-level explanation is insufficient.

## Database file and page model

SQLite stores a database in a sequence of fixed-size pages.

Conceptually:

```text
database file
  -> page 1: database header + B-tree content
  -> page 2
  -> page 3
  -> ...
```

The file contains structures such as:

- table B-trees;
- index B-trees;
- freelist pages;
- schema metadata;
- overflow pages for large records.

The database file format is explicitly documented and designed for long-term compatibility.

A SQLite database is therefore not an opaque proprietary heap. Its on-disk organization is part of the project's compatibility contract.

## B-tree layer

Ordinary tables and indexes are implemented using B-trees.

The B-tree layer reasons about:

- keys;
- records;
- pages;
- cell layout;
- tree traversal;
- splitting and balancing;
- overflow data.

It does **not** own transaction durability by itself. That responsibility belongs lower in the stack to the pager and journaling machinery.

This separation is important:

```text
B-tree
  = logical page organization and lookup structure

pager
  = page cache + locking + atomic commit + rollback/recovery coordination
```

## Pager: the transactional filesystem boundary

The pager is one of SQLite's most important subsystems.

It manages fixed-size database pages and coordinates:

- page caching;
- reads and writes;
- locking;
- transaction commit and rollback;
- rollback-journal behavior;
- interaction with WAL mode;
- synchronization with persistent storage through the VFS.

Many SQLite production problems that look like "SQL issues" are actually pager/filesystem/concurrency issues:

- another writer holds the database;
- a long reader prevents a WAL checkpoint from completing;
- disk space runs out;
- a network filesystem does not implement locking safely;
- an application copies or replaces files while they are live;
- durability settings do not match the failure model.

## VFS: the operating-system abstraction

SQLite accesses the operating system through a **Virtual File System** abstraction.

A VFS implements operations such as:

- open/close;
- read/write;
- file locking;
- shared memory where required;
- synchronization;
- randomness;
- time;
- filesystem capability checks.

This allows SQLite to support different operating systems and specialized storage environments without putting OS-specific behavior into every higher layer.

It also means SQLite's correctness assumptions eventually depend on the VFS and filesystem honoring their contracts.

## Rowid tables

Most SQLite tables are **rowid tables** unless declared `WITHOUT ROWID`.

For a rowid table:

```text
table B-tree key
  -> integer rowid
  -> row payload
```

If a column is declared exactly as `INTEGER PRIMARY KEY`, it aliases the rowid.

That has practical consequences:

- rowid lookup is direct and efficient;
- the rowid is part of physical table organization;
- secondary indexes ultimately identify the table row through rowid;
- primary-key declarations that are not the `INTEGER PRIMARY KEY` rowid alias behave differently from clustered-primary-key storage in systems such as InnoDB.

Do not assume that the phrase "primary key" implies the same physical storage model across databases.

## `WITHOUT ROWID` tables

`WITHOUT ROWID` changes the storage model so the declared primary key becomes the B-tree key rather than maintaining the normal hidden integer rowid organization.

This can be useful when:

- the natural primary key is compact;
- the rowid adds no value;
- avoiding duplicate primary-key storage can reduce space or lookup work.

It is not universally faster.

A wide or awkward composite primary key can increase B-tree and secondary-index costs. Choose it based on the real key shape and access pattern, not because `WITHOUT ROWID` sounds more normalized.

## Dynamic typing and type affinity

SQLite has a flexible type system.

Values carry storage classes such as:

- null;
- integer;
- real;
- text;
- blob.

Columns have **type affinity**, which influences conversions and comparisons but does not make ordinary tables behave like rigidly typed columns in many client/server databases.

This is a frequent portability trap.

For example, application code should not assume that declaring a column with a familiar SQL type name guarantees that every stored value will always have exactly the host-language type the developer expected.

Validate data at the application boundary and use database constraints deliberately.

## `STRICT` tables

SQLite also supports `STRICT` tables for schemas that need stronger type discipline.

Use them when application invariants benefit from rejecting values that do not fit the declared storage class rules.

`STRICT` does not turn SQLite into PostgreSQL or MySQL. SQLite's supported type names, conversion behavior, date/time conventions, booleans, and expression semantics still need to be understood on their own terms.

## Transactions are always present

SQLite performs database reads and writes inside transactions.

If the application does not explicitly begin one, SQLite starts an implicit transaction as needed and commits it when the statement lifecycle completes.

Explicit transactions are essential when multiple statements form one logical change:

```sql
BEGIN;

UPDATE accounts
SET balance = balance - 100
WHERE id = 10;

UPDATE accounts
SET balance = balance + 100
WHERE id = 20;

COMMIT;
```

The transaction boundary determines both correctness and concurrency behavior.

## Savepoints, not nested `BEGIN`

`BEGIN ... COMMIT` transactions do not nest.

For nested rollback scopes use savepoints:

```sql
SAVEPOINT item_change;

UPDATE items
SET state = 'processed'
WHERE id = 7;

ROLLBACK TO item_change;
RELEASE item_change;
```

This matters in libraries where a lower-level function may need local rollback behavior while the caller already owns the outer transaction.

## `DEFERRED`, `IMMEDIATE`, and `EXCLUSIVE`

SQLite allows explicit transaction modes that change when write intent is acquired.

### `BEGIN DEFERRED`

The transaction begins without immediately taking a write reservation. It may start as a read transaction and later attempt to upgrade when a write occurs.

### `BEGIN IMMEDIATE`

The connection tries to establish write intent at the beginning of the transaction.

This is useful when the application knows it must write and would rather discover writer contention before doing substantial read/compute work.

### `BEGIN EXCLUSIVE`

This requests stronger exclusivity. Its practical effect differs between rollback-journal and WAL environments, so it should not be used as a generic "make transaction safer" switch.

Choose the mode for a concurrency reason you can explain.

## The single-writer rule

SQLite can serve multiple concurrent readers, but **only one write transaction can modify a given database file at a time**.

This is one of the most important architectural facts in the entire project.

It does not mean SQLite is "single-threaded." It means write serialization happens at the database-file transaction level.

Many workloads are perfectly compatible with this design because write transactions are short:

```text
writer A -> commit
writer B -> commit
writer C -> commit
```

Problems arise when applications hold write transactions while doing unrelated work:

```text
BEGIN write transaction
  -> update row
  -> make network request
  -> wait for user input
  -> perform expensive computation
  -> COMMIT
```

That keeps the scarce writer slot occupied far longer than necessary.

## `SQLITE_BUSY` is part of normal concurrency

When a connection cannot obtain a required lock because another connection is using the database incompatibly, SQLite can return `SQLITE_BUSY`.

Applications should have a deliberate policy for this condition.

Options include:

- a busy timeout;
- a busy handler;
- bounded application-level retry;
- shortening transactions;
- reducing write contention;
- serializing writes in the application architecture.

Do not convert an unbounded busy retry into a hidden request hang.

## Rollback-journal mode

In rollback-journal mode, SQLite protects atomic updates by recording original database-page content before overwriting the main database file.

A simplified write lifecycle is:

```text
read original page
  -> save original page in rollback journal
  -> modify database page
  -> synchronize according to durability policy
  -> commit
  -> remove/truncate/finalize journal
```

If a crash leaves a valid **hot journal**, SQLite can use it to restore the database to a consistent pre-transaction state when the database is opened again.

The journal is therefore part of the live transactional state of the database while a transaction is in flight.

## Never treat `database.db` as the only live file blindly

Depending on journal mode and connection state, SQLite can have associated files such as:

```text
app.db
app.db-journal
```

or in WAL mode:

```text
app.db
app.db-wal
app.db-shm
```

Copying only `app.db` while the database is active can produce an inconsistent or stale backup.

Use a documented backup mechanism instead of filesystem copying whenever live transactions are possible.

## WAL mode

Write-ahead logging reverses the main write direction.

Instead of first preserving old pages and then modifying the database file, committed changes are appended to the WAL:

```text
reader sees database snapshot

writer
  -> append changed pages to -wal
  -> commit record in WAL

checkpoint
  -> copy eligible WAL pages back into main database
```

WAL improves read/write concurrency because readers can continue using their snapshots while a writer appends changes.

But WAL does **not** remove the one-writer rule.

There is still only one writer at a time for a database WAL.

## WAL snapshots

A reader in WAL mode establishes an end point in the WAL and continues reading a consistent snapshot relative to that point.

Later commits can be appended by a writer without changing what the existing reader observes.

That is why a reader and writer can often operate concurrently in WAL mode.

It also explains why a long-lived reader can become operationally expensive: its snapshot can prevent checkpoint progress past pages that reader may still need.

## Checkpointing

A checkpoint transfers committed content from the WAL back into the main database file.

Conceptually:

```text
WAL frames
  -> checkpoint
  -> main database pages
```

Checkpoints can be automatic or application-controlled.

Operational questions include:

- How large is the WAL growing?
- Are long readers blocking checkpoint progress?
- Is checkpoint work causing latency spikes?
- Is the application closing connections cleanly?
- Is the workload creating write bursts faster than checkpoints can absorb?

WAL performance is therefore not only about enabling `PRAGMA journal_mode=WAL`; checkpoint behavior is part of the design.

## WAL and network filesystems

Standard SQLite WAL coordination uses shared-memory mechanisms for the WAL index.

That requires participating processes to be on the same machine and makes WAL unsuitable for ordinary network-filesystem sharing.

More broadly, opening the same SQLite database directly from multiple machines depends on filesystem locking semantics that many network filesystems do not implement reliably enough for safe use.

If many remote clients need shared access, put an application service in front of SQLite or use a client/server database rather than sharing the database file directly across machines.

## Isolation model

Separate SQLite database connections do not see uncommitted changes from each other under normal operation.

In rollback-journal mode, readers and writers use file locking so writes are serialized and readers can be excluded during critical write phases.

In WAL mode, readers can keep a stable snapshot while newer transactions commit into the WAL.

Do not map SQLite's behavior mechanically onto another database's named isolation levels. Reason from:

- connection boundaries;
- transaction start/end;
- journal mode;
- read snapshot timing;
- write-lock acquisition.

## Same-connection behavior is different from cross-connection isolation

Code using one SQLite connection can observe its own transaction changes.

The isolation discussion mainly matters between separate database connections.

This distinction is important in frameworks that hide connection pooling. Two repository calls that look adjacent in application code may or may not be using the same underlying SQLite connection.

## Indexes

SQLite indexes are B-trees that can avoid full table scans or sorting work.

A simple index:

```sql
CREATE INDEX idx_orders_customer
ON orders(customer_id);
```

A composite index:

```sql
CREATE INDEX idx_orders_customer_created
ON orders(customer_id, created_at DESC);
```

The column order matters.

An index beginning with `(customer_id, created_at)` can support search patterns that constrain the leftmost portion of that key order, but should not be assumed to optimize unrelated predicates on `created_at` alone.

## Covering indexes

A covering index contains all data needed by a query so SQLite can answer it using the index without visiting the table B-tree for additional columns.

That can reduce page lookups for hot read paths.

The trade-off is the same as elsewhere:

- wider indexes use more disk;
- they consume cache space;
- writes become more expensive;
- migrations and backups get larger.

Do not make every index covering by default.

## Partial indexes

SQLite supports indexes over only rows satisfying a predicate.

Example:

```sql
CREATE INDEX idx_jobs_ready
ON jobs(priority, created_at)
WHERE state = 'ready';
```

For workloads where a small active subset is queried frequently, a partial index can be substantially smaller than indexing every historical row.

The query predicate must align with the index condition for the planner to use it effectively.

## Expression indexes

SQLite can index expressions when the expression is suitable for indexing.

Example:

```sql
CREATE INDEX idx_users_lower_email
ON users(lower(email));
```

This is useful only if queries use a matching expression pattern.

An expression index should encode a real access pattern, not compensate for unclear data modeling.

## Query planning

SQLite's planner chooses among possible algorithms for table access, joins, sorting, and index use.

Useful factors include:

- available indexes;
- index column order;
- estimated selectivity;
- collected statistics;
- equality/range predicates;
- ordering requirements;
- join order;
- covering opportunities.

A slow query can be caused by:

```text
missing useful index
```

or:

```text
index exists but query cannot use its leading key shape
```

or:

```text
planner lacks representative statistics
```

or simply:

```text
query requests too much work
```

Those require different fixes.

## `EXPLAIN QUERY PLAN`

Use `EXPLAIN QUERY PLAN` to inspect the planner's high-level strategy:

```sql
EXPLAIN QUERY PLAN
SELECT id, title
FROM notes
WHERE folder_id = ?
ORDER BY updated_at DESC
LIMIT 50;
```

Look for questions such as:

- Is SQLite scanning the entire table?
- Which index is selected?
- Is a temporary B-tree required for sorting or grouping?
- What is the join order?
- Is the chosen index consistent with the filter shape?

Do not treat the textual output format as a stable machine API across SQLite releases. Use it primarily as a diagnostic tool.

## Statistics and `PRAGMA optimize`

Query-planner statistics can change index choices when multiple candidate plans exist.

Modern SQLite documentation recommends `PRAGMA optimize` as the normal way for applications to keep useful planner statistics current without blindly running full `ANALYZE` work every time.

A practical pattern is:

- run optimization after schema/index changes;
- run it periodically for long-lived applications;
- avoid manually editing `sqlite_stat*` tables unless you have a specialized, well-tested reason.

Planner statistics are hints about data distribution, not correctness metadata. A stale statistic should make a plan slower, not change the correct query result.

## Schema changes

SQLite supports transactional schema changes, but migration design still matters.

Production applications should consider:

- old app versions opening a newer schema;
- new app versions opening an older schema;
- partial application upgrade states;
- migration time on large local databases;
- temporary disk requirements;
- rollback behavior if the process is killed;
- compatibility of triggers, views, indexes, and virtual tables.

Use a schema-version strategy that lets the application decide explicitly whether it can open and migrate the database.

## Foreign keys

SQLite supports foreign-key constraints, but applications should enable and verify enforcement explicitly rather than depending on environment/build defaults.

A typical initialization path includes:

```sql
PRAGMA foreign_keys = ON;
```

Then define relationships normally:

```sql
CREATE TABLE parent (
    id INTEGER PRIMARY KEY
);

CREATE TABLE child (
    id INTEGER PRIMARY KEY,
    parent_id INTEGER NOT NULL REFERENCES parent(id)
);
```

Foreign keys protect integrity but can increase write and migration costs. Supporting indexes on referenced/accessed columns may be important for performance.

## Conflict resolution

SQLite has conflict-resolution behavior for constraint violations, including forms associated with `ROLLBACK`, `ABORT`, `FAIL`, `IGNORE`, and `REPLACE`, plus modern UPSERT syntax.

These are not interchangeable convenience keywords.

`REPLACE`, in particular, can have delete/insert-style semantic consequences that are very different from a normal update.

Choose conflict behavior based on business invariants and test trigger/foreign-key effects.

## JSON support

SQLite includes JSON functions/operators in modern builds.

This can be useful for:

- storing semi-structured attributes alongside relational columns;
- extracting JSON fields;
- transforming JSON values;
- indexing expressions derived from JSON content.

Do not turn every schema into one giant JSON column simply because JSON functions exist.

Frequently queried and integrity-critical attributes often deserve normal relational columns and constraints.

## FTS5

FTS5 is SQLite's full-text-search extension.

It provides specialized virtual-table indexing for tokenized text search.

Use it when the workload needs real full-text search semantics rather than patterns such as:

```sql
WHERE body LIKE '%term%'
```

FTS indexes introduce their own schema, maintenance, tokenizer, and synchronization concerns. If content is stored separately from the FTS table, test how updates remain consistent.

## Virtual tables

SQLite's virtual-table interface lets modules expose nontraditional data sources through SQL table semantics.

Examples in the wider SQLite ecosystem include:

- full-text search;
- R-tree spatial indexing;
- generated or external data sources;
- application-defined modules.

A virtual table can participate in planning through its module interfaces, so performance characteristics depend on the module implementation as well as SQLite's planner.

Treat third-party virtual-table extensions as executable dependencies with their own security and compatibility boundaries.

## Extension loading

SQLite can be extended with loadable native-code extensions when the host application enables that capability.

Loading an extension means loading executable code into the application process.

Therefore:

- keep extension loading disabled unless needed;
- do not allow untrusted users to choose arbitrary extension paths;
- pin and review shipped extensions;
- treat extension binaries as part of the software supply chain.

## Security model

SQLite does not have server-style users, roles, and per-database network authentication.

Its primary trust boundary is the application and filesystem.

Security therefore depends on:

- OS file permissions;
- sandboxing;
- encryption strategy outside core SQLite when confidentiality at rest is required;
- correct SQL parameter binding;
- limiting dangerous extension or pragma capabilities;
- treating untrusted database files as hostile input;
- constraining resource use for attacker-controlled queries/data.

"No database server" does not mean "no database attack surface."

## Untrusted database files

Applications sometimes open database files supplied by users, plugins, downloads, or synchronization systems.

Treat those files as untrusted structured input.

SQLite's security guidance includes defense-in-depth controls such as:

- disabling trusted-schema behavior where appropriate;
- restricting or disabling extension loading;
- using the authorizer API for untrusted SQL environments;
- applying runtime limits;
- enabling defensive database modes where supported by the binding/API.

The exact controls available depend on the build and wrapper, so security-sensitive applications should check their SQLite integration rather than assuming all bindings expose every option.

## SQL parameter binding

Use bind parameters for values:

```sql
SELECT id, title
FROM notes
WHERE owner_id = ?
  AND state = ?;
```

Do not build SQL by concatenating untrusted values:

```text
"... WHERE owner_id = " + user_input
```

Parameter binding protects data values from changing SQL syntax.

It does not validate identifiers such as table or column names. Dynamic identifiers require allowlisting or controlled SQL generation.

## Threading modes

SQLite supports multiple threading configurations selected at compile time and, within supported constraints, at startup or connection-open time.

The critical rule is not to memorize a default. It is to know which mode your runtime actually provides and what your language binding permits.

A connection or prepared statement must not be used concurrently in ways prohibited by its threading mode.

Language runtimes may impose stricter rules than the SQLite C library.

## Connection-per-thread is not a universal rule

Some applications use one connection per worker, others serialize work through one database executor, and others use a small local pool.

The best design depends on:

- language binding constraints;
- read/write ratio;
- WAL versus rollback mode;
- transaction duration;
- UI-thread restrictions;
- busy-handling strategy.

More connections do not create more simultaneous writers.

## Backup API

SQLite provides an online backup API designed to copy a live database safely while other connections may be active.

Conceptually:

```text
source database connection
  -> backup API copies pages incrementally
  -> destination database connection
```

Incremental copying allows an application to bound how much work happens in one step and coexist with normal database activity.

For application backups, this is safer than ad hoc copying of live database files.

## `VACUUM INTO`

`VACUUM INTO` can create a compact copy of a database into another file.

This can be useful for export or backup workflows where producing a rebuilt standalone file is acceptable.

It is not the same operational primitive as the incremental backup API. Choose based on:

- database size;
- temporary space;
- latency budget;
- whether incremental copying is needed;
- desired compaction behavior.

## Point-in-time recovery is not built in like a server WAL archive

SQLite WAL is a local transaction mechanism, not a built-in long-term archived log service comparable to PostgreSQL WAL archiving or MySQL binary-log PITR workflows.

If an application needs historical recovery points, it must design them explicitly using mechanisms such as:

- periodic safe backups/snapshots;
- application event logs;
- versioned user documents;
- filesystem/platform snapshot facilities with correct database coordination.

Do not assume keeping an old `-wal` file creates a supported PITR system.

## Integrity checks

SQLite provides integrity-check mechanisms for validating database structure.

They are useful after:

- suspicious I/O failures;
- restore operations;
- migrations that manipulate files externally;
- support incidents involving corruption reports.

Integrity checks are not a substitute for backups. A correctly detected corrupt database is still corrupt.

## How SQLite databases become corrupt

SQLite is designed to preserve database integrity across normal crashes when the filesystem and environment honor required guarantees.

Corruption can still happen when those assumptions are violated.

Dangerous patterns include:

- modifying database bytes outside SQLite;
- copying or restoring only part of the live database/journal/WAL state;
- deleting a journal that is required for recovery;
- broken filesystem locking;
- renaming or replacing a database file while it is in use;
- linking incompatible independent SQLite copies into one process in ways that defeat locking coordination;
- hardware or storage failures;
- application bugs that misuse low-level APIs.

When corruption occurs, investigate the surrounding file lifecycle and locking environment instead of assuming a random SQL statement damaged the B-tree by itself.

## File replacement and sync systems

A SQLite database is not a normal text document that can safely be merged by consumer file-sync software.

Avoid workflows where two devices independently edit the same database file and a sync layer later chooses or merges versions.

If multi-device synchronization is needed, synchronize at the application/data model level or through a server/service designed for conflict resolution.

## Mobile applications

SQLite is a natural fit for mobile apps because it provides local transactional state with no separate server.

Typical uses include:

- offline-first domain data;
- caches with relational queries;
- user-created local content;
- queues for deferred synchronization;
- metadata for downloaded files;
- search indexes.

Mobile-specific design concerns include:

- app process termination during transactions;
- migrations across skipped app versions;
- storage pressure;
- background workers competing with foreground reads;
- backup/restore behavior of the mobile OS;
- encryption requirements;
- synchronization conflict semantics.

The platform ORM does not remove those database-level concerns.

## Desktop applications and application file formats

SQLite can serve as both application database and structured file format.

A desktop application can treat a database as one document containing:

- normalized metadata;
- user objects;
- configuration;
- indexes;
- binary content where appropriate.

Compared with an ad hoc directory of JSON/XML files, SQLite can provide:

- atomic multi-record updates;
- constraints;
- indexed lookup;
- partial reads;
- schema evolution;
- transactional recovery.

The trade-off is that users should not modify internal records with arbitrary external tools unless the file format is intentionally documented as a public interface.

## Server-side SQLite

SQLite can also work well inside an application server when the server and database file are on the same machine and the application's write-concurrency needs fit the single-writer model.

A useful architecture is:

```text
remote clients
   |
   v
application-specific server API
   |
   v
one local SQLite database
```

The database itself is not shared over the network; the server serializes and validates higher-level operations.

This can be simpler than deploying a separate database service for small or moderate workloads.

But if many independent processes or machines require high write concurrency, a client/server database may be the better boundary.

## Performance mental model

SQLite performance is strongly influenced by:

- transaction boundaries;
- number and shape of writes;
- index design;
- working-set size;
- page-cache behavior;
- filesystem latency;
- journal mode;
- synchronization settings;
- checkpoint behavior in WAL mode;
- query-planner statistics;
- temporary sorting or B-tree work;
- row width and blob access patterns.

The biggest performance mistake is often not a pragma. It is doing one durable transaction per row when the application could safely batch related work.

## Batch writes in transactions

Bad pattern:

```text
insert row -> commit
insert row -> commit
insert row -> commit
... thousands of times
```

Better when the business operation allows it:

```sql
BEGIN;
-- many related INSERT/UPDATE statements
COMMIT;
```

Grouping work can drastically reduce commit/synchronization overhead.

Do not make transactions arbitrarily huge either. Very large transactions increase rollback cost, lock duration, WAL/journal growth, and failure recovery work.

## Synchronous durability settings

SQLite exposes synchronization controls that influence how aggressively it asks the operating system to persist critical writes.

Changing those settings can alter performance and the failure window under power loss or OS crashes.

Do not copy benchmark pragmas into production without understanding:

- journal mode;
- filesystem guarantees;
- hardware cache behavior;
- whether losing recently committed transactions is acceptable;
- whether corruption resistance or only durability is affected by the exact mode.

Use the official documentation for the current release and test under realistic failure assumptions.

## Cache size and memory mapping

SQLite exposes controls for page-cache sizing and memory-mapped I/O.

These are workload tuning tools, not universal speed switches.

Increasing cache use can help repeated page access but competes with the rest of the application's memory budget. Memory mapping can alter I/O behavior but should be evaluated against platform, file size, address space, and concurrency requirements.

Measure before and after changes.

## Temporary work

Queries may need temporary storage for:

- sorts;
- DISTINCT;
- GROUP BY;
- materialization;
- some joins or subqueries.

`EXPLAIN QUERY PLAN` can reveal cases where a temporary B-tree is used.

Often the correct fix is an index aligned with filtering and ordering—not increasing generic memory settings.

## Large BLOBs

SQLite can store large BLOB values, but architecture still matters.

Consider:

- database-page churn;
- backup size;
- update frequency;
- whether the blob is read with its metadata or independently;
- platform filesystem behavior;
- incremental BLOB APIs where appropriate.

Do not split blobs into external files automatically, and do not put every file into SQLite automatically. Choose based on atomicity, access pattern, lifecycle, and backup needs.

## Database size is not the only scale limit

SQLite publishes explicit implementation limits for areas such as:

- database size;
- SQL statement complexity;
- number of columns;
- attached databases;
- expression depth;
- parameter numbering;
- string/blob length.

Most applications hit architectural limits—write concurrency, storage latency, schema design, or device capacity—long before the theoretical maximum database-file size.

Treat maximums as safety boundaries, not target operating points.

## Operational triage

When an SQLite-backed application reports database problems, classify the incident before changing pragmas.

### `SQLITE_BUSY`

Check:

1. Is another write transaction open?
2. Are transactions doing network/UI work before commit?
3. Is a migration holding a lock?
4. Is the busy timeout/retry policy appropriate?
5. Would one serialized writer queue simplify the application?

### Growing `-wal` file

Check:

1. Are long-running readers keeping old snapshots open?
2. Are checkpoints occurring?
3. Is a connection/statement left active unexpectedly?
4. Is write volume continuously outrunning checkpoint work?

### Sudden slow query

Check:

1. Did data volume or distribution change?
2. Did an index change?
3. What does `EXPLAIN QUERY PLAN` show?
4. Were planner statistics refreshed with `PRAGMA optimize`?
5. Is the query waiting on filesystem or lock contention rather than CPU?

### `SQLITE_FULL`

Check:

- free disk space;
- filesystem quota;
- temp-file space;
- WAL/journal growth;
- platform storage pressure.

### Corruption report

Check:

1. Preserve a copy of all relevant database/journal/WAL files before experimenting.
2. Identify whether files were copied, renamed, restored, or synchronized externally.
3. Check storage and filesystem health.
4. Run documented integrity checks on a copy where possible.
5. Restore from a verified backup rather than repeatedly writing to the damaged original.

## Migration discipline

A safe application migration system should be:

- versioned;
- transactional where supported by the operation;
- deterministic;
- restart-aware;
- tested on realistically large databases;
- tested across supported upgrade paths;
- backed up when migration risk justifies it.

Avoid migration code that says "if column missing, try random ALTER statements until one works." Schema evolution is application state and deserves the same rigor as code deployment.

## Practical initialization checklist

A production application opening a database should make deliberate decisions about:

```text
open flags / path
threading + connection ownership
foreign-key enforcement
journal mode
busy handling
synchronous durability policy
schema version + migrations
extension loading policy
security/defensive settings
planner maintenance strategy
backup policy
```

Do not scatter these decisions across unrelated call sites. Centralize connection/database initialization so the application's SQLite contract is reviewable.

## Example: short write transaction

```sql
BEGIN IMMEDIATE;

UPDATE documents
SET title = ?,
    updated_at = ?
WHERE id = ?;

INSERT INTO change_log(document_id, operation, created_at)
VALUES (?, 'update', ?);

COMMIT;
```

The important idea is not the exact SQL. It is that:

- write intent is acquired deliberately;
- the transaction is short;
- related changes commit atomically;
- external I/O is kept outside the transaction.

## Example: queue claim pattern

A local worker queue needs an atomic claim so two workers do not process the same job.

One design is:

```text
begin short write transaction
  -> find eligible job
  -> mark it claimed/running
commit
perform slow external work outside transaction
begin short write transaction
  -> persist result
commit
```

Keeping network work outside the write transaction protects the single-writer slot.

The exact SQL can vary depending on SQLite version and application semantics; concurrency correctness matters more than copying one queue snippet.

## SQLite versus PostgreSQL

The strongest difference is architectural.

SQLite:

- runs inside the application process;
- usually stores one database in one local file;
- has no database server or network protocol;
- allows one writer at a time per database file;
- is excellent for local/embedded/application-owned state.

PostgreSQL:

- runs as a separate database server;
- manages many client connections centrally;
- supports concurrent server-side transaction processing with a very different MVCC/WAL architecture;
- provides roles, remote authentication, replication, PITR, and operational server tooling;
- is suited to shared networked data and higher write concurrency.

Choosing between them is usually a deployment-boundary decision before it is a SQL-feature decision.

## SQLite versus MySQL

SQLite and MySQL both support relational SQL workloads but solve different system problems.

SQLite is embedded and application-owned.

MySQL is a client/server database with:

- server-managed connections/accounts;
- InnoDB transactional storage;
- binary-log replication;
- server HA ecosystem and routing tools;
- higher multi-client write-concurrency capacity.

Use SQLite when keeping the engine next to the application makes the system simpler. Use a client/server system when data ownership, remote access, centralized operations, or concurrent writers justify the server boundary.

## Common mistakes

- Treating SQLite as a tiny network database server.
- Sharing a WAL database over a normal network filesystem.
- Holding write transactions open across HTTP calls, user input, or expensive computation.
- Ignoring `SQLITE_BUSY` because tests use only one connection.
- Copying only the main `.db` file while WAL/journal state is active.
- Deleting `-wal`, `-shm`, or journal files because they "look temporary."
- Assuming primary keys have InnoDB/PostgreSQL-like physical behavior without understanding rowid tables.
- Assuming column declarations enforce rigid types in ordinary tables.
- Forgetting to enable/verify foreign-key enforcement.
- Adding many overlapping indexes without measuring write and storage cost.
- Using one transaction per imported row.
- Turning off durability controls to improve a benchmark without modeling power-loss risk.
- Using file synchronization as multi-device database replication.
- Loading arbitrary native extensions from user-controlled paths.
- Assuming corruption can only be caused by SQLite itself rather than filesystem/file-lifecycle misuse.
- Running schema migrations without testing large real-world databases and interrupted upgrades.

## Learning path

### Beginner

Learn:

1. database files and connections;
2. tables, rowid, and `INTEGER PRIMARY KEY`;
3. transactions and savepoints;
4. parameter binding;
5. indexes;
6. foreign keys and constraints;
7. backup basics.

### Intermediate

Learn:

1. B-tree and pager mental model;
2. rollback journal versus WAL;
3. single-writer concurrency;
4. `SQLITE_BUSY` handling;
5. WAL checkpoints and long readers;
6. type affinity and `STRICT` tables;
7. composite/covering/partial indexes;
8. `EXPLAIN QUERY PLAN` and `PRAGMA optimize`;
9. migration design;
10. virtual tables, FTS5, and JSON features where needed.

### Advanced

Learn:

1. database file format and page layout;
2. VDBE bytecode and planner internals;
3. pager locking state and crash recovery;
4. WAL-index/checkpoint behavior;
5. VFS contracts and filesystem assumptions;
6. custom functions, collations, and virtual-table modules;
7. security controls for untrusted databases/SQL;
8. low-level backup/recovery tooling;
9. performance testing under realistic device I/O and concurrency;
10. corruption diagnosis and defensive file lifecycle engineering.

## What to learn next

- [`database/postgresql`](https://github.com/BLCCoreStudio/OpenDevIndex/tree/database/postgresql/entry) — compare an embedded local database with a multi-process client/server MVCC/WAL system.
- [`database/mysql`](https://github.com/BLCCoreStudio/OpenDevIndex/tree/database/mysql/entry) — compare SQLite's rowid/pager/WAL architecture with MySQL's SQL layer and InnoDB storage engine.
- B-trees — understand how table and index key order shapes reads, writes, and storage locality.
- transaction isolation — separate the abstract consistency problem from SQLite's concrete lock/snapshot implementation.
- filesystem durability and locking — understand the OS guarantees the pager and VFS rely on.
- local-first synchronization — learn why replicating logical operations/state is different from synchronizing a live SQLite file.

## Authoritative sources

Primary references for this module include:

- SQLite official documentation;
- SQLite architecture documentation;
- database file-format documentation;
- pager/locking and isolation documentation;
- WAL and WAL-format documentation;
- query-planner and `ANALYZE`/`PRAGMA optimize` documentation;
- rowid and `WITHOUT ROWID` documentation;
- backup API documentation;
- security guidance;
- database-corruption guidance;
- official public-domain dedication;
- SQLite's canonical Fossil source repository.

See [`sources.md`](sources.md) for the curated source list.

## Verification and maintenance

This deep-dive revision was reviewed on **2026-09-06** against current SQLite documentation and the official SQLite source repository.

Facts most likely to age include:

- recommended planner-maintenance commands;
- newly supported SQL syntax and extensions;
- default compile options;
- security/defensive APIs;
- WAL/checkpoint implementation refinements;
- limits;
- extension availability;
- platform/VFS behavior;
- query-planner strategies.

Stable architectural ideas—SQLite as an embedded library, SQL-to-bytecode execution, B-tree/pager/VFS separation, one writer per database file, rollback/WAL transaction mechanisms, and the need to respect filesystem locking and live auxiliary files—should still be rechecked when major internals change.