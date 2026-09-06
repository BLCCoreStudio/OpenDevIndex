# History

## 2026-09-06 — deep-dive

- Promoted `cloud/prometheus` from a compact schema-v1 overview to a schema-v3 deep technical reference.
- Reframed the module around the complete metrics pipeline: discovery, relabeling, scraping, ingestion, local TSDB, PromQL, rules, alerting, APIs, federation, and remote storage integration.
- Documented counters, gauges, classic/native histograms, summaries, labels, cardinality, churn, metric naming, and instrumentation design.
- Added TSDB head/WAL/block/compaction/retention concepts, storage safety guidance, HA patterns, remote write/read, federation, scaling, and capacity planning.
- Added PromQL evaluation types, rate/reset handling, aggregation, vector matching, recording-rule contracts, alert design, and common query mistakes.
- Added Kubernetes, Grafana, and OpenTelemetry integration boundaries plus security, failure modes, debugging workflows, anti-patterns, an operational checklist, and a staged learning path.
- Added Technology Universe coverage metadata and typed relationships to Kubernetes, Grafana, and OpenTelemetry.
- Verified the Apache-2.0 license and expanded sources to current upstream architecture, data-model, query, rule, storage, instrumentation, federation, remote-write, and API documentation.

## 2026-08-31 — v0.1

- Reviewed `cloud/prometheus` against the current OpenDevIndex catalog and taxonomy.
- Recorded canonical kind `platform` and domain facets: observability.
- Re-rendered module documentation from validated source-backed metadata.

## Earlier history

## 2026-08-31

- Added `cloud/prometheus` to the curated OpenDevIndex v0.1 catalog.
- Created the initial source-backed knowledge module.
- Verified metadata structure and required references with the repository validator.
