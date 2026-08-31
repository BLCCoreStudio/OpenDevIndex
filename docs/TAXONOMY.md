# Taxonomy v3

OpenDevIndex separates a module's **stable address**, **semantic classification**, **domains**, and **relationships** so the catalog can grow into a technology knowledge graph without breaking published links.

## Stable address

Every module has a durable `<category>/<slug>` address, for example:

```text
tool/git
framework/pytorch
ai/tensorflow
protocol/mcp
hardware/ryzen-9-9950x
architecture/x86-64
algorithm/dijkstra
model/llama
format/parquet
dataset/imagenet
```

Existing addresses are not renamed merely because classification improves. Legacy namespaces such as `ai/`, `security/`, `cloud/`, and `opensource/` remain valid.

## Canonical kind

`kind` answers **what the subject is**. Taxonomy v3 keeps the software kinds from v2 and expands them with technology-wide kinds including:

- `hardware`
- `architecture`
- `algorithm`
- `model`
- `format`
- `device`
- `dataset`
- `technique`
- `operating-system`
- `kernel`
- `specification`

This lets one stable address remain compatible while semantic classification becomes more precise. For example, `opensource/linux-kernel` can remain a stable address while being classified as `kind: kernel`.

## Domains

`domains` answer **where the technology belongs or is commonly used**. They are multi-valued facets. Taxonomy v3 expands coverage beyond software into areas such as:

```yaml
domains:
  - computer-architecture
  - hardware
  - operating-systems
  - cryptography
  - identity
  - internet
  - wireless
  - embedded
  - iot
  - robotics
  - quantum-computing
  - supply-chain
  - performance
  - reliability
```

A subject may belong to several domains without being duplicated. The controlled vocabulary lives in [`taxonomy/v3.yaml`](../taxonomy/v3.yaml).

## Relationships

Schema v3 can connect modules using typed relationships:

```yaml
relationships:
  - type: implements
    target: architecture/x86-64
  - type: depends-on
    target: protocol/http
  - type: alternative-to
    target: tool/example
  - type: successor-of
    target: technology/example-v1
```

The controlled relationship vocabulary includes:

- `depends-on`
- `implements`
- `built-with`
- `uses`
- `used-by`
- `integrates-with`
- `compatible-with`
- `alternative-to`
- `extends`
- `part-of`
- `based-on`
- `successor-of`
- `predecessor-of`
- `replaces`
- `secures`
- `related-to`

A relationship may include a short `note` when the edge is not obvious. Relationship targets use stable module references so graph edges remain durable.

## Deployment and license metadata

Taxonomy-aware entries may also include deployment and licensing metadata:

```yaml
license: Apache-2.0
deployment_types:
  - self-hosted
  - service
```

Taxonomy v3 also supports physical and low-level deployment forms such as `hardware`, `device`, `firmware`, and `embedded`.

## Compatibility

The validator continues to accept schema versions 1 and 2. New modules should use schema version 3 so they can participate fully in the knowledge graph. Taxonomy v2 remains in the repository as a historical compatibility artifact; current tooling defaults to v3.

## Why this model

A single hierarchy cannot represent modern technology accurately. A technology can simultaneously be a protocol implementation, security boundary, hardware dependency, learning prerequisite, alternative, historical successor, and part of several domains. Stable addresses plus canonical kinds, multi-valued domains, and typed graph relationships provide compatibility without sacrificing depth or discoverability.
