# History

## 2026-09-05 — deep-dive upgrade

- Upgraded `tool/containerd` from schema v2 to schema v3.
- Added Technology Universe coverage mapping for `cloud-devops-sre` / `containers` and `deployment`.
- Reframed the module around containerd's actual layer in the stack: lifecycle daemon/API between higher-level platforms and low-level runtimes.
- Added detailed coverage of content, images, descriptors, snapshots, container metadata, tasks, namespaces, garbage collection, leases, plugins, Runtime v2/shims, persistent root/runtime state, events, and observability.
- Added Kubernetes CRI, runtime-class, cgroup, CNI, and NRI integration context.
- Documented `ctr`, `nerdctl`, and `crictl` as different diagnostic/user interfaces rather than interchangeable views.
- Added security boundaries, performance characteristics, upgrade concerns, common failure modes, and an evidence-driven operational workflow.
- Added graph relationships to Containers, Docker, and Kubernetes.
- Expanded sources to current project documentation, OCI standards, and official Kubernetes CRI documentation.

## 2026-08-31 — v0.5

- Reviewed `tool/containerd` against the current OpenDevIndex catalog and taxonomy.
- Recorded canonical kind `tool` and domain facets: cloud, containers, systems.
- Re-rendered module documentation from validated source-backed metadata.
