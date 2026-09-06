# OpenTelemetry

> Vendor-neutral observability framework and specification for instrumenting, generating, correlating, collecting, processing, and exporting traces, metrics, logs, and evolving telemetry signals through common APIs, SDKs, semantic conventions, context propagation, OTLP, and the OpenTelemetry Collector.

OpenTelemetry is best understood as an **observability interoperability layer**, not as an observability database or dashboard product.

It standardizes important boundaries between application code, instrumentation libraries, telemetry pipelines, and backends:

```text
application / library
        |
        v
OpenTelemetry API
        |
        v
OpenTelemetry SDK
        |
        +--> processors / sampling / aggregation
        |
        v
      exporter
        |
        v
       OTLP
        |
        v
OpenTelemetry Collector
        |
        +--> receive
        +--> process
        +--> route
        +--> export
        |
        v
observability backend(s)
```

The backend still owns storage, indexing, querying, visualization, retention, and backend-specific analytics. OpenTelemetry deliberately leaves those responsibilities to systems such as Prometheus-compatible metrics platforms, tracing backends, logging platforms, and commercial observability services.

That separation is the source of OpenTelemetry's portability—and also the reason operators need to understand the boundaries precisely.

---

# Why OpenTelemetry matters

Without a common telemetry model, an organization can end up with a different vendor SDK in every application:

```text
service A -> vendor A tracing SDK
service B -> vendor B metrics SDK
service C -> custom logging agent
```

Changing backend then becomes an application-instrumentation migration.

OpenTelemetry changes the intended architecture to:

```text
application instrumentation
        |
        v
OpenTelemetry APIs + conventions
        |
        v
portable telemetry pipeline
        |
        +----> backend A
        +----> backend B
        +----> migration / dual export
```

The portability is not absolute. Backends still differ in query languages, storage models, supported semantic conventions, histogram behavior, trace sampling, log features, and operational limits. But OpenTelemetry significantly reduces coupling at the **generation and transport** layer.

---

# What OpenTelemetry is — and is not

OpenTelemetry is:

- a cross-language specification;
- language APIs for producing telemetry;
- SDK requirements and implementations;
- instrumentation libraries and zero-code instrumentation ecosystems;
- semantic conventions;
- context propagation conventions and implementations;
- a protocol, OTLP, for telemetry transport;
- the OpenTelemetry Collector for receiving, processing, and exporting telemetry;
- an ecosystem for traces, metrics, logs, and evolving signals such as profiles.

OpenTelemetry is not:

- a telemetry database;
- a dashboard product;
- a tracing storage backend;
- a log index;
- a PromQL engine;
- a guarantee of lossless end-to-end telemetry delivery;
- a guarantee that every language implements every specification feature at the same maturity;
- a guarantee that every backend interprets every signal identically;
- a substitute for a deliberate cardinality, sampling, privacy, and retention policy.

A useful rule is:

> OpenTelemetry standardizes how telemetry is described, produced, correlated, moved, and processed. Your backend still decides how that telemetry is stored and queried.

---

# Project architecture

The OpenTelemetry ecosystem contains several layers that should not be conflated.

## Specification

The specification defines cross-language expectations for:

- APIs;
- SDK behavior;
- traces;
- metrics;
- logs;
- resources;
- baggage and context;
- propagation;
- configuration;
- exporters;
- OTLP;
- semantic conventions.

A language implementation follows the specification, but language-specific support can differ by feature maturity and implementation timing.

## API

The API is the instrumentation-facing abstraction.

Application and library code can use API concepts such as:

- `Tracer` / spans;
- `Meter` / metric instruments;
- logger/logging bridges where supported;
- context and baggage.

Libraries should normally depend on the API rather than force a particular SDK implementation on users.

That enables an application to decide whether and how telemetry is recorded and exported.

## SDK

The SDK provides the operational implementation behind the API.

SDK responsibilities can include:

- provider configuration;
- sampling;
- span processors;
- metric aggregation;
- readers;
- log processors;
- resource association;
- exporters;
- batching;
- shutdown/flush behavior.

Without an SDK or equivalent recording implementation, API instrumentation can remain non-recording/no-op instead of forcing telemetry behavior on every consumer of an instrumented library.

## Instrumentation libraries

Instrumentation libraries add telemetry around common frameworks and libraries such as:

- HTTP servers and clients;
- database libraries;
- RPC frameworks;
- messaging systems;
- runtime libraries.

A well-designed instrumentation library follows semantic conventions so the same kind of operation produces consistent telemetry across applications.

## Zero-code instrumentation

Many language ecosystems offer automatic or zero-code instrumentation mechanisms.

Depending on language/runtime, these may use:

- agents;
- runtime hooks;
- bytecode instrumentation;
- monkey patching;
- preload mechanisms;
- environment-based injection.

Zero-code instrumentation is excellent for broad baseline coverage. Manual instrumentation is still valuable for business operations and application-specific boundaries that an automatic agent cannot infer.

## Collector

The Collector is a vendor-neutral telemetry proxy and processing service.

It receives, processes, and exports signals without being the final observability backend.

---

# The core telemetry identity model

Three concepts answer three different questions.

## Resource

A Resource answers:

> What entity produced this telemetry?

Examples of resource attributes include:

- `service.name`;
- service namespace/version;
- process information;
- host information;
- container information;
- Kubernetes Pod/namespace/deployment information;
- cloud provider/region information.

Resource attributes describe the producer, not one individual operation.

Conceptually:

```text
Resource
  service.name = checkout
  deployment.environment.name = production
  k8s.namespace.name = shop
  cloud.region = region-a
        |
        +--> spans
        +--> metrics
        +--> logs
```

Set `service.name` deliberately. Falling back to an unknown/default service identity makes cross-service observability much harder.

## Instrumentation scope

An Instrumentation Scope answers:

> Which logical instrumentation unit produced this telemetry?

A scope can represent:

- an instrumentation library;
- a package;
- a module;
- a framework integration;
- an application component.

It is identified by a name and may include version, schema URL, and attributes.

This makes it possible to distinguish telemetry generated by, for example, an HTTP framework instrumentation package from custom checkout-service instrumentation.

## Signal-specific attributes

Attributes on a span, metric data point, or log record answer:

> What dimensions describe this particular operation or measurement?

Do not put entity-wide identity into every event manually when it belongs in the Resource.

Do not put high-cardinality per-request identity into metrics merely because attributes are technically allowed.

---

# Semantic conventions

Semantic conventions define shared names and meanings for common telemetry concepts.

Examples include conventions for:

- HTTP;
- RPC;
- databases;
- messaging;
- cloud resources;
- Kubernetes;
- processes and runtimes;
- service identity;
- errors and exceptions.

The value is interoperability.

Instead of every team inventing:

```text
http.status
status_code
responseCode
httpCode
```

semantic conventions define a common vocabulary that instrumentation and backends can understand consistently.

## Stability matters

Not every semantic convention has the same maturity.

A production migration should distinguish:

- stable conventions;
- development conventions;
- deprecated conventions;
- transition/migration guidance.

Do not assume a convention copied from an old blog post is current.

## Schema evolution

Instrumentation may identify the semantic-convention schema it emits. This helps consumers understand which semantic versioning/evolution rules apply.

Where backends or processors perform schema translation, test transformations before changing conventions across a large fleet.

---

# Context and propagation

Distributed tracing requires causal context to cross process and network boundaries.

A simplified request flow is:

```text
client span
   |
   | inject trace context
   v
HTTP request headers
   |
   | extract context
   v
server span
   |
   | inject
   v
RPC / queue / downstream request
```

Without propagation, each service may generate valid local spans that cannot be assembled into one distributed trace.

## Context

Context is the in-process container for correlation state.

It commonly carries the active span/trace context and can also carry baggage.

Correct context management is especially important in asynchronous systems where execution jumps between threads, tasks, callbacks, coroutines, or queues.

## Propagators

Propagators inject context into a carrier and extract it on the receiving side.

Carriers can include:

- HTTP headers;
- message metadata;
- RPC metadata;
- other protocol-specific key-value fields.

W3C Trace Context is a common cross-vendor trace propagation format in OpenTelemetry ecosystems.

## Trust boundary

Incoming trace context is external input.

At trust boundaries, consider:

- whether arbitrary external trace IDs should be accepted;
- whether baggage should be filtered;
- whether internal context should be propagated to third parties;
- header size limits;
- malicious or malformed propagation data.

Context propagation is observability plumbing, but it is still network input.

---

# Baggage

Baggage is a propagated key-value store associated with context.

It is useful when contextual information must be available downstream without changing every function signature.

But baggage is **not automatically a span attribute, metric attribute, or log field**. Instrumentation must explicitly read baggage and record it when appropriate.

## Baggage security

Baggage may cross many service boundaries and may appear in network headers.

Never put secrets or sensitive personal data into baggage casually.

Avoid:

- passwords;
- API keys;
- session tokens;
- sensitive customer data;
- regulated identifiers.

Also remember that incoming baggage is not inherently trustworthy. A client may forge it.

---

# Traces

A trace represents a distributed operation as related spans.

```text
trace
  |
  +-- server span: POST /checkout
        |
        +-- DB span: SELECT cart
        |
        +-- client span: payment RPC
        |      |
        |      +-- server span: charge
        |
        +-- producer span: publish order
```

## Span

A span represents one operation.

A span can include:

- name;
- trace/span context;
- parent context;
- span kind;
- start and end timestamps;
- attributes;
- events;
- links;
- status.

## Span naming

Span names should describe a useful class of operations rather than contain unbounded identifiers.

Good:

```text
GET /users/{id}
checkout.submit
payment.authorize
```

Dangerous:

```text
GET /users/948561028
```

The latter can create high-cardinality operation names and make aggregation difficult.

## Span kind

Span kind communicates the role of the operation, such as server, client, producer, consumer, or internal behavior.

Correct kind helps backends understand service boundaries and latency relationships.

## Events

Span events represent notable timestamped occurrences during a span.

Examples:

- exception recorded;
- retry attempt;
- state transition.

Do not create a child span for every tiny event if the event does not represent meaningful duration or causal structure.

## Links

Links associate a span with other span contexts without claiming a strict parent-child relationship.

They are useful for patterns such as:

- batch processing;
- fan-in/fan-out;
- message processing where one operation relates to several prior contexts.

---

# Trace sampling

Collecting every trace may be too expensive at scale.

Sampling determines which trace data is recorded/exported.

## Head sampling

Head sampling makes the decision near the beginning of a trace.

Advantages:

- low overhead;
- simple;
- decision is available early.

Trade-off:

- the sampler cannot know the final latency, error, or downstream outcome when deciding.

A rare important error may be dropped if the initial decision was “do not sample.”

## Tail sampling

Tail sampling waits until enough of the trace is available to make a decision based on completed behavior.

It can prioritize traces with:

- errors;
- high latency;
- particular attributes;
- unusual routes;
- policy matches.

Trade-offs:

- buffering cost;
- stateful routing requirements;
- more memory;
- delayed decision;
- more Collector topology complexity.

Tail sampling is normally a Collector/backend pipeline concern rather than a magic SDK flag.

## Sampling and propagation

Sampling decisions are propagated as part of trace context. Inconsistent sampling design across services can produce incomplete traces or unexpected cost.

Design sampling as an end-to-end policy.

---

# Metrics

OpenTelemetry metrics represent measurements through instruments, aggregation, temporality, attributes, and export data models.

Important concepts include:

- synchronous and asynchronous instruments;
- counters and up/down counters;
- gauges;
- histograms;
- aggregation;
- temporality;
- exemplars;
- Views.

## Counter

Represents a monotonic cumulative measurement.

Examples:

- requests completed;
- bytes sent;
- jobs processed.

## UpDownCounter

Represents a quantity that can increase and decrease through additive changes.

Examples can include current logical work in progress when change events are directly observed.

## Gauge

Represents a current observed value.

Examples:

- temperature;
- current queue length;
- latest memory value.

## Histogram

Aggregates a distribution of measurements such as:

- request duration;
- payload size;
- queue wait time.

OTLP can transport histogram data with counts, sums, boundaries/buckets where applicable, exemplars, and temporal information.

## Temporality

Metric streams may use cumulative or delta temporality depending on instrument/backend/pipeline support.

This distinction matters during conversion.

A backend expecting cumulative counters cannot simply reinterpret arbitrary delta streams without state, and cumulative-to-delta conversion must handle resets and process lifecycle correctly.

## Views

Views let SDKs influence aggregation and stream configuration.

They can be used to:

- change aggregation;
- rename or reshape streams;
- restrict attributes;
- tune histogram behavior.

Views are powerful cardinality controls. Use them deliberately rather than exporting every possible attribute.

---

# Metrics cardinality

OpenTelemetry does not eliminate metric cardinality economics.

Every unique set of metric attributes can become a distinct stream/series in downstream systems.

Dangerous attributes include:

- user ID;
- request ID;
- trace ID as a regular metric dimension;
- raw URL path with IDs;
- UUIDs;
- timestamps;
- arbitrary exception messages.

A semantic convention may define an attribute, but that does not mean every metric should carry it.

Ask:

1. Is this dimension bounded?
2. Will operators aggregate/filter by it?
3. What happens at 10x scale?
4. Would the detail be better represented in traces or logs?

---

# Exemplars

Exemplars associate individual metric observations with contextual information, commonly trace/span identity.

They provide a bridge such as:

```text
latency histogram spike
        |
        v
exemplar trace ID
        |
        v
specific distributed trace
```

Exemplars are not a replacement for metric aggregation or trace storage. They are sparse correlation points.

---

# Logs

OpenTelemetry logging support is designed to correlate log records with the rest of telemetry while interoperating with existing logging ecosystems.

A LogRecord can carry information such as:

- timestamp;
- observed timestamp;
- severity;
- body;
- attributes;
- resource;
- instrumentation scope;
- trace ID;
- span ID.

## Trace correlation

When a log record is emitted inside an active trace context, OpenTelemetry-compatible logging pipelines can associate trace/span identifiers with the record.

This enables workflows such as:

```text
trace -> related logs
log -> related trace
```

Correlation is valuable, but do not turn trace IDs into high-cardinality metric labels merely to reproduce the same relationship.

## Existing logging libraries

OpenTelemetry generally works with language logging ecosystems rather than requiring every application to abandon its normal logging API immediately.

Bridges/appenders/exporters may convert existing logs into the OpenTelemetry data model.

Validate support for the exact language implementation because logging maturity differs across ecosystems.

---

# Profiles and evolving signals

OpenTelemetry is expanding beyond traces, metrics, and logs.

Profiles are an evolving signal area and OTLP profile support is not necessarily at the same stability level as trace, metric, and log transport.

Do not design a production compatibility contract from a generic “OpenTelemetry supports profiles” statement alone.

Check:

- specification maturity;
- language SDK support;
- Collector component support;
- backend support;
- protocol version.

---

# OTLP

OTLP is the OpenTelemetry Protocol used to transport telemetry between producers, Collectors, and backends.

The protocol defines:

- telemetry message schema;
- export request/response behavior;
- Protobuf representation;
- gRPC transport;
- HTTP transport;
- success, partial-success, retry, and throttling semantics.

Current trace, metric, and log OTLP signal transport is stable; evolving signals can have different maturity.

## OTLP/gRPC

OTLP/gRPC uses gRPC and Protobuf.

The standard default port is commonly:

```text
4317
```

## OTLP/HTTP

OTLP/HTTP can use Protobuf payloads over HTTP, with standard signal paths such as:

```text
/v1/traces
/v1/metrics
/v1/logs
```

The standard default port is commonly:

```text
4318
```

Treat these as protocol defaults, not a network-security recommendation. Production endpoints should be configured explicitly.

## Compression and retry

OTLP defines transport behavior around errors, throttling, retryable failures, and compression support.

But OTLP does **not** provide a magical end-to-end exactly-once guarantee across every hop.

A pipeline may contain:

```text
SDK -> Agent Collector -> Gateway Collector -> queue -> backend
```

Each hop has its own buffering and failure semantics.

---

# OTLP delivery semantics

A critical operational fact is:

> Successful delivery from one client to one server does not prove durable end-to-end persistence in the final backend.

Possible loss points include:

- SDK process crash before export;
- local queue overflow;
- Collector crash with memory-only queue;
- network partition;
- retry timeout;
- exporter queue overflow;
- persistent queue disk failure;
- message-queue failure;
- backend rejection;
- malformed telemetry;
- sampling or filtering policy.

If telemetry is mission-critical evidence, document every queue and acknowledgement boundary.

---

# SDK pipeline

A simplified trace SDK pipeline looks like:

```text
instrumentation
     |
     v
Tracer API
     |
     v
sampler
     |
     v
recording Span
     |
     v
SpanProcessor
     |
     v
batch / export
     |
     v
OTLP exporter
```

Metrics and logs have signal-specific processing pipelines, but the same principle applies: API calls are not identical to exported backend records.

Between generation and export, telemetry may be:

- aggregated;
- sampled;
- batched;
- filtered;
- transformed;
- dropped;
- retried.

---

# Batch processing

Batching reduces export overhead by sending telemetry in groups instead of making a network request for every individual item.

This improves throughput but creates buffering semantics.

Trade-offs include:

- memory use;
- delay before export;
- more telemetry at risk if a process terminates without flushing;
- batch-size sensitivity;
- backend request-size limits.

Applications should allow SDKs to shut down/flush cleanly where practical, especially for short-lived workloads.

---

# OpenTelemetry Collector

The Collector is a programmable telemetry pipeline.

Its core component model is:

```text
receiver
   |
   v
processor(s)
   |
   v
exporter
```

Additional concepts include:

- connectors;
- extensions;
- service pipelines;
- internal telemetry.

## Receivers

Receivers accept telemetry from sources.

Examples can include:

- OTLP;
- Prometheus scraping;
- existing trace protocols;
- log inputs;
- vendor-specific formats.

Defining a receiver in configuration does not necessarily enable it. It must be referenced by an active service pipeline.

## Processors

Processors transform or control telemetry between receive and export.

Common responsibilities include:

- batching;
- memory limiting;
- filtering;
- attribute transformation;
- resource enrichment;
- sampling;
- Kubernetes metadata enrichment.

Processor order matters.

```text
filter -> transform
```

can produce different results from:

```text
transform -> filter
```

## Exporters

Exporters send telemetry to downstream destinations.

Examples include:

- OTLP backends;
- Prometheus-compatible systems;
- cloud/vendor endpoints;
- debugging output;
- queues.

Network exporters should be designed with queue/retry behavior in mind.

## Connectors

A connector acts as an exporter from one pipeline and a receiver into another.

This enables cross-pipeline workflows such as:

```text
traces
  |
  v
span-metrics connector
  |
  v
metrics pipeline
```

Connectors can derive, route, count, or otherwise bridge telemetry across pipelines depending on component behavior.

## Extensions

Extensions provide capabilities outside direct telemetry data flow, such as:

- health endpoints;
- profiling/diagnostics;
- authentication helpers;
- service discovery;
- storage support.

---

# Collector configuration model

A simplified Collector configuration is:

```yaml
receivers:
  otlp:
    protocols:
      grpc: {}
      http: {}

processors:
  memory_limiter: {}
  batch: {}

exporters:
  otlp/backend:
    endpoint: telemetry.example.internal:4317

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/backend]
```

The exact component options are version-sensitive.

The important structural rule is:

> configuring a component and enabling it in a pipeline are separate actions.

A receiver that exists in YAML but is not referenced by a pipeline does not process that pipeline's data.

---

# Collector deployment patterns

## Agent pattern

A Collector runs near each workload or node.

```text
applications
    |
    v
local Agent Collector
    |
    v
backend / gateway
```

Benefits:

- low-latency local endpoint;
- host/node metadata access;
- local processing;
- reduced application knowledge of backend credentials.

Trade-offs:

- many Collector instances;
- resource overhead per node/workload;
- configuration distribution complexity.

## Gateway pattern

A central pool receives telemetry from many applications/agents.

```text
app/agents
   \ | /
    \|/
Gateway Collectors
      |
      v
backends
```

Benefits:

- centralized credentials;
- centralized routing and transformation;
- easier tail-sampling topology;
- easier backend isolation.

Trade-offs:

- shared failure domain;
- network hop;
- scaling/load-balancing requirements.

## Agent + Gateway

A common production architecture combines both:

```text
application
   |
local agent
   |
regional/shared gateway
   |
backend(s)
```

Use architecture requirements—not habit—to decide whether both tiers are necessary.

---

# Collector resiliency

Collector resilience centers on buffering and retry behavior when a downstream endpoint is unavailable.

## Sending queue

A sending queue buffers telemetry before export.

If the backend slows down, queue depth rises.

Monitor queue capacity and utilization rather than waiting until the queue is full.

## Retry

Retry mechanisms can handle transient endpoint failures with backoff.

Retry duration is finite unless configured otherwise. A backend outage longer than the retry/queue capacity can still result in data loss.

## Persistent queue / WAL

Critical Collector exporters can use persistent storage so queued telemetry survives Collector process restart.

This improves durability against process failure but does not protect against:

- disk loss;
- full disk;
- corrupted storage;
- backend outage longer than available capacity;
- misconfiguration.

## External message queue

For stronger decoupling, a durable message queue can sit between Collector tiers or before a backend.

This increases operational complexity and should be justified by durability/decoupling requirements.

---

# Backpressure and overload

Telemetry pipelines can fail because they receive data faster than they can export it.

A simplified capacity equation is:

```text
ingress rate > sustained egress rate
        |
        v
queue growth
        |
        v
memory/disk pressure
        |
        v
refusal or drop
```

Scaling the Collector helps only if the downstream backend can accept the additional traffic.

If the backend is saturated, adding more Collector workers may accelerate pressure rather than solve it.

First identify the bottleneck.

---

# Collector internal telemetry

The Collector emits its own operational telemetry.

Monitor at least:

- accepted telemetry;
- refused telemetry;
- exporter send failures;
- queue size/capacity;
- enqueue failures;
- process memory/CPU;
- receiver/exporter latency where available;
- component-specific errors.

A telemetry pipeline that is not monitored is itself an observability blind spot.

---

# Tail sampling architecture

Tail sampling needs trace-wide or sufficiently complete trace information.

A naive horizontally scaled Collector fleet can send spans from one trace to different sampling instances:

```text
span A -> sampler 1
span B -> sampler 2
span C -> sampler 3
```

No sampler sees the whole trace.

Production tail-sampling architectures therefore need consistent routing or another mechanism that co-locates related trace data before the decision.

This is a distributed-systems problem, not merely a configuration toggle.

---

# Auto-instrumentation versus manual instrumentation

## Auto-instrumentation excels at edges

It can often capture:

- inbound HTTP;
- outbound HTTP;
- database calls;
- RPC;
- messaging libraries;
- runtime metrics.

## Manual instrumentation adds domain meaning

Manual spans/metrics can capture:

- checkout validation;
- inventory reservation;
- fraud decision;
- model inference step;
- batch stage;
- business queue wait.

The strongest systems usually combine both.

Avoid duplicate instrumentation where an automatic agent and manual library both instrument the same operation.

---

# Instrumentation library design

Libraries that publish native OpenTelemetry instrumentation should generally depend on the API, not force an SDK.

This preserves application control over:

- sampling;
- exporters;
- backend choice;
- resource configuration;
- batching;
- shutdown.

A reusable library should not secretly start its own unrelated telemetry pipeline unless that behavior is explicitly part of its contract.

---

# Error recording

Trace status and exception events are related but distinct concepts.

A span can record exception information while status communicates whether the operation should be considered erroneous according to semantic rules.

Do not mark every handled exception as a failed operation automatically.

For example, an internal retry may throw an exception but ultimately succeed. The correct telemetry should reflect the operation's semantic outcome, not simply whether an exception object ever existed.

---

# Service identity

`service.name` is foundational for usable telemetry.

A practical resource identity often includes:

```text
service.name
service.namespace
service.version
deployment.environment.name
```

plus runtime-specific resource attributes.

Do not encode deployment instance identity into `service.name`.

Bad:

```text
checkout-pod-a8291
```

Better:

```text
service.name = checkout
k8s.pod.name = checkout-a8291
```

Stable service identity and ephemeral instance identity serve different query purposes.

---

# Kubernetes integration

OpenTelemetry commonly runs in Kubernetes using:

- SDKs inside workloads;
- auto-instrumentation;
- node/DaemonSet Collectors;
- sidecars;
- gateway Collector Deployments;
- OpenTelemetry Operator-managed resources;
- Kubernetes metadata processors/receivers.

A common path is:

```text
Pod SDK
  |
  v
OTLP
  |
  v
node Collector
  |
  +--> enrich with Kubernetes resource metadata
  |
  v
gateway Collector
  |
  v
backend
```

Kubernetes labels can be extremely high cardinality. Do not copy every Pod annotation/label into telemetry automatically.

Enrichment policy should be explicit.

---

# Prometheus interoperability

OpenTelemetry and Prometheus overlap in metrics but have different native models and histories.

Interoperability can happen through:

- Prometheus receivers scraping metrics into a Collector;
- OpenTelemetry instrumentation exporting metrics toward Prometheus-compatible systems;
- remote-write compatible pipelines;
- Prometheus exposition compatibility;
- backend OTLP ingestion.

## Important conversion concerns

When converting between OpenTelemetry and Prometheus models, pay attention to:

- metric names;
- units;
- resource attributes;
- labels/attributes;
- counters and resets;
- delta versus cumulative temporality;
- histograms;
- exemplars;
- target identity;
- metadata.

“Both support metrics” does not mean conversion is semantically trivial.

---

# Backend portability

A vendor-neutral SDK does not make every backend interchangeable.

Backends can differ in:

- query language;
- storage retention;
- aggregation behavior;
- histogram support;
- attribute limits;
- event/log capabilities;
- trace search;
- service graph generation;
- sampling architecture;
- cardinality pricing/limits.

OpenTelemetry reduces instrumentation lock-in. It does not eliminate backend architecture decisions.

---

# Dual export and migration

Collector pipelines make it possible to export to multiple backends during migration.

```text
OTLP receiver
      |
      v
   processors
    /      \
   v        v
backend A backend B
```

Useful for:

- migration validation;
- disaster testing;
- backend evaluation;
- separate security/compliance sinks.

Trade-off:

- roughly duplicated egress and downstream ingest cost;
- differences in accepted semantics;
- one slow exporter may require separate buffering/failure isolation.

Do not run dual export indefinitely without knowing the cost.

---

# Security and privacy

Telemetry often contains more sensitive data than teams expect.

Potentially sensitive fields include:

- HTTP URLs;
- database statements;
- user identifiers;
- headers;
- query parameters;
- message payload metadata;
- exception messages;
- log bodies;
- baggage;
- cloud/Kubernetes metadata.

## Minimize at source

The safest sensitive attribute is often the attribute never collected.

Prefer allowlists and semantic instrumentation over “collect everything, redact later.”

## Collector redaction/filtering

Collectors can filter or transform attributes before export.

This is useful as defense in depth, but downstream privacy should not rely entirely on one processor remaining perfectly configured forever.

## OTLP endpoint security

Protect OTLP receivers with appropriate:

- network policy;
- TLS;
- authentication where needed;
- rate limits;
- tenant boundaries;
- payload limits.

An exposed telemetry receiver can become a data-injection and resource-exhaustion surface.

## Telemetry poisoning

If untrusted clients can submit telemetry, they may generate:

- forged service names;
- fake errors;
- massive attribute cardinality;
- misleading traces;
- oversized payloads.

Observability systems need trust boundaries just like business APIs.

---

# Performance overhead

Instrumentation overhead can come from:

- span creation;
- attribute construction;
- context propagation;
- stack/exception capture;
- metric aggregation;
- logging bridges;
- batching;
- serialization;
- export/network I/O.

## Avoid expensive work for non-recording spans

Where language APIs expose recording/sampling state, avoid computing expensive attributes that will never be recorded.

For example, serializing a huge object just to attach it to a dropped span wastes application CPU even if the SDK later discards it.

## Attribute limits

SDK/backend limits exist partly to protect resource use.

Treat truncation/dropped-attribute telemetry as an operational signal that instrumentation design may need review.

---

# Failure modes

## No telemetry appears in backend

Trace the pipeline stage by stage:

```text
instrumentation
 -> SDK provider
 -> processor/reader
 -> exporter
 -> network
 -> Collector receiver
 -> processor chain
 -> Collector exporter
 -> backend ingest
 -> backend query
```

Do not assume the last visible component is the failing one.

## Trace is broken across services

Check:

- propagation injection;
- extraction;
- supported propagator format;
- proxy/header stripping;
- async context loss;
- message metadata propagation;
- trust-boundary sanitization.

## Service appears as `unknown_service`

Resource/service identity was not configured correctly.

Set `service.name` explicitly through supported SDK configuration or resource configuration.

## Duplicate spans

Likely causes:

- auto-instrumentation plus manual instrumentation of the same library boundary;
- two agents;
- framework and generic HTTP instrumentation overlap;
- Collector duplication/routing;
- backend ingest from multiple exporters.

## Metrics explode in cardinality

Inspect attributes introduced by:

- manual instrumentation;
- semantic conventions;
- resource-to-metric conversion;
- Kubernetes enrichment;
- logs-to-metrics/span-to-metrics connectors;
- unbounded route/user/request fields.

## Collector memory rises continuously

Check:

- exporter queue growth;
- backend slowness;
- batch sizes;
- tail-sampling state;
- high-cardinality processors;
- oversized telemetry;
- insufficient memory limiter/sizing.

## Collector drops data

Look for:

- refused telemetry;
- full sending queues;
- exporter failures;
- retry expiration;
- memory-limiter pressure;
- disk/WAL exhaustion;
- backend throttling.

## Tail sampling misses expected traces

Check whether all spans of a trace reach the same sampling decision point and whether the decision wait/policy captures late spans.

## Metrics differ after backend migration

Investigate semantic conversion:

- temporality;
- aggregation;
- histogram representation;
- resource mapping;
- attribute filtering;
- unit/name conversion.

A transport-successful migration can still be analytically incorrect.

---

# Debugging workflow

## 1. Prove local instrumentation exists

Use a development/debug exporter or language-specific diagnostic tooling.

Confirm that the expected span/metric/log record is created before debugging the network.

## 2. Verify Resource identity

Inspect:

- `service.name`;
- environment;
- version;
- host/container/Kubernetes attributes.

Incorrect Resource identity can make valid telemetry appear “missing” because queries filter on the wrong service.

## 3. Verify exporter configuration

Check:

- OTLP protocol;
- endpoint;
- TLS mode;
- headers/authentication;
- signal-specific exporter settings.

## 4. Verify Collector receive path

Use Collector internal telemetry and safe debug tooling to confirm the receiver accepts records.

## 5. Verify processing

Inspect filter, transform, sampling, and routing processors.

A processor may intentionally drop the telemetry.

## 6. Verify export

Check queue size, failures, retries, throttling, and backend responses.

## 7. Query backend directly

Once export is confirmed, verify backend indexing/query semantics.

At that point the problem may no longer be OpenTelemetry.

---

# Collector debugging checklist

When a Collector behaves unexpectedly:

- confirm component exists in configuration;
- confirm component is enabled in the expected pipeline;
- confirm signal type matches the pipeline;
- verify receiver bind address;
- verify processor order;
- verify exporter endpoint/auth/TLS;
- inspect Collector logs;
- inspect internal telemetry;
- inspect queue capacity and failures;
- check backend throttling;
- check memory limiter and process memory;
- validate any persistent-storage path and disk capacity.

---

# Configuration portability

OpenTelemetry defines common environment variables such as those for:

- service name;
- Resource attributes;
- propagators;
- trace sampler;
- exporters;
- OTLP endpoint/protocol/headers.

But language SDK support is not perfectly uniform.

Before standardizing an organization-wide environment-variable policy, check the compliance/support matrix for each language implementation.

A setting working in Java does not prove it is implemented identically in every other SDK.

---

# Semantic-convention migration

Semantic conventions evolve.

A safe migration pattern is:

1. identify changed/deprecated attributes;
2. verify instrumentation-library versions;
3. verify backend support;
4. update dashboards/alerts/queries;
5. run temporary compatibility mapping where needed;
6. remove legacy fields only after consumers migrate.

Avoid breaking every dashboard by changing instrumentation and query assumptions in the same uncontrolled deployment.

---

# Instrumentation governance

At organization scale, OpenTelemetry benefits from governance around:

- service naming;
- Resource identity;
- approved semantic conventions;
- custom attribute naming;
- sensitive-data policy;
- trace sampling;
- metric cardinality;
- histogram strategy;
- Collector distributions;
- exporter destinations;
- version upgrades.

Without governance, vendor-neutral telemetry can still become organization-specific chaos.

---

# Collector distributions

The OpenTelemetry Collector ecosystem has multiple distributions with different component sets.

Do not assume a receiver/processor/exporter documented in the contrib ecosystem is included in every Collector binary.

Before deploying configuration, verify that the chosen distribution contains each component.

For tightly controlled environments, building a smaller custom distribution can reduce:

- binary size;
- unused attack surface;
- dependency footprint;
- accidental component availability.

The trade-off is responsibility for build/release maintenance.

---

# Version compatibility

OpenTelemetry has several independently moving surfaces:

- specification;
- semantic conventions;
- language APIs/SDKs;
- instrumentation packages;
- Collector core;
- Collector contrib;
- OTLP schema/protocol;
- backend OTLP support.

Do not reason about “the OpenTelemetry version” as if there were one universal release number.

Compatibility reviews should identify the exact component being upgraded.

---

# Reliability design

Telemetry reliability should be matched to signal value.

Not all telemetry needs the same durability.

For example:

- high-volume debug traces may accept sampling/loss;
- security audit evidence may require a separate durable pipeline;
- SLO metrics may justify redundant collection;
- application logs may require stronger retention than transient traces.

OpenTelemetry provides pipeline mechanisms, but it does not define your business durability requirements.

---

# OpenTelemetry and SLOs

OpenTelemetry can produce and transport the metrics used for SLOs, but the SLO definition belongs to your reliability policy/backend tooling.

Make sure SLI metrics have:

- stable names;
- stable units;
- bounded attributes;
- clear numerator/denominator semantics;
- compatible temporality/aggregation;
- tested backend conversion.

An instrumentation migration should not silently redefine an SLO.

---

# Anti-patterns

## “Send everything” instrumentation

Collecting every header, query, SQL statement, stack, and object creates privacy and cost problems.

## User IDs in metric attributes

Creates high cardinality and privacy risk.

## Baggage as a secret channel

Baggage is propagated context, not a secure secret store.

## SDK-to-every-vendor direct export

Can recreate vendor coupling and put credentials/configuration into every application.

A Collector tier is often easier to govern in production.

## One giant Collector gateway with no redundancy

Creates a broad observability failure domain.

## Tail sampling without trace affinity

Produces incomplete decisions because related spans are split across samplers.

## Memory-only queues for telemetry that must survive Collector restart

Makes process restart a data-loss event.

## Converting every Resource attribute into metric labels

Can multiply time-series cardinality dramatically.

## Treating OTLP success as durable backend persistence

Each network hop has separate acknowledgement/durability semantics.

## Assuming all SDKs support the same features

Specification maturity and implementation maturity are different things.

---

# Operational checklist

Before production rollout, verify:

- `service.name` and Resource identity conventions are defined;
- semantic conventions are versioned/reviewed;
- sensitive attributes are prohibited or filtered;
- propagation across HTTP/RPC/messaging is tested;
- baggage has a security policy;
- trace sampling strategy is documented;
- metric cardinality budgets exist;
- histogram/temporality behavior is compatible with the backend;
- SDK batching and shutdown behavior are tested;
- Collector distribution contains all configured components;
- receivers are network-restricted appropriately;
- exporter TLS/authentication is configured;
- sending queues and retries are sized;
- persistent queues are used where restart durability matters;
- Collector internal telemetry is monitored;
- backend throttling and export failures alert operators;
- tail-sampling topology preserves trace affinity;
- OpenTelemetry and backend upgrades are compatibility-tested.

---

# Learning path

## Beginner

Learn:

1. Resource versus span/metric/log attributes;
2. API versus SDK;
3. traces, metrics, and logs;
4. context propagation;
5. OTLP;
6. Collector receiver/process/export model.

Practice:

- instrument one HTTP service;
- set `service.name`;
- export traces to a local Collector;
- inspect one distributed trace;
- add a custom metric;
- correlate a log with trace context.

## Intermediate

Learn:

1. semantic conventions;
2. instrumentation scopes;
3. baggage;
4. sampling;
5. metric temporality and histograms;
6. Collector processors;
7. Prometheus interoperability;
8. resource enrichment.

Practice:

- add automatic instrumentation and one manual business span;
- propagate context through a queue;
- filter a sensitive attribute in the Collector;
- convert/export metrics to a Prometheus-compatible backend;
- diagnose one deliberate propagation break.

## Advanced

Learn:

1. tail sampling;
2. Collector HA/scaling;
3. queue/WAL durability;
4. signal routing and connectors;
5. semantic-convention migrations;
6. multi-backend export;
7. custom Collector distributions;
8. telemetry governance and cost engineering.

Practice:

- build an Agent + Gateway topology;
- simulate backend outage and observe queue behavior;
- enable persistent storage and restart a Collector;
- test tail-sampling trace affinity;
- dual-export during a backend migration and compare semantic results.

---

# Relationships in OpenDevIndex

- `cloud/prometheus` — OpenTelemetry metrics interoperate with Prometheus through scraping, exposition, remote-write, OTLP ingestion, and Collector pipelines, with explicit conversion semantics required for temporality, histograms, resources, and labels.

As additional stable tracing/logging backend modules are added to OpenDevIndex, relationships should reflect real protocol or architecture integration rather than broad “observability-related” graph edges.

---

# Verification

This deep-dive was reviewed on **2026-09-06** against current upstream OpenTelemetry documentation and specifications covering project architecture, API/SDK components, signals, Resources, Instrumentation Scope, context propagation, Baggage, sampling, semantic conventions, OTLP, Collector components/configuration/resiliency, internal telemetry, and Prometheus interoperability.

The specification repository is Apache-2.0 licensed. Trace, metric, and log OTLP transport is stable in the current OTLP specification; newer signal areas such as profiles can have different maturity and must be checked independently.

The module deliberately avoids assuming uniform feature support across every language SDK, Collector distribution, or observability backend.

---

# Maintenance

Update this module when any of the following materially changes:

- API/SDK stability or component model;
- signal maturity;
- semantic conventions;
- OTLP transport or schema;
- propagation requirements;
- metric data model/temporality;
- Collector component architecture;
- Collector queue/resiliency guidance;
- configuration environment variables;
- Prometheus interoperability;
- security/privacy guidance.

Preserve the stable OpenDevIndex address `cloud/opentelemetry`. Deep-dive content should remain hand-curated and source-backed rather than being replaced by a generic catalog renderer.
