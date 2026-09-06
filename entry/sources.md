# Sources

Reviewed for the Prometheus deep-dive on **2026-09-06**.

OpenDevIndex prefers upstream project documentation, canonical repositories, protocol/specification material, and original operational guidance. Version-sensitive flags and feature states should be checked against the documentation for the exact Prometheus release in use.

## Project and architecture

- **Prometheus Overview** — https://prometheus.io/docs/introduction/overview/ (`official`)
- **Prometheus source repository** — https://github.com/prometheus/prometheus (`repository`)
- **Prometheus Apache-2.0 license** — https://github.com/prometheus/prometheus/blob/main/LICENSE (`repository`)

## Data model and metrics

- **Data Model** — https://prometheus.io/docs/concepts/data_model/ (`documentation`)
- **Metric Types** — https://prometheus.io/docs/concepts/metric_types/ (`documentation`)
- **Metric and Label Naming** — https://prometheus.io/docs/practices/naming/ (`documentation`)
- **Instrumentation Practices** — https://prometheus.io/docs/practices/instrumentation/ (`documentation`)
- **Histograms and Summaries** — https://prometheus.io/docs/practices/histograms/ (`documentation`)

## Collection and configuration

- **Prometheus Configuration** — https://prometheus.io/docs/prometheus/latest/configuration/configuration/ (`documentation`)
- **Configuration Reloading** — https://prometheus.io/docs/prometheus/latest/configuration/configuration/ (`documentation`)
- **Federation** — https://prometheus.io/docs/prometheus/latest/federation/ (`documentation`)

## PromQL and API

- **Querying Basics** — https://prometheus.io/docs/prometheus/latest/querying/basics/ (`documentation`)
- **Operators** — https://prometheus.io/docs/prometheus/latest/querying/operators/ (`documentation`)
- **Functions** — https://prometheus.io/docs/prometheus/latest/querying/functions/ (`documentation`)
- **HTTP API** — https://prometheus.io/docs/prometheus/latest/querying/api/ (`documentation`)

## Rules and alerting

- **Recording Rules** — https://prometheus.io/docs/prometheus/latest/configuration/recording_rules/ (`documentation`)
- **Alerting Rules** — https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/ (`documentation`)
- **Alerting Practices** — https://prometheus.io/docs/practices/alerting/ (`documentation`)

## Storage and scaling

- **Prometheus Storage** — https://prometheus.io/docs/prometheus/latest/storage/ (`documentation`)
- **Remote Write Tuning** — https://prometheus.io/docs/practices/remote_write/ (`documentation`)
- **Remote Write Specification** — https://prometheus.io/docs/specs/prw/remote_write_spec/ (`documentation`)
- **Remote Write 2.0 Specification** — https://prometheus.io/docs/specs/prw/remote_write_spec_2_0/ (`documentation`)

## Editorial notes

- Prometheus core is documented separately from ecosystem projects such as Alertmanager, Prometheus Operator, Thanos, Cortex/Mimir, and Grafana.
- Kubernetes operator custom resources are discussed only to explain the configuration-generation boundary; they are not part of the core Prometheus server API.
- Native histograms and remote-write protocol behavior are explicitly treated as version-sensitive.
- Prometheus is a monitoring metrics system, not an authoritative billing, event-log, audit-log, or tracing database.
