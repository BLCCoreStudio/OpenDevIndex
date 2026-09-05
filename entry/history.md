# History

## 2026-09-06 — deep-dive review

- Upgraded `cloud/kubernetes` from schema v1 to schema v3.
- Reframed the module around the API-driven desired-state and reconciliation model rather than presenting Kubernetes as generic container clustering.
- Added the control-plane and node architecture: kube-apiserver, etcd, kube-scheduler, controller manager, kubelet, CRI runtime, networking, and CSI storage boundaries.
- Added the Kubernetes object model, controller ownership, finalizers, workload controllers, scheduling, resource requests/limits, probes, graceful termination, networking, storage, security, extensibility, observability, high availability, upgrades, performance, autoscaling, and failure diagnosis.
- Added Technology Universe coverage metadata for containers, orchestration, deployment, reliability, and platform engineering.
- Added deliberate graph relationships to Containers, containerd, and Docker.
- Expanded the source set to upstream Kubernetes architecture, API, workload, scheduling, networking, storage, security, etcd, and upgrade documentation.
- Marked version-sensitive operational details so future maintenance can distinguish durable mental models from release-specific behavior.

## 2026-08-31 — v0.1

- Reviewed `cloud/kubernetes` against the current OpenDevIndex catalog and taxonomy.
- Recorded canonical kind `platform` and domain facets: cloud, containers.
- Re-rendered module documentation from validated source-backed metadata.

## Earlier history

## 2026-08-31

- Added `cloud/kubernetes` to the curated OpenDevIndex v0.1 catalog.
- Created the initial source-backed knowledge module.
- Verified metadata structure and required references with the repository validator.
