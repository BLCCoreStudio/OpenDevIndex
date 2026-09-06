# Grafana

> Open-source observability visualization and alerting platform that connects to external data sources, executes their query languages, transforms results, renders dashboards and Explore views, and manages alert evaluation and notification workflows.

Grafana is easiest to understand as a **query, visualization, and operational interaction layer over other systems**.

It usually does not own the raw telemetry shown on a dashboard. Prometheus owns metrics, a log backend owns logs, a tracing backend owns traces, and databases own their queryable data. Grafana connects to those systems, issues queries, transforms results, renders visualizations, stores dashboard/configuration metadata, and can evaluate alerts.

The shortest useful mental model is:

```text
metrics / logs / traces / SQL / APIs
             |
             v
        data-source plugin
             |
             v
        query execution
             |
             v
    frames / query results
             |
       transformations
             |
             v
 panels / Explore / alert evaluation
             |
             v
 dashboard / notification workflow
```

This boundary is critical during incidents. A blank panel can be caused by Grafana, the query, the data-source plugin, credentials, networking, or the upstream data system. “Grafana is broken” is only one possibility.

---

# Why Grafana matters

Observability data is fragmented by design. Metrics, logs, traces, profiles, cloud APIs, SQL databases, and application-specific stores have different data models and query languages.

Grafana provides a common operational surface without forcing every source into one storage engine.

That enables teams to:

- build dashboards from multiple systems;
- explore data interactively without first creating a dashboard;
- correlate metrics with logs and traces;
- parameterize dashboards with variables;
- transform query results for presentation;
- share links and operational context;
- evaluate alert rules over supported data sources;
- route alert notifications through policy trees and contact points;
- provision data sources and dashboards as code;
- extend the platform through plugins.

The trade-off is that Grafana becomes part of the operational control plane. Poor queries, weak permissions, unsafe plugins, uncontrolled variables, or broken provisioning can affect many teams at once.

---

# What Grafana is — and is not

Grafana is:

- a web application and API for observability workflows;
- a data-source integration platform;
- a dashboard and panel renderer;
- an exploratory query interface;
- an alert-rule evaluation and notification-management platform;
- a persistent store for Grafana configuration metadata;
- a plugin host.

Grafana is not automatically:

- a metrics database;
- a log database;
- a tracing backend;
- a replacement for Prometheus;
- a source of truth for application telemetry;
- a guarantee that a panel query is cheap;
- a guarantee that two panels use identical semantics;
- a secure multi-tenant boundary unless authentication, permissions, folders, data sources, and deployment topology are designed accordingly.

A common architecture is:

```text
applications
   |
   +---- metrics ---> Prometheus -----+
   +---- logs ------> log backend ----+----> Grafana
   +---- traces ----> trace backend --+       |
                                             +--> dashboards
                                             +--> Explore
                                             +--> alerts
```

---

# Core architecture

## Grafana server

A self-hosted Grafana server is responsible for concerns such as:

- HTTP/API handling;
- authentication and sessions;
- dashboard and folder management;
- data-source configuration;
- query orchestration through plugins;
- alert evaluation where configured;
- notification configuration;
- plugin loading;
- provisioning;
- persistence of Grafana metadata.

It does not need to contain the telemetry itself.

## Grafana database

Grafana stores its own persistent application state in a relational database.

Examples include:

- users and organizations;
- dashboards and folders;
- data-source definitions;
- alerting configuration;
- preferences;
- service-account and other application metadata;
- plugin/configuration state where applicable.

A fresh small installation commonly uses SQLite. Production and high-availability deployments generally use an external supported relational database such as PostgreSQL or MySQL.

Do not confuse:

```text
Grafana database
```

with:

```text
Grafana data sources
```

The first stores Grafana's own control/configuration state. The second are external systems Grafana queries.

## Data-source plugins

A data-source plugin defines how Grafana communicates with a particular backend and maps backend capabilities into Grafana query, alerting, annotation, variable, and visualization workflows.

Examples include systems using:

- PromQL;
- SQL;
- log query languages;
- tracing APIs;
- cloud monitoring APIs;
- JSON/HTTP or vendor-specific protocols.

A data-source plugin is not merely a connector string. It participates in query construction, authentication, transport, response parsing, and sometimes backend-specific UX.

## Panel and visualization plugins

Panels convert query results into visual representations such as:

- time-series graphs;
- tables;
- stat values;
- gauges;
- heatmaps;
- state timelines;
- logs;
- node graphs;
- geomaps.

A panel may execute multiple queries and then apply transformations before rendering.

## App plugins

App plugins can bundle broader functionality, including data sources, panels, pages, and navigation.

Plugins expand Grafana's capability and its trust boundary. Treat plugin installation as software supply-chain management.

---

# The data path

A useful debugging model separates six stages.

## Stage 1 — dashboard or Explore defines a query

The query contains data-source-specific logic.

For Prometheus, that is commonly PromQL. For SQL data sources, it may be SQL. For logs or traces, the query model differs again.

Grafana does not make these languages equivalent.

## Stage 2 — variables and macros expand

Dashboard variables, time-range macros, interval calculations, template substitutions, and panel repetition can change the final query.

What appears in the editor is not always exactly what reaches the backend.

## Stage 3 — data-source plugin executes

The plugin sends the request using configured URL, authentication, headers, TLS settings, and backend-specific behavior.

## Stage 4 — backend evaluates

The external system performs the actual query.

A slow PromQL expression is primarily Prometheus/query-backend work even though Grafana initiated it.

## Stage 5 — Grafana receives results and transforms them

Grafana can reshape, join, filter, calculate, rename, reduce, or organize returned data.

## Stage 6 — visualization renders

Panel configuration maps the result into a visual model with units, thresholds, overrides, legends, links, and display options.

This gives a practical failure tree:

```text
no useful panel
   |
   +-- wrong variable expansion?
   +-- query invalid?
   +-- credentials/network failure?
   +-- backend returned no data?
   +-- transformation removed/mis-shaped data?
   +-- visualization options misleading?
```

---

# Data sources

A data source is a configured connection to an external system.

Important configuration often includes:

- endpoint URL;
- authentication mode;
- credentials or tokens;
- TLS settings;
- custom headers;
- backend-specific options;
- query timeout/cache behavior where supported.

## Security boundary

Data-source credentials are high-value secrets.

If a data source can query production telemetry across every team, anyone who can use that data source may gain visibility beyond their application unless the backend itself enforces tenancy or the Grafana permission model constrains access appropriately.

Grafana permissions cannot magically make an upstream credential less privileged.

A robust model asks:

1. What can the Grafana user do?
2. Which data source can they access?
3. What can that data-source credential do at the backend?
4. Does the backend independently enforce tenant/query scope?

## Server-side versus browser trust

Modern Grafana commonly performs data-source communication through its backend/plugin infrastructure, which helps keep credentials off the browser. Still, plugin and data-source behavior varies, so review the exact plugin architecture for sensitive systems rather than assuming every request follows the same path.

---

# Prometheus integration

Prometheus is one of Grafana's most important data sources.

The normal boundary is:

```text
Prometheus
  - discovers targets
  - scrapes metrics
  - stores time series
  - evaluates PromQL

Grafana
  - constructs/sends PromQL
  - receives query results
  - transforms/displays them
  - may evaluate Grafana-managed alerts using the data source
```

Grafana's Prometheus data source also works with systems implementing compatible Prometheus query APIs.

## Query editor

The Prometheus query editor helps build PromQL and select metrics/labels, but the semantics remain PromQL semantics.

A query that is expensive in the Prometheus expression browser will generally remain expensive when run from Grafana.

## Exemplars

Prometheus-compatible backends can expose exemplars that connect metric observations to trace identifiers. Grafana can use these to navigate from a metric spike toward a related trace when the data-source and trace integrations are configured correctly.

That does not mean every metric point has a trace. Exemplars are sparse correlation hints.

---

# Dashboards

A dashboard is a collection of panels and dashboard-level configuration.

A production dashboard should be treated as executable operational logic rather than decorative JSON.

It contains:

- queries;
- variables;
- time-range assumptions;
- transformations;
- thresholds;
- panel repetition;
- links;
- annotations;
- units and visualization semantics.

Changing any of these can alter an operator's interpretation during an incident.

## Dashboard design hierarchy

A useful operational dashboard often answers questions in this order:

1. Is the service meeting user-facing objectives?
2. Where is impact concentrated?
3. Is capacity/saturation involved?
4. Which dependency changed?
5. Where can I drill into lower-level evidence?

Dashboards that begin with hundreds of infrastructure metrics can make diagnosis slower.

## Stable semantics

A dashboard should not silently redefine the meaning of a business or SRE metric.

If a “success rate” panel uses a different denominator than the alert with the same name, incidents become confusing.

Prefer shared recording rules or well-documented query definitions for critical calculations.

---

# Panels

A panel contains one or more queries plus visualization configuration.

Important concepts include:

- data source;
- query/ref ID;
- transformations;
- field options;
- overrides;
- units;
- thresholds;
- links;
- visualization type.

## Multiple queries

A panel can combine queries from one or more compatible data sources.

This can be useful, but it can also hide different time resolutions, missing-data semantics, and aggregation rules.

If two series are compared visually, verify they represent compatible quantities.

## Units

A wrong display unit can make a technically correct query misleading.

Examples:

- seconds rendered as milliseconds;
- ratio 0–1 rendered as percent without correct scaling;
- bytes shown as decimal/IEC units inconsistently;
- rate displayed as cumulative total.

Visualization correctness is part of observability correctness.

---

# Variables

Variables make dashboards reusable and interactive.

Typical variables represent:

- environment;
- cluster;
- namespace;
- service;
- region;
- instance;
- data source.

## Variables are query multipliers

A variable may issue its own metadata query. A repeated row/panel may then multiply panel queries for every selected value.

A dashboard that looks like one page can produce a large backend workload:

```text
10 panels
x 20 repeated services
x several queries/panel
= hundreds of backend queries
```

Use variables deliberately.

## All/multi-value selections

An “All” option often expands into broad regex or matcher logic. On a high-cardinality Prometheus backend, that can turn a cheap dashboard into an expensive global query.

Test worst-case selections, not only the default.

## Data-source variables

Switching data sources dynamically can be powerful for multi-environment dashboards, but the selected backends must expose compatible metric names and semantics.

---

# Transformations

Grafana transformations operate on query results after retrieval.

They can:

- rename fields;
- filter fields;
- join results;
- calculate fields;
- group or reduce data;
- organize tables;
- reshape frames.

## Transformations are not free

A transformation can move work from the backend into Grafana/browser processing.

This can be appropriate for small result sets but problematic for huge datasets.

Prefer pushing large aggregations into the data system when it has a more efficient query engine.

## Hidden logic risk

If a panel query looks correct but the visualization is wrong, inspect transformations before rewriting the query.

A transformation chain can significantly change the final result.

---

# Explore

Explore is Grafana's interactive investigation workspace.

It is useful for:

- ad hoc queries;
- iterating on PromQL/log/trace expressions;
- split views;
- moving between related signals;
- inspecting query results before committing them to a dashboard.

A healthy workflow is:

```text
incident question
   -> Explore
   -> refine query
   -> validate semantics/cost
   -> promote stable view into dashboard/rule
```

Explore should not become a substitute for durable operational dashboards or alerts when a query is repeatedly needed.

---

# Alerting architecture

Grafana Alerting separates rule evaluation from notification handling, following the Prometheus alerting model.

Conceptually:

```text
data source
    |
    v
alert rule evaluation
    |
    v
alert instances
    |
    v
notification policy / direct contact point
    |
    v
contact point integrations
```

## Alert rules

A rule evaluates queries and expressions on a schedule.

A single rule can produce multiple alert instances when labels create multiple result identities.

This means alert cardinality matters just as dashboard/query cardinality matters.

## Grafana-managed versus data-source-managed rules

Grafana can manage alert rules itself, while some data sources have their own native rule systems.

Keep ownership explicit:

```text
Who evaluates the rule?
Where is the rule stored?
Which query engine executes it?
Which Alertmanager receives it?
```

During migration, duplicate ownership can cause duplicate notifications.

## Contact points

Contact points define notification destinations such as email, messaging systems, incident-management tools, or webhooks.

A contact point can contain multiple integrations.

## Notification policies

Notification policies route alerts based on labels and define grouping/timing behavior.

A policy tree can:

- choose contact points;
- group related alert instances;
- control wait/repeat intervals;
- apply nested routing;
- support silence/mute strategies.

Poor label design at the alert-rule layer makes routing difficult downstream.

## Silences and mute timings

Silences suppress selected alert notifications based on matchers. Mute timings suppress delivery according to schedules.

These mechanisms should reduce known noise without hiding active incidents permanently.

---

# Provisioning and configuration as code

Grafana supports file-based provisioning for resources such as data sources and dashboards, and additional as-code workflows exist for managing Grafana resources.

This is valuable because production observability configuration benefits from:

- version history;
- code review;
- reproducible environments;
- controlled rollout;
- drift detection.

## Ownership rule

Decide whether a resource is primarily managed by:

- provisioning files;
- API/IaC automation;
- UI editing.

Mixing all three without an ownership policy creates confusing drift.

Example failure:

```text
user edits dashboard in UI
      |
      v
provisioning reload overwrites it
      |
      v
user thinks Grafana lost changes
```

The real issue is conflicting sources of truth.

## Secret handling

Do not commit plaintext data-source passwords/tokens merely because the provisioning file is version controlled.

Use environment/secret-management integration appropriate to the deployment.

---

# Dashboard JSON and version control

Grafana dashboards can be represented as JSON and managed through APIs/provisioning/IaC tooling.

Raw JSON is complete but not always human-friendly. Generated fields, IDs, panel coordinates, and plugin options can create noisy diffs.

A good review workflow focuses on semantic changes:

- query expressions;
- data-source references;
- variables;
- transformations;
- thresholds;
- links;
- alert logic;
- permissions/provisioning behavior.

Do not approve a giant dashboard diff based only on “it renders.”

---

# Authentication and authorization

Grafana supports local and external authentication patterns depending on edition and deployment, including integrations with common identity providers.

Authentication answers:

> Who is the user?

Authorization answers:

> What can that user do and which resources can they access?

## Basic roles and permissions

Grafana OSS provides organization/basic-role and dashboard/folder permission mechanisms. More granular RBAC capabilities are edition-dependent.

Do not document Enterprise/Cloud-only RBAC features as if they exist identically in OSS.

## Folder permissions

Folders are important organizational and permission boundaries.

A scalable approach is to align folders with teams, services, or environments and then control dashboard access through folder-level permissions where practical.

Remember that effective access can come from multiple permission paths; evaluate the highest applicable permission rather than assuming a narrower dashboard permission always wins.

## Service accounts

Automation should use service accounts or equivalent non-human credentials rather than personal user credentials.

Scope automation tokens to the minimum required actions.

---

# Data-source security

Data-source configuration is one of the highest-value Grafana trust boundaries.

A user who can modify a data source may be able to:

- redirect queries to another endpoint;
- change credentials;
- alter TLS verification;
- inject custom headers;
- expose broader backend data;
- disrupt every dashboard using that source.

Restrict data-source administration more strongly than ordinary dashboard editing.

## Backend permissions still matter

Grafana should not be the only guard protecting sensitive telemetry.

Where feasible, backend systems should enforce their own authentication and tenant boundaries.

---

# Plugins and supply chain

Plugins execute code inside Grafana's frontend and/or backend plugin environment depending on plugin type.

Treat plugin installation like adding software to a production control plane.

Review:

- publisher/source;
- signature status and policy;
- permissions/capabilities;
- network access;
- update process;
- CVEs/advisories;
- compatibility with the installed Grafana version.

Avoid installing abandoned plugins just because an old dashboard depends on them.

## Plugin upgrades

A plugin upgrade can change:

- query model;
- panel rendering;
- dashboard JSON schema;
- backend protocol behavior;
- alert support;
- browser behavior.

Test representative dashboards before broad rollout.

---

# High availability

A single Grafana instance is straightforward. High availability changes the persistence and routing model.

A typical HA layout is:

```text
                 load balancer
                  /        \
                 v          v
           Grafana A    Grafana B
                  \        /
                   v      v
                shared DB
              MySQL/Postgres
```

The shared database holds durable Grafana state so multiple application instances can serve the same environment.

High availability of Grafana itself does not make the underlying telemetry data sources highly available.

If Prometheus is down, two healthy Grafana servers still cannot query it.

## Sessions

Session behavior and recommended HA configuration can change across Grafana versions. Follow the exact-version upstream HA guidance when choosing shared session stores or load-balancer affinity.

## Database availability

The Grafana database becomes critical control-plane infrastructure in HA deployments.

Protect it with:

- backups;
- tested restore;
- HA appropriate to requirements;
- connection-pool sizing;
- monitoring;
- upgrade/migration planning.

---

# Backup and recovery

A Grafana recovery plan should account for:

- Grafana database;
- configuration files;
- provisioning files;
- plugin state/installations;
- custom certificates;
- secret-management dependencies;
- external database credentials.

If dashboards and data sources are fully provisioned from version-controlled sources, recovery is easier—but user state, alerting state, annotations, and other metadata may still live in the database.

Test restore, not just backup creation.

---

# Performance model

Grafana performance has at least three independent dimensions:

1. Grafana server work.
2. Browser rendering work.
3. Data-source/backend query work.

A slow dashboard may be bottlenecked in any of them.

## Query fan-out

Dashboard load can generate many backend queries through:

- many panels;
- multiple queries per panel;
- repeated panels;
- variables;
- annotations;
- alert preview;
- auto-refresh.

If 100 users open the same expensive dashboard every 10 seconds, the backend impact can be large even if Grafana CPU is low.

## Auto-refresh

Short refresh intervals are not automatically “more real-time.” They can overload data sources and browsers while adding little operational value.

Choose refresh intervals based on:

- source sampling interval;
- query cost;
- incident needs;
- user count;
- dashboard complexity.

Refreshing a Prometheus dashboard every second when metrics scrape every 30 seconds mostly repeats work.

## Result size

Large tables, high-resolution time series, and unbounded log queries can overwhelm browsers.

Use sensible time ranges, limits, aggregation, and query resolution.

## Alert evaluation load

Large numbers of Grafana-managed alert rules and short evaluation intervals can compete with dashboard traffic for resources. At larger scale, follow current Grafana guidance for isolating or scaling alert evaluation.

---

# Query correctness versus visualization correctness

A panel can be wrong even when the query is correct.

Examples:

- threshold uses wrong unit;
- nulls are rendered as zeros;
- field override applies to unintended series;
- transformation drops a field;
- stacking implies quantities are additive when they are not;
- axis scale hides a meaningful difference;
- percentage is computed after an invalid aggregation;
- legend aliases hide distinct label dimensions.

Operational visualization is a form of data modeling.

---

# Common failure modes

## Dashboard shows “No data”

Check in order:

1. time range;
2. variable values;
3. exact query;
4. data-source connectivity;
5. backend result;
6. transformation chain;
7. panel filters/overrides.

“No data” is not the same as zero.

## Data source test fails

Investigate:

- URL/DNS;
- routing/firewall;
- TLS certificates;
- authentication;
- proxy configuration;
- backend health;
- plugin compatibility.

## Dashboard is slow

Use query inspection/profiling to separate:

- backend latency;
- number of queries;
- result size;
- Grafana processing;
- browser rendering.

Do not scale Grafana servers if Prometheus is spending 20 seconds on the PromQL expression.

## Variable dropdown is slow

The variable query may scan high-cardinality metadata.

Limit scope and avoid global label-value scans when possible.

## Alert evaluates differently from dashboard

Check:

- evaluation interval/time;
- query expression;
- data source;
- transformations unavailable to alerting;
- dashboard variables versus alert labels;
- reduce/condition expressions;
- missing-data/error-state handling.

A dashboard panel and an alert are separate execution contexts.

## Dashboard edits disappear

Likely causes include provisioning or external automation reapplying the source-of-truth definition.

Find the owner before editing again.

## Users see data they should not

Audit both Grafana permissions and backend credential scope. A shared broadly privileged data source can defeat assumptions made at the folder level.

## Duplicate alerts

Check whether the same logical rule is evaluated by:

- Grafana-managed alerting;
- Prometheus/data-source-managed rules;
- multiple Grafana instances without correct HA coordination;
- duplicated provisioning definitions.

---

# Debugging workflow

## 1. Reproduce in Explore

Take the panel query into Explore to remove dashboard layout/repetition complexity.

## 2. Inspect query details

Use Grafana's query inspection tools to see the actual request and response where supported.

Compare:

- expanded variables;
- request URL/body;
- query duration;
- returned series/frames;
- errors.

## 3. Run query at the backend

For Prometheus, run the exact PromQL directly in Prometheus or another trusted query client.

If it is slow there, optimize the query/backend first.

## 4. Remove transformations

If raw data is correct, disable transformations progressively until the incorrect step becomes visible.

## 5. Check panel options

Validate units, overrides, null behavior, thresholds, stacking, and field selection.

## 6. Inspect server logs

For connection/auth/plugin/server problems, inspect Grafana server logs and relevant backend logs.

## 7. Check provisioning ownership

If configuration reverts, inspect Git/IaC/provisioning pipelines before making more UI edits.

---

# Dashboard engineering practices

## Build from questions, not available metrics

Start with an operational question such as:

> Are users experiencing elevated latency in checkout?

Then choose metrics and visualizations that answer it.

Do not start with:

> We have 300 metrics; how can we put them all on one page?

## Separate overview and drill-down

A top-level service dashboard should remain readable during an incident.

Link to deeper dashboards for:

- instances;
- databases;
- queues;
- Kubernetes resources;
- dependency-specific diagnostics.

## Include context

Useful dashboards often include:

- deployment annotations;
- SLO thresholds;
- ownership/runbook links;
- environment variables;
- links to logs/traces.

## Review query cost

Treat dashboards like code. A small visual edit can contain a large query change.

---

# Alert engineering practices

## Keep labels routable

Alert labels should describe stable dimensions such as service/team/severity/environment.

Avoid unbounded labels that create thousands of alert instances.

## Separate rule semantics from notification policy

Rule:

> Is this condition true?

Notification policy:

> Who should receive it, when, and grouped how?

This separation makes routing reusable.

## Test contact points

A configured contact point that has never sent a test notification should not be assumed to work during an incident.

## Monitor the alerting system

Watch rule-evaluation failures and notification delivery failures. An alerting platform can fail silently if nobody monitors its own health.

---

# Security model

## Protect admin access

Grafana administrators can control data sources, plugins, users, and broad application settings. Use strong authentication and least privilege.

## Protect secrets

Data-source credentials and notification tokens should not appear in dashboards or repositories.

## Review anonymous/public access

Public or anonymous dashboard access can intentionally expose operational data. Confirm that data-source results do not contain internal identifiers or sensitive business metrics.

## Reverse proxy and TLS

When Grafana is served behind a reverse proxy, configure root URL, forwarded headers, TLS termination, and authentication boundaries deliberately.

## Content and link safety

Dashboards can contain links and rendered content. Treat untrusted plugin/content sources carefully, especially in shared environments.

## Keep current

Grafana is a large web application with plugins and third-party integrations. Track security advisories and supported-release guidance.

---

# OSS versus Enterprise/Cloud

Grafana documentation covers multiple editions.

A deep technical reference must not imply that every feature is available identically in Grafana OSS.

Examples of edition-sensitive areas can include:

- fine-grained RBAC;
- reporting;
- enterprise data-source capabilities;
- certain access-management features;
- managed-cloud integrations.

When planning a feature, verify the edition marker in current documentation.

This OpenDevIndex module primarily describes the open-source Grafana platform and marks edition-sensitive functionality when relevant.

---

# Licensing

The current Grafana source repository is licensed under the GNU Affero General Public License v3.

License obligations matter especially when modifying and operating network-accessible software. Organizations distributing or modifying Grafana should review the actual AGPL text and obtain legal advice where needed rather than relying on a short technical summary.

Plugins and bundled components may have their own licenses.

---

# Scaling patterns

## Small deployment

```text
users -> one Grafana -> SQLite -> a few data sources
```

Appropriate for development or small evaluation use.

## Production deployment

```text
users
  |
load balancer
 /         \
Grafana A Grafana B
 \         /
 shared PostgreSQL/MySQL
      |
 multiple data sources
```

Add monitoring, backups, secure authentication, controlled provisioning, and plugin governance.

## Large installation concerns

At organization scale, separate concerns become important:

- dashboard ownership;
- folder hierarchy;
- data-source tenancy;
- query budgets;
- alert evaluation capacity;
- plugin governance;
- database scaling;
- image rendering capacity;
- authentication/authorization;
- provisioning pipelines.

One global Grafana instance can be useful, but it also creates a broad blast radius. Multiple instances can improve isolation but increase operational duplication. Choose deliberately.

---

# Anti-patterns

## Using Grafana as the only definition of observability semantics

Critical metrics and SLO formulas should have documented/query-rule ownership outside one hand-edited panel.

## Giant dashboards

Hundreds of panels create cognitive and query load.

## One shared admin data source for every user

Creates unnecessary data exposure and blast radius.

## One-second refresh everywhere

Often wastes resources without adding information.

## Dashboard variables with unbounded label scans

Creates slow metadata queries and poor UX.

## UI edits on provisioned dashboards

Creates source-of-truth conflicts.

## Installing unsigned/abandoned plugins casually

Expands the supply-chain attack surface.

## Alert rules without notification tests

A firing condition is useless if delivery is broken.

## Treating “No data” as healthy zero

Can hide collection failures.

---

# Operational checklist

Before production use, verify:

- authentication is integrated and tested;
- administrator access is limited;
- folder/dashboard permissions match ownership;
- data-source credentials are least privilege;
- backend systems enforce tenancy where required;
- provisioning/IaC/UI ownership is documented;
- plugins are approved and monitored for updates;
- dashboard query cost is reviewed;
- variables do not create uncontrolled fan-out;
- critical dashboards use consistent units and semantics;
- alert evaluation and notification delivery are monitored;
- contact points are tested;
- Grafana database is backed up and restore is tested;
- HA deployments use a supported shared database/topology;
- Grafana and data sources are monitored independently;
- security advisories and release compatibility are tracked.

---

# Learning path

## Beginner

Learn:

1. data sources;
2. queries;
3. panels;
4. dashboards;
5. variables;
6. Explore.

Practice:

- add Prometheus as a data source;
- build a request-rate panel;
- add a service variable;
- reproduce the query in Explore;
- add a dashboard link to a drill-down view.

## Intermediate

Learn:

1. transformations;
2. annotations;
3. provisioning;
4. folders and permissions;
5. alert rules;
6. notification policies/contact points;
7. plugin lifecycle.

Practice:

- provision a dashboard from version control;
- build a metric-to-trace workflow;
- create an alert with stable routing labels;
- test a contact point;
- debug a slow repeated panel.

## Advanced

Learn:

1. HA architecture;
2. database scaling/recovery;
3. query fan-out and backend load;
4. multi-team tenancy;
5. plugin security;
6. alerting scale;
7. edition boundaries;
8. as-code governance.

Practice:

- run multiple Grafana nodes against a shared database;
- restore configuration from backup;
- measure backend query load from a large dashboard;
- design separate team data-source permissions;
- simulate a data-source outage and verify dashboard/alert behavior.

---

# Relationships in OpenDevIndex

- `cloud/prometheus` — Grafana has a built-in Prometheus data source and commonly uses PromQL for dashboards, Explore, exemplars, and alerting.

Grafana also integrates with many logging, tracing, SQL, cloud, and observability systems. Relationships should be added only when corresponding OpenDevIndex modules exist and the edge communicates meaningful architectural information rather than graph density.

---

# Verification

This deep-dive was reviewed on **2026-09-06** against current upstream Grafana documentation covering data sources, Prometheus integration, dashboards, Explore, variables, transformations, alerting, notification routing, provisioning, authentication, permissions, plugins, high availability, installation, and backup/recovery.

The module deliberately separates Grafana OSS from Enterprise/Cloud-only features and avoids hard-coding version-sensitive deployment recommendations where they may change. Exact supported databases, browser versions, HA session behavior, plugin APIs, and alerting scale guidance should be checked against the documentation for the installed Grafana release.

---

# Maintenance

Update this module when any of the following materially changes:

- dashboard or data-source architecture;
- plugin platform/security model;
- Grafana Alerting architecture;
- provisioning/as-code workflows;
- OSS permission model;
- HA/session/database guidance;
- supported persistent databases;
- Prometheus data-source capabilities;
- licensing;
- security guidance.

Preserve the stable OpenDevIndex address `cloud/grafana`. Deep-dive content should remain hand-curated and source-backed rather than being replaced by a generic catalog renderer.
