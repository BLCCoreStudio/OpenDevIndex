# Apache Cassandra

> Distributed wide-column database designed for high availability, horizontal scale, multi-node replication, and predictable write-heavy workloads without a single primary server.

## What it is

Apache Cassandra is indexed as a **database**. Its stable OpenDevIndex address is `database/cassandra`; taxonomy facets are kept separate from that address so classification can improve without breaking links.

## Why it matters

The module focuses on the technology's practical role, high-signal characteristics, common use cases, and authoritative references. Fast-changing details should be verified against the sources below rather than inferred from stale copies.

## Typical use cases

- Store high-volume operational data across many commodity servers
- Run geographically distributed workloads that prioritize availability and replication
- Support write-heavy applications with partitioned data models and tunable consistency

## Key points

- Cassandra uses a peer-to-peer architecture without a single primary node
- Data is partitioned and replicated across a cluster according to configurable strategies
- CQL provides a SQL-inspired interface while the underlying data model is optimized around query-specific partitions

## Taxonomy

- Kind: `database`
- Domains: `data`, `distributed-systems`
- Deployment: `self-hosted`, `service`
- License metadata: `Apache-2.0`

## Primary links

- Homepage: https://cassandra.apache.org/
- Repository: https://github.com/apache/cassandra

## Verified sources

- [Apache Cassandra official site](https://cassandra.apache.org/) — `official`
- [Apache Cassandra source repository](https://github.com/apache/cassandra) — `repository`

## Verification

The catalog metadata and source references for this module were reviewed on **2026-08-31**. Automated checks validate structure and source reachability; factual updates still require source-backed editorial review.

## Maintenance

Update this independently versioned module when material facts, project status, canonical documentation, or important trade-offs change. Preserve the stable module address unless a compatibility migration is explicitly documented.
