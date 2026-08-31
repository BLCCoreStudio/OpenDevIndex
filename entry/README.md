# CockroachDB

> Distributed SQL database designed for horizontal scale and resilience while presenting a PostgreSQL-compatible SQL interface and transactional consistency model.

## What it is

CockroachDB is indexed as a **database**. Its stable OpenDevIndex address is `database/cockroachdb`; taxonomy facets are kept separate from that address so classification can improve without breaking links.

## Why it matters

The module focuses on the technology's practical role, high-signal characteristics, common use cases, and authoritative references. Fast-changing details should be verified against the sources below rather than inferred from stale copies.

## Typical use cases

- Run globally distributed transactional applications
- Scale SQL workloads across multiple nodes
- Build services that need automatic replication and node-failure tolerance

## Key points

- CockroachDB distributes ranges of data across cluster nodes
- It provides serializable transactions by default
- Its SQL surface is intentionally compatible with many PostgreSQL tools and drivers

## Taxonomy

- Kind: `database`
- Domains: `data`, `distributed-systems`
- Deployment: `self-hosted`, `service`
- License metadata: `not yet curated`

## Primary links

- Homepage: https://www.cockroachlabs.com/docs/
- Repository: https://github.com/cockroachdb/cockroach

## Verified sources

- [CockroachDB documentation](https://www.cockroachlabs.com/docs/) — `documentation`
- [CockroachDB source repository](https://github.com/cockroachdb/cockroach) — `repository`

## Verification

The catalog metadata and source references for this module were reviewed on **2026-08-31**. Automated checks validate structure and source reachability; factual updates still require source-backed editorial review.

## Maintenance

Update this independently versioned module when material facts, project status, canonical documentation, or important trade-offs change. Preserve the stable module address unless a compatibility migration is explicitly documented.
