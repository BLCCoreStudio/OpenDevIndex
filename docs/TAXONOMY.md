# Taxonomy v2

OpenDevIndex separates a module's **stable address** from its **semantic classification**.

## Stable address

Every module has a durable `<category>/<slug>` address used for independent versioning and links, for example:

```text
tool/git
framework/pytorch
ai/tensorflow
protocol/mcp
```

Existing addresses are not renamed merely because classification improves. This avoids breaking references to published modules.

## Canonical kind

`kind` answers **what the technology is**. Taxonomy v2 currently supports:

- `tool`
- `language`
- `framework`
- `library`
- `runtime`
- `platform`
- `database`
- `protocol`
- `standard`
- `system`
- `toolchain`
- `service`
- `project`
- `concept`

For example, the stable address `ai/tensorflow` is classified as `kind: framework`. The address is retained for compatibility; discovery uses the canonical kind.

## Domains

`domains` answer **where the technology belongs or is commonly used**. They are multi-valued facets such as:

```yaml
domains:
  - ai
  - machine-learning
```

A technology can belong to several domains without being duplicated. PyTorch and TensorFlow can both be frameworks while also belonging to AI and machine learning. Docker can be a tool while belonging to containers and DevOps.

The controlled domain vocabulary lives in [`taxonomy/v2.yaml`](../taxonomy/v2.yaml).

## Deployment and license metadata

Taxonomy-aware entries may also include:

```yaml
license: Apache-2.0
deployment_types:
  - self-hosted
  - saas
```

These fields improve search and filtering but are curated only when they can be stated accurately. Complex or build-dependent licensing should not be reduced to a misleading single value.

## New modules

New entries should prefer a canonical kind as their address namespace where practical, for example `runtime/wasmtime` or `library/pytest`. Legacy address namespaces such as `ai/`, `security/`, `cloud/`, and `opensource/` remain supported for already-published modules.

## Why this model

A single folder-like hierarchy cannot represent modern software accurately. A project can simultaneously be a framework, AI technology, Python ecosystem component, distributed system, and developer tool. Stable addresses plus multi-valued taxonomy facets provide compatibility without sacrificing discoverability.
