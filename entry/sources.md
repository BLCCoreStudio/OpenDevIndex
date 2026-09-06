# Sources

Reviewed for the OpenTelemetry deep-dive on **2026-09-06**.

OpenDevIndex prefers the upstream OpenTelemetry specification, current project documentation, semantic-convention specification, OTLP specification, and Collector documentation. OpenTelemetry has multiple independently evolving components, so exact feature maturity must be verified for the specific language SDK, Collector distribution, protocol signal, and backend.

## Project and specification

- **What is OpenTelemetry?** — https://opentelemetry.io/docs/what-is-opentelemetry/ (`official`)
- **OpenTelemetry specification repository** — https://github.com/open-telemetry/opentelemetry-specification (`standard`)
- **Apache-2.0 license** — https://github.com/open-telemetry/opentelemetry-specification/blob/main/LICENSE (`repository`)
- **OpenTelemetry Concepts** — https://opentelemetry.io/docs/concepts/ (`documentation`)
- **OpenTelemetry Components** — https://opentelemetry.io/docs/concepts/components/ (`documentation`)
- **Instrumentation** — https://opentelemetry.io/docs/concepts/instrumentation/ (`documentation`)
- **Instrumentation Libraries** — https://opentelemetry.io/docs/concepts/instrumentation/libraries/ (`documentation`)

## Identity, context, and conventions

- **Resources** — https://opentelemetry.io/docs/concepts/resources/ (`documentation`)
- **Instrumentation Scope** — https://opentelemetry.io/docs/concepts/instrumentation-scope/ (`documentation`)
- **Context Propagation** — https://opentelemetry.io/docs/concepts/context-propagation/ (`documentation`)
- **Baggage** — https://opentelemetry.io/docs/concepts/signals/baggage/ (`documentation`)
- **Semantic Conventions** — https://opentelemetry.io/docs/specs/semconv/ (`standard`)
- **Resource Semantic Conventions** — https://opentelemetry.io/docs/specs/semconv/resource/ (`standard`)

## Signals

- **Signals** — https://opentelemetry.io/docs/concepts/signals/ (`documentation`)
- **Tracing API / Span model** — https://opentelemetry.io/docs/specs/otel/trace/api/ (`standard`)
- **Metrics Data Model** — https://opentelemetry.io/docs/specs/otel/metrics/data-model/ (`standard`)
- **OpenTelemetry Logging specification** — https://opentelemetry.io/docs/specs/otel/logs/ (`standard`)
- **Sampling** — https://opentelemetry.io/docs/concepts/sampling/ (`documentation`)

## OTLP

- **OTLP Specification** — https://opentelemetry.io/docs/specs/otlp/ (`standard`)
- **OTLP Exporter specification** — https://opentelemetry.io/docs/specs/otel/protocol/exporter/ (`standard`)
- **Environment Variable Specification** — https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/ (`standard`)

## Collector

- **OpenTelemetry Collector** — https://opentelemetry.io/docs/collector/ (`documentation`)
- **Collector Components** — https://opentelemetry.io/docs/collector/components/ (`documentation`)
- **Collector Configuration** — https://opentelemetry.io/docs/collector/configuration/ (`documentation`)
- **Collector Resiliency** — https://opentelemetry.io/docs/collector/resiliency/ (`documentation`)
- **Collector Scaling** — https://opentelemetry.io/docs/collector/scaling/ (`documentation`)
- **Collector Troubleshooting** — https://opentelemetry.io/docs/collector/troubleshooting/ (`documentation`)
- **Collector Internal Telemetry** — https://opentelemetry.io/docs/collector/internal-telemetry/ (`documentation`)

## Editorial notes

- OpenTelemetry is not an observability storage or visualization backend; those functions are intentionally left to other systems.
- Trace, metric, and log OTLP transport is currently stable, while evolving signals can have different maturity.
- Language implementations do not necessarily reach feature maturity simultaneously; verify each SDK's support matrix before standardizing configuration.
- Semantic conventions evolve independently and can contain stable and development groups at the same time.
- Collector core/contrib/custom distributions do not contain identical component sets.
- Prometheus interoperability requires explicit attention to temporality, histogram representation, Resource mapping, metric names, and attributes.
