# Sources

Verified on **2026-09-05**. This module prefers containerd's canonical repository documentation, OCI standards, and official Kubernetes runtime documentation.

## Project and architecture

- **containerd official site** — https://containerd.io/ (`official`)
  - Canonical project identity and high-level scope.
- **containerd source repository** — https://github.com/containerd/containerd (`repository`)
  - Canonical implementation, APIs, release branches, issue history, and project README.
- **containerd Getting Started** — https://github.com/containerd/containerd/blob/main/docs/getting-started.md (`documentation`)
  - Installation, client/tool roles, daemon configuration, native API usage, and Kubernetes setup guidance.
- **containerd Operations Guide** — https://github.com/containerd/containerd/blob/main/docs/ops.md (`documentation`)
  - Persistent `root` versus ephemeral `state`, plugin-owned storage, metrics, metadata configuration, and operational cautions.
- **containerd Releases and Stability** — https://github.com/containerd/containerd/blob/main/RELEASES.md (`documentation`)
  - API/release policy, deprecations/removals, `ctr` stability expectations, and version-specific migration context.

## Kubernetes and node integration

- **containerd CRI Plugin Configuration** — https://github.com/containerd/containerd/blob/main/docs/cri/config.md (`documentation`)
  - Current CRI configuration structure, containerd 2.x config version 3, snapshotter/runtime classes, and cgroup guidance.
- **containerd NRI Documentation** — https://github.com/containerd/containerd/blob/main/docs/NRI.md (`documentation`)
  - NRI integration, containerd namespace examples, and node-resource extension behavior.
- **Kubernetes Container Runtime Interface** — https://kubernetes.io/docs/concepts/containers/cri/ (`documentation`)
  - Official kubelet-to-runtime API boundary and Kubernetes runtime model.

## Runtime standard

- **OCI Runtime Specification** — https://specs.opencontainers.org/runtime-spec/ (`standard`)
  - Standard runtime configuration/state/lifecycle boundary used beneath higher-level container lifecycle managers.

## Source policy

Version-sensitive claims—especially config/plugin IDs, CRI behavior, release compatibility, sandbox/NRI behavior, and runtime integrations—should be rechecked against the deployed containerd major/minor release before updating the module. The project README and `docs/` tree are preferred over third-party tutorials for architecture and operations. Historical design documents may explain intent but should not override current implementation documentation.
