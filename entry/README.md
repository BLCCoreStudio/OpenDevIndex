# Prometheus

> Open-source metrics monitoring and alerting platform built around labeled time series, pull-oriented scraping, PromQL, local TSDB storage, rule evaluation, and integrations for visualization and long-term or distributed storage.

Prometheus is best understood as a **metrics collection, time-series storage, query, and rule-evaluation system** whose core design favors operational reliability and local autonomy over transparent distributed storage.

The shortest useful mental model is:

```text
instrumented targets / exporters
            |
            | HTTP scrape
            v
      service discovery
            |
      target relabeling
            |
            v
       Prometheus server
   +-----------------------+
   | scrape + ingest       |
   | local TSDB            |
   | PromQL engine         |
   | recording rules       |
   | alerting rules        |
   +-----------------------+
        |             |
        |             +----> Alertmanager -> notifications
        |
        +----> HTTP API -> Grafana / clients
        |
        +----> remote write -> external / long-term storage
```

Prometheus does **not** attempt to be a general event log, a tracing backend, a billing ledger, or a magically clustered database. Its strengths come from a deliberately narrower model: numeric observations over time, identified by labels, collected frequently enough to answer operational questions.

---

## Why it matters

Modern systems are dynamic. Instances appear and disappear, Kubernetes Pods are rescheduled, autoscalers change replica counts, and individual hostnames are often poor long-term identifiers. Prometheus addresses this with a dimensional data model:

```text
metric name + label set -> time series -> timestamped samples
```

Instead of defining a separate metric name for every combination, the same metric can carry dimensions such as service, status code, method, region, cluster, or instance.

This makes aggregation and slicing natural:

```promql
sum by (service) (rate(http_requests_total[5m]))
```

The same flexibility creates one of Prometheus's largest operational risks: **cardinality explosion**. Every unique label set is another time series with memory, CPU, disk, query, and network cost.

---

# Core architecture

## Prometheus server

The Prometheus server combines several responsibilities in one autonomous process:

- target discovery;
- scrape scheduling;
- sample ingestion;
- local time-series storage;
- PromQL query execution;
- recording-rule evaluation;
- alerting-rule evaluation;
- HTTP API and UI endpoints;
- optional remote-read / remote-write integration.

This integrated architecture is important. A single server can continue scraping, querying recent data, and evaluating rules even when external dashboards or remote storage are unavailable.

That local independence is a reliability feature, not merely a deployment convenience.

## Exporters

An exporter translates metrics from a system that does not natively expose Prometheus-format metrics.

Examples include host, database, proxy, and hardware exporters.

Conceptually:

```text
legacy / external system
       |
       v
    exporter
       |
       v
Prometheus exposition endpoint
       |
       v
   Prometheus scrape
```

Exporters should expose a stable semantic metric model. Simply converting every internal field into a label is usually a bad design.

## Client libraries

Applications can expose metrics directly using Prometheus client libraries or compatible instrumentation libraries.

Typical instrumentation captures:

- request counts;
- failures;
- duration distributions;
- queue depth;
- in-progress operations;
- resource usage;
- domain-specific business or system signals.

Instrumentation is part of the software interface. Metric names, label meanings, and histogram boundaries become dependencies for dashboards, alerts, SLO calculations, and automation.

## Pushgateway

Prometheus primarily uses a pull model. Pushgateway exists for a narrower case: short-lived service-level batch jobs that may terminate before they can be scraped.

It should not be treated as a generic replacement for scraping.

Pushed series can outlive the process that created them, so lifecycle cleanup becomes the operator's responsibility. For machine-level batch jobs, the node textfile collector pattern is often more appropriate.

## Alertmanager

Prometheus evaluates alerting expressions and sends firing alert instances to Alertmanager. Alertmanager then handles concerns such as:

- grouping;
- deduplication;
- routing;
- silencing;
- inhibition;
- notification delivery.

Keep the ownership boundary clear:

```text
Prometheus: should this alert be firing?
Alertmanager: how should firing alerts be routed and delivered?
```

## Grafana and other API clients

Prometheus includes its own expression browser, but rich operational visualization is commonly provided by Grafana or other consumers of the Prometheus HTTP API.

A dashboard is therefore usually **not** the source of metric data. It is a query client over Prometheus or a compatible backend.

---

# Data model

## A time series is an identity, not just a metric name

A Prometheus time series is identified by its metric name and full set of labels.

For example:

```text
http_requests_total{
  service="checkout",
  method="POST",
  code="200"
}
```

and:

```text
http_requests_total{
  service="checkout",
  method="POST",
  code="500"
}
```

are two different time series.

Changing a label value changes the series identity.

## Samples

A series contains samples associated with timestamps. PromQL generally evaluates values at explicit evaluation times and applies lookback and staleness semantics rather than assuming every target emits a sample at the exact query timestamp.

This matters when debugging gaps, disappearing targets, and range queries.

## Labels

Labels are dimensions. Good labels describe bounded categories useful for aggregation.

Good candidates often include:

- HTTP method;
- status class/code;
- service;
- cluster;
- region;
- queue name;
- operation type.

Dangerous candidates include unbounded or nearly unbounded identifiers:

- user ID;
- email address;
- request ID;
- trace ID as a regular label;
- session ID;
- full URL including arbitrary path parameters;
- timestamp;
- random UUID.

The rule is not “labels must be few.” The rule is that the **cross-product of values must remain economically bounded**.

## Special labels

Prometheus uses labels internally during discovery and relabeling. Labels beginning with `__` generally have special roles and may be removed before ingestion unless mapped into persistent labels.

`__name__` represents the metric name in PromQL's label model.

---

# Metric types

Metric types describe the intended semantics of observations. Prometheus's storage model ultimately stores time-series samples, while client libraries and exposition metadata communicate metric type.

## Counter

A counter represents a cumulative value that normally only increases, except when it resets because the process restarts or the counter is otherwise reinitialized.

Examples:

- requests served;
- bytes transmitted;
- jobs completed;
- failures observed.

Counters are usually queried with `rate()` or `increase()` rather than graphed as raw cumulative totals.

```promql
rate(http_requests_total[5m])
```

PromQL's counter-aware functions account for resets.

## Gauge

A gauge represents a value that can move up or down.

Examples:

- queue depth;
- memory usage;
- temperature;
- current connections;
- desired replica count.

A gauge should not be passed through counter-specific reasoning just because it happens to trend upward for a period.

## Histogram

Histograms observe distributions such as latency or size.

Classic histograms expose cumulative bucket series plus count and sum. Native histograms can represent histogram samples more compactly and dynamically, but support and behavior are version-sensitive and should be verified against the exact Prometheus/client/backend versions in use.

Histograms are especially useful when you need aggregation across instances.

For a classic request-duration histogram, a quantile may be estimated with:

```promql
histogram_quantile(
  0.95,
  sum by (le) (rate(http_request_duration_seconds_bucket[5m]))
)
```

Bucket design matters: a histogram cannot recover resolution that was never observed.

## Summary

Summaries can calculate client-side quantiles in supported client libraries.

The main trade-off is that precomputed client-side quantiles are generally not aggregatable across independent instances in the same way histogram buckets are.

For fleet-wide percentile questions, histograms are often a better fit.

---

# Pull-oriented collection

Prometheus commonly scrapes targets over HTTP at a configured interval.

A scrape cycle conceptually performs:

```text
discover target
   |
   v
apply target relabeling
   |
   v
HTTP request to metrics endpoint
   |
   v
parse exposition
   |
   v
apply metric relabeling
   |
   v
append accepted samples to TSDB
```

## Why pull works well

Pulling gives the monitoring system explicit knowledge of targets and scrape health.

If a target cannot be scraped, Prometheus can record that failure directly through the synthetic `up` metric.

That creates an important distinction:

```text
no business metric because value is zero
```

versus:

```text
no metric because collection failed
```

A push-only design can make those cases harder to distinguish.

## Scrape interval

A shorter interval gives higher temporal resolution but increases:

- samples per second;
- storage use;
- network traffic;
- target CPU cost;
- Prometheus ingestion work.

A longer interval reduces cost but can miss short-lived behavior and reduces resolution for rates and alerting.

Choose intervals from operational requirements, not convention alone.

## Scrape timeout

The timeout must be shorter than or compatible with the scrape interval. Slow exporters can consume scrape capacity and create false monitoring gaps.

A metrics endpoint should normally be cheap enough that observing a service does not materially harm it.

---

# Service discovery

Static target lists are sufficient for small stable systems. Dynamic environments need discovery.

Prometheus supports many discovery mechanisms, including Kubernetes and cloud/provider-specific integrations.

Discovery produces target metadata. Relabeling turns that metadata into the final scrape target and target labels.

A useful mental model is:

```text
raw discovered object
        |
        v
__meta_* labels
        |
        v
relabel rules
        |
        v
keep/drop target + map useful metadata
        |
        v
final scrape identity
```

## Kubernetes discovery

In Kubernetes, Prometheus can discover resources such as Pods, Services, Endpoints/EndpointSlices, and Nodes depending on role and configuration.

Kubernetes discovery does not mean “scrape everything.” Production setups normally select targets through annotations, labels, operators, or explicit monitoring custom resources.

Poorly constrained discovery can create enormous target sets and cardinality.

---

# Relabeling

Relabeling is one of Prometheus's most powerful and most frequently misunderstood mechanisms.

There are several stages with different purposes.

## Target relabeling

Applied before scraping. It can:

- keep or drop discovered targets;
- rewrite target addresses;
- select metrics paths;
- map discovery metadata into target labels;
- normalize instance/job identity.

If a target never appears on the Targets page, debug target discovery and target relabeling before investigating metric relabeling.

## Metric relabeling

Applied after a successful scrape but before samples are stored.

It can:

- drop unwanted series;
- rewrite labels;
- reduce ingestion cardinality.

Dropping a metric here still incurs the cost of fetching and parsing it from the target. If the exporter itself can avoid generating the metric, that can be cheaper.

## Write relabeling

Applied before samples are sent through remote write.

This lets an operator keep local data while sending only selected data remotely, or normalize outbound labels for a remote backend.

Do not mix these stages mentally. A rule in the wrong stage may appear to “do nothing” because the relevant labels are no longer present.

---

# Local TSDB

Prometheus includes a local on-disk time-series database.

The design is optimized for append-heavy metric workloads and autonomous single-server operation.

## Head block and WAL

Recent samples live in the in-memory/head portion of the database and are protected against process crashes by a write-ahead log (WAL).

Conceptually:

```text
incoming samples
      |
      +----> WAL
      |
      v
    Head
      |
      v
persisted TSDB blocks
      |
      v
background compaction
```

The WAL is part of crash recovery. Deleting it to recover from corruption may lose recent data.

## Blocks

Persisted data is organized into time-based blocks containing:

- chunk data;
- index data;
- metadata;
- tombstones for deletions where applicable.

Background compaction combines smaller blocks into larger ones.

Compaction temporarily needs extra disk because source and replacement blocks coexist during the operation.

## Retention

Retention can be bounded by time, size, or both. When both are configured, the first effective limit wins.

Plan disk headroom for:

- persistent blocks;
- WAL;
- head chunks;
- temporary compaction overhead;
- unexpected cardinality increases.

Running a TSDB at nearly 100% disk utilization is an avoidable outage pattern.

## Filesystem assumptions

Prometheus's local TSDB expects reliable local/POSIX filesystem semantics. Upstream documentation specifically warns against unsupported network filesystems such as typical NFS deployments for the local database.

If durable replicated object storage is required, use an architecture designed for remote/distributed storage rather than placing the local TSDB directory on an unsuitable shared filesystem.

## Backups

Use supported snapshot-based procedures rather than copying a live data directory blindly.

A backup strategy must be tested by restore. A file archive that has never been restored is only a hypothesis.

---

# PromQL mental model

PromQL is a functional query language over labeled time series.

Most confusion disappears when the value types and evaluation time are explicit.

## Instant vector

A set of time series with one sample per series at the evaluation time.

Example:

```promql
up{job="api"}
```

## Range vector

A set of series, each containing samples over a time window.

Example:

```promql
http_requests_total[5m]
```

Range vectors are often input to functions such as `rate()`.

## Scalar

A single numeric value.

## String

A string value exists in the language type system but is used much less often in normal monitoring queries.

## Native histogram samples

Modern Prometheus can also evaluate native histogram samples in supported operations. Always verify function/operator support when mixing float and histogram samples.

---

# Rates and counters

For a counter, the raw value is usually less useful than its change rate.

```promql
rate(requests_total[5m])
```

A common aggregation pattern is:

```promql
sum by (service) (
  rate(requests_total[5m])
)
```

Apply the counter-aware function before aggregation when resets must be detected per underlying series.

Bad conceptual order:

```text
aggregate counters first -> reset identity may be lost -> rate later
```

Better:

```text
rate each counter series -> aggregate the rates
```

---

# Vector matching

Binary operations between vectors match series by labels.

This is powerful but easy to get wrong.

`on(...)`, `ignoring(...)`, and group modifiers control matching semantics.

Before writing a many-to-one join, state explicitly:

- what is the join key?
- which side is unique?
- which labels should survive?
- can duplicate keys appear later?

A query that “works today” because labels happen to be unique can break when infrastructure expands.

---

# Aggregation

Common aggregation operators include:

- `sum`;
- `avg`;
- `min`;
- `max`;
- `count`;
- `topk` / `bottomk`;
- quantile-related operations where appropriate.

Prefer `by(...)` when you want to state the labels that define the output identity.

Example:

```promql
sum by (cluster, service) (
  rate(http_requests_total[5m])
)
```

Be cautious with `without(...)` in long-lived rules when new labels may be added later and accidentally leak into the output identity.

---

# Recording rules

Recording rules evaluate PromQL periodically and store the result as new time series.

They are useful for:

- expensive repeated dashboard queries;
- stable SLI components;
- cross-team query contracts;
- pre-aggregated fleet views;
- multi-stage alert expressions.

Example conceptually:

```yaml
groups:
- name: api.rules
  rules:
  - record: service:http_requests:rate5m
    expr: sum by (service) (rate(http_requests_total[5m]))
```

A recording rule trades query-time computation for ingestion/storage and evaluation work.

Bad recording rules can also permanently encode poor labels or unnecessary high-cardinality results.

Use names that communicate aggregation and window semantics.

---

# Alerting rules

Alerting rules evaluate PromQL conditions over time.

A robust alert usually has:

- a symptom-oriented expression;
- a duration (`for`) that filters brief noise where appropriate;
- stable labels used for routing;
- annotations that explain impact and investigation context;
- a runbook or dashboard reference when practical.

Example shape:

```yaml
- alert: HighErrorRate
  expr: ...
  for: 10m
  labels:
    severity: page
  annotations:
    summary: "..."
```

Prometheus determines whether each alert instance is pending or firing. Alertmanager controls downstream delivery behavior.

## Alert on symptoms

Prefer alerts that correlate with user-visible or service-objective pain over alerts for every possible low-level cause.

A page should normally imply an actionable human response.

This reduces alert fatigue and keeps paging semantics trustworthy.

---

# Cardinality economics

Cardinality is central to Prometheus capacity planning.

Suppose a metric has labels:

```text
service: 50 values
method: 6 values
status: 20 values
region: 8 values
instance: 500 values
```

The theoretical cross-product is enormous even before additional dimensions.

Not every combination may exist, but the model illustrates the risk.

## Why high cardinality hurts

More active series increase:

- head memory;
- index size;
- WAL volume;
- disk usage;
- compaction work;
- scrape parsing;
- query planning/execution;
- remote-write traffic;
- cache pressure in downstream systems.

## Churn is separate from steady cardinality

A system can have a moderate number of active series but extreme **series churn** if labels include ephemeral identifiers.

For example, placing a Kubernetes Pod UID or request ID into a label can continuously create new series identities.

Churn stresses the index and storage even after old series stop receiving samples.

## Cardinality review questions

Before adding a label, ask:

1. How many values can it have today?
2. How many could it have at 10x scale?
3. Is the set bounded by design?
4. Does an operator need to aggregate/filter by it?
5. Could the information live in logs or traces instead?
6. Does the label change frequently for the same logical workload?

---

# Instrumentation design

## Counters for events

Prefer counters for cumulative events and derive rates.

Examples:

```text
requests_total
errors_total
processed_bytes_total
jobs_completed_total
```

## Gauges for current state

Examples:

```text
queue_depth
active_sessions
inflight_requests
memory_bytes
```

## Measure both count and latency

For a request path, a useful base often includes:

- total requests;
- failures or outcome labels;
- duration histogram;
- in-flight requests where saturation matters.

A latency dashboard without traffic volume can mislead. A 10-second request may be catastrophic at 10,000 RPS and irrelevant if it occurs once in a batch job.

## Metric naming

Use consistent base units and suffix conventions.

Common patterns include:

- `_total` for counters;
- `_seconds` for durations;
- `_bytes` for sizes.

Keep one metric family semantically coherent. Do not mix unrelated quantities because they happen to share dimensions.

---

# Histograms and SLOs

Latency SLOs commonly require distributions rather than averages.

An average can hide tail pain:

```text
99 requests at 20 ms
1 request at 10 s
```

The mean is not a good description of the outlier experience.

## Bucket design

Classic histogram bucket boundaries should reflect meaningful service thresholds.

If an SLO is “95% under 300 ms,” include useful resolution around that boundary.

Buckets that are too coarse create quantile estimation error. Too many buckets multiply series cardinality.

## Aggregation

Histogram buckets can be aggregated across replicas when label dimensions and bucket definitions are compatible.

This is one reason histograms are preferred over client-side summary quantiles for many distributed service SLOs.

---

# Remote write

Remote write streams samples from Prometheus to a compatible remote endpoint.

Typical reasons include:

- long-term retention;
- global query layers;
- managed monitoring backends;
- multi-cluster aggregation;
- durable replicated storage;
- central analytics.

Remote write adds a queue and another failure domain.

Conceptually:

```text
scrape -> local ingest -> remote-write WAL/queue -> remote endpoint
```

Do not assume remote storage replaces the local reliability role automatically. Prometheus is still designed so local monitoring can remain useful when remote systems fail, depending on configuration.

## Operational concerns

Monitor:

- queue backlog;
- failed samples;
- retries;
- shard count;
- endpoint latency;
- memory usage;
- dropped samples;
- WAL growth.

A slow remote endpoint can consume substantial memory and create backlog.

Write relabeling can reduce outbound data before transmission.

## Protocol versions

Prometheus supports versioned remote-write protocols. Newer protocol capabilities such as richer metadata and native-histogram transport are version-sensitive; verify compatibility with the specific remote backend before changing wire-format settings.

---

# Remote read

Remote read allows Prometheus to query compatible external storage in supported configurations.

It should not be treated as a universal transparent distributed database layer. Query latency, backend capability, API stability, and data consistency characteristics depend on the remote system.

Large-scale Prometheus ecosystems often use purpose-built projects that implement distributed query/storage architectures rather than relying on a single Prometheus node to behave like a cluster.

---

# Federation

Federation lets one Prometheus server scrape selected series from another Prometheus server's `/federate` endpoint.

Two common patterns are:

## Hierarchical federation

```text
local Prometheus A ---\
local Prometheus B ----> global Prometheus
local Prometheus C ---/
```

The global server usually collects aggregated or high-value series, while local servers retain detailed per-instance metrics.

## Cross-service federation

One service's Prometheus can import selected metrics from another monitoring domain so related signals can be queried together.

Federation is not a free replacement for distributed storage. It creates another scrape topology with explicit selection and retention semantics.

---

# High availability

Prometheus local storage is not natively a replicated clustered TSDB.

A common HA pattern runs multiple Prometheus servers independently scraping the same targets.

```text
             targets
             /    \
            v      v
      Prometheus A Prometheus B
```

This duplicates ingestion deliberately so loss of one monitoring server does not eliminate current visibility.

Alertmanager deployments can deduplicate equivalent alerts from multiple Prometheus replicas when external labels and routing are designed correctly.

For global query and long-term storage, additional systems may sit above or beside these replicas.

## Replica labels

When multiple replicas write to a central system, a replica identity label is often needed for source distinction, while the global query layer may deduplicate replicas.

Do not accidentally include a replica label in alert identity if that causes one real incident to page multiple times.

---

# Kubernetes integration

Prometheus fits Kubernetes well because both systems are label-oriented and dynamic.

A typical pipeline is:

```text
Kubernetes API discovery
       |
       v
Pod / Service / Endpoint metadata
       |
       v
relabeling / monitor selection
       |
       v
scrape targets
       |
       v
Prometheus TSDB
```

In operator-managed environments, custom resources such as ServiceMonitor/PodMonitor may generate scrape configuration indirectly. Those resources belong to the Prometheus Operator ecosystem rather than the core Prometheus server itself.

Keep that distinction clear when debugging:

```text
monitoring CRD -> generated Prometheus config -> discovered target -> scrape
```

A failure at the CRD/operator layer is different from a failed HTTP scrape.

---

# Grafana integration

Grafana typically queries Prometheus through its HTTP API.

The boundaries are:

```text
Prometheus: collect/store/query metrics
Grafana: visualize/query/compose dashboards
```

Dashboard variables can generate expensive or high-cardinality queries. A visually simple dashboard may execute dozens or hundreds of PromQL requests when repeated panels and variables expand.

Treat dashboard query cost as production workload on Prometheus.

---

# OpenTelemetry integration

OpenTelemetry and Prometheus overlap in metrics instrumentation and transport but are not identical products.

OpenTelemetry provides APIs, SDKs, semantic conventions, and Collector pipelines across metrics, traces, and logs. Prometheus provides a mature metrics scrape/query/rule/TSDB ecosystem.

Common integrations include:

- OpenTelemetry Collector exposing Prometheus-scrape endpoints;
- Collector scraping Prometheus-compatible metrics;
- Collector forwarding metrics toward Prometheus-compatible remote-write storage;
- applications instrumented with OpenTelemetry while Prometheus remains the metrics backend.

When mixing systems, verify semantic conversion of:

- metric names;
- units;
- temporality;
- histograms;
- resource attributes/labels;
- counters and resets.

A syntactically successful conversion can still be semantically wrong.

---

# Security model

Prometheus is operational infrastructure and often sees sensitive topology information.

## Protect the HTTP interface

Depending on configuration, the API exposes:

- metric values;
- label values;
- target metadata;
- configuration/status information;
- query capabilities;
- administrative endpoints if explicitly enabled.

Do not expose Prometheus directly to untrusted networks merely because the data is “only metrics.” Labels can contain hostnames, service names, tenant identifiers, internal paths, or other sensitive metadata.

## Scrape credentials

Prometheus may hold credentials for scraping protected endpoints and querying service-discovery APIs.

Use least privilege and secure secret delivery.

## Remote write credentials

Remote-write endpoints often require credentials with ingestion privileges. Protect them like other production service credentials.

## Label privacy

Never place secrets, tokens, email addresses, or sensitive user identifiers in metric labels.

Metrics are optimized for aggregation, replication, caching, and operational access—not secret storage.

## Exporter trust

An exporter transforms external data into monitoring data. A compromised exporter can create enormous cardinality or misleading metrics even if it cannot modify application state.

Resource limits and scrape limits can help contain damage.

---

# Failure modes

## Target is DOWN

Start with the target page and `up` metric.

Check:

1. Was the target discovered?
2. Did relabeling keep it?
3. Is the final address correct?
4. Is DNS/network connectivity working?
5. Is TLS/auth correct?
6. Does the metrics endpoint respond within timeout?
7. Is the exposition valid?

Do not debug PromQL before confirming collection.

## Metric is missing but target is UP

Possible causes:

- application stopped exposing it;
- metric is conditional and has not been initialized;
- metric relabeling dropped it;
- exporter filters removed it;
- name changed;
- label selector is too restrictive;
- scrape/sample limits rejected data.

## Query returns no data

Check:

- evaluation time;
- label matchers;
- staleness;
- target lifetime;
- metric rename;
- scrape gaps;
- recording-rule output;
- whether you need an instant or range expression.

## Counter rate spikes after restart

Use PromQL counter-aware functions rather than manual subtraction. Also verify exporter instrumentation is actually monotonic between resets.

## Prometheus memory grows unexpectedly

Investigate active-series cardinality and churn first.

Likely causes:

- new high-cardinality label;
- broad Kubernetes discovery;
- dynamic path/user/request labels;
- exporter upgrade exposing many new series;
- scrape interval reduction;
- duplicate targets.

## Disk fills

Check:

- retention settings;
- ingestion rate;
- active series;
- WAL size;
- compaction backlog/errors;
- temporary compaction headroom;
- remote-write backlog if relevant.

Do not simply increase retention repeatedly without capacity modeling.

## Query is slow

Look for:

- selectors matching huge series sets;
- long time ranges;
- small query steps over long ranges;
- regex matchers over large label spaces;
- expensive joins;
- histogram cardinality;
- dashboard fan-out;
- missing recording rules for repeatedly expensive aggregations.

## Alert never fires

Inspect the expression at current time, then the alert's pending state and `for` duration.

Also verify rule-group evaluation health and interval.

## Alert fires but nobody receives it

The problem may be downstream of Prometheus:

```text
rule evaluation -> alert sent -> Alertmanager routing -> receiver
```

Check each boundary separately.

## Remote write falls behind

Inspect queue metrics, endpoint errors, network latency, retry behavior, and remote capacity. Backpressure can grow over time even when the endpoint is only slightly slower than sustained ingestion.

---

# Debugging workflow

## 1. Verify configuration

Use `promtool` to validate configuration and rule files before deployment.

Typical workflow:

```bash
promtool check config prometheus.yml
promtool check rules rules.yml
```

## 2. Check runtime targets

Use the Prometheus target/status UI or HTTP API to inspect:

- discovered labels;
- final labels;
- scrape URL;
- last scrape;
- scrape duration;
- last error.

## 3. Query the raw series

Start with the exact metric before building a complex expression.

```promql
http_requests_total
```

Then narrow labels.

## 4. Build PromQL incrementally

A useful sequence is:

```text
raw selector
 -> range selector
 -> rate/increase
 -> aggregation
 -> arithmetic
 -> threshold / join
```

Inspect the output at each step.

## 5. Inspect rule evaluation

Check rule-group status, last evaluation, evaluation duration, and errors.

## 6. Inspect TSDB health

Monitor Prometheus's own metrics for:

- head series;
- samples appended;
- WAL/compaction issues;
- rule evaluation;
- query load;
- remote write;
- scrape health.

Prometheus should monitor itself.

---

# Capacity planning

A rough storage model begins with:

```text
samples/second
  = active scraped series / scrape interval
```

and:

```text
storage
  ~= samples/second x retention seconds x compressed bytes/sample
```

But real capacity also includes:

- indexes;
- label data;
- WAL;
- head memory;
- compaction headroom;
- tombstones;
- recording-rule output;
- remote-write queue memory.

Series count and churn are often more important than raw sample compression.

## Scaling levers

Before introducing a distributed backend, consider:

- dropping unused metrics;
- reducing label cardinality;
- increasing scrape intervals for low-value metrics;
- separating workloads across Prometheus servers;
- using recording rules;
- reducing dashboard/query fan-out;
- federating selected aggregates;
- using remote write for long-term/global requirements.

Distributed storage should solve a real requirement, not compensate for uncontrolled instrumentation.

---

# Recording rules as an API layer

At scale, stable recording rules can become a useful contract between platform teams and consumers.

Instead of every dashboard reimplementing a complex service calculation, the platform can publish a named series with controlled labels.

Example conceptual layers:

```text
raw metrics
    |
    v
service-level recording rules
    |
    v
SLO / dashboard / alert expressions
```

Benefits:

- consistent semantics;
- reduced repeated query cost;
- simpler consumer queries;
- easier review of critical calculations.

Risk:

- a wrong recording rule propagates wrong semantics everywhere.

Treat important rule files as production code: review, test, version, and validate them.

---

# Alert design

A good alert answers:

1. What user/system symptom is happening?
2. How severe is it?
3. Which ownership boundary should receive it?
4. Is there a useful action now?
5. Where should the operator look next?

Avoid alerts such as “CPU > 80%” without service context unless high CPU itself is the actionable failure mode.

A high CPU signal may be useful as dashboard context while latency/error/SLO burn is the page.

## Multi-window burn-rate alerts

For SLO-driven systems, error-budget burn-rate alerts can detect both fast catastrophic burn and slower sustained burn.

The exact windows and thresholds are service-policy decisions, not universal Prometheus defaults.

---

# Common PromQL mistakes

## Using `rate()` on a gauge

`rate()` is intended for counters. For gauges, use functions appropriate to the question such as average/min/max over time or derivation where mathematically justified.

## Summing before counter reset handling

Prefer:

```promql
sum(rate(counter_total[5m]))
```

over applying `rate()` to an already-aggregated expression that can no longer identify individual resets.

## Averaging averages

An average of per-instance averages is not generally the fleet average unless weights are equal.

Prefer carrying numerator and denominator separately, then divide after aggregation.

## Averaging percentiles

Percentiles are not composable by ordinary averaging.

Aggregate histogram distributions first, then calculate the quantile where supported.

## Using unbounded regex selectors

Broad regex matchers can scan enormous label spaces and make dashboards unpredictable.

## Ignoring missing data

A query returning nothing is different from a query returning zero. Decide explicitly what missing series should mean.

---

# Anti-patterns

## User IDs in labels

Creates unbounded cardinality and privacy risk.

## One Prometheus for every workload forever

Extreme fragmentation complicates global operations and rule consistency.

## One giant Prometheus for the entire organization

Creates an enormous blast radius and capacity boundary.

## Network filesystem for local TSDB

Violates the storage assumptions documented upstream and can lead to corruption/reliability problems.

## Pushgateway for normal services

Weakens target-health/lifecycle semantics and creates stale pushed series.

## Alerting on every low-level anomaly

Produces fatigue and hides truly actionable pages.

## Dashboard-only monitoring

A dashboard nobody is looking at is not an alerting strategy.

## Remote write without monitoring the queue

Turns central storage outages into silent backlog or data-loss surprises.

## Unreviewed exporter upgrades

Can unexpectedly add thousands of series or change metric semantics.

---

# Operational checklist

Before a production deployment, verify:

- scrape targets have clear ownership;
- service discovery is constrained;
- relabeling rules are reviewed and tested;
- label cardinality budgets exist;
- metrics do not contain secrets or user identifiers;
- important counters/histograms follow stable naming and unit conventions;
- scrape interval and timeout match operational requirements;
- Prometheus monitors its own ingestion, TSDB, query, rule, and remote-write health;
- disk retention leaves compaction/WAL headroom;
- backups/snapshots are tested by restore;
- HA replicas are independent where monitoring availability requires them;
- alert rules are symptom-oriented and actionable;
- Alertmanager routes and silences are tested;
- remote-write backlog and failures are monitored;
- expensive dashboards have query budgets or recording rules;
- upgrades are tested against PromQL, rules, remote storage, and native-histogram compatibility.

---

# Learning path

## Beginner

Learn:

1. metric names and labels;
2. counter versus gauge;
3. scrape targets and `up`;
4. instant versus range queries;
5. `rate()` and aggregation;
6. basic alert rules.

Practice:

- instrument a small HTTP service;
- scrape it;
- restart it and observe counter resets;
- create a latency histogram;
- query request rate and error ratio.

## Intermediate

Learn:

1. service discovery;
2. target and metric relabeling;
3. recording rules;
4. histograms and quantiles;
5. vector matching;
6. Alertmanager boundary;
7. TSDB retention and cardinality.

Practice:

- scrape a Kubernetes workload;
- intentionally drop an unwanted metric;
- create a recording rule;
- diagnose a high-cardinality label;
- design a symptom-based alert.

## Advanced

Learn:

1. WAL/head/block storage behavior;
2. remote write/read;
3. federation;
4. HA replicas and deduplication architectures;
5. long-term/distributed storage integrations;
6. SLO burn-rate alerting;
7. native histograms;
8. query/capacity engineering.

Practice:

- simulate remote-write failure and recovery;
- size retention from measured ingestion;
- build an HA pair;
- profile expensive PromQL;
- compare local storage, federation, and remote-storage architectures for a real scale target.

---

# When Prometheus is a good fit

Prometheus is especially strong for:

- numeric operational metrics;
- dynamic service-oriented infrastructure;
- Kubernetes/cloud-native environments;
- SRE alerting and diagnosis;
- multidimensional aggregation;
- environments where local monitoring should remain available during broader infrastructure failure.

# When it is not the right source of truth

Do not use Prometheus as the authoritative system for:

- exact billing/accounting events;
- audit logs;
- per-request forensic records;
- arbitrary text search;
- durable business transactions;
- trace-span storage.

Prometheus intentionally tolerates gaps and operational trade-offs that are acceptable for monitoring but inappropriate for financial correctness or legal audit evidence.

---

# Relationships in OpenDevIndex

- `cloud/kubernetes` — dynamic target discovery and one of the most important deployment environments for Prometheus.
- `cloud/grafana` — common visualization and query client for Prometheus-compatible data sources.
- `cloud/opentelemetry` — complementary telemetry instrumentation/collection ecosystem that can interoperate with Prometheus metrics pipelines.

Alertmanager is also architecturally central to Prometheus alert delivery, but no standalone OpenDevIndex module is linked here until a stable module address exists.

---

# Verification

This deep-dive was reviewed on **2026-09-06** against current upstream Prometheus documentation covering architecture, data model, metric types, PromQL, configuration, recording and alerting rules, storage, remote write, federation, instrumentation, naming, histograms, alerting practices, and the HTTP API.

The module intentionally avoids hard-coding release-specific feature-state assumptions where they may change. Native histogram behavior, remote-write protocol choices, command-line defaults, API details, and integrations should be checked against the documentation for the exact Prometheus release and remote backend in use.

---

# Maintenance

Update this module when any of the following materially changes:

- PromQL semantics;
- native histogram support or defaults;
- scrape/exposition behavior;
- TSDB or WAL architecture;
- service-discovery or relabeling behavior;
- remote-write/read protocols;
- alert/rule semantics;
- storage safety guidance;
- supported deployment topology;
- security guidance.

Preserve the stable OpenDevIndex address `cloud/prometheus`. Deep-dive content should remain hand-curated and source-backed instead of being replaced by a generic catalog renderer.
