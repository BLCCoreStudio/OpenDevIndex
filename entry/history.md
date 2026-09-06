# History

## 2026-09-05 — deep-dive review

- Upgraded `cloud/helm` from schema v1 to schema v3.
- Reframed the module around the chart -> values -> rendered manifests -> Kubernetes API -> release-record mental model.
- Added modern Helm client/library architecture and clarified that current Helm does not use the historical Helm 2 Tiller model.
- Added chart anatomy, versioning, templating, values precedence/schema, helpers, dependencies, library charts, rendering, install/upgrade/rollback/uninstall lifecycle, hooks, CRDs, and release revisions.
- Added Kubernetes ownership boundaries, drift and multi-owner conflicts, GitOps interaction, OCI/chart repository distribution, provenance, RBAC, release-metadata sensitivity, chart security review, plugins, Go SDK, performance, failure modes, and CI/CD guidance.
- Added Helm 2/3/4 context while marking major/minor-version behavior and Helm/Kubernetes compatibility as release-sensitive.
- Added Technology Universe coverage metadata for orchestration, deployment, CI/CD, and platform engineering.
- Added a deliberate graph relationship to `cloud/kubernetes` without adding generic ecosystem edges.
- Expanded the source set to current Helm architecture, charts, templating, release lifecycle, OCI, provenance, RBAC, plugins, support policy, and Helm 4 documentation.

## 2026-08-31 — v0.1

- Reviewed `cloud/helm` against the current OpenDevIndex catalog and taxonomy.
- Recorded canonical kind `tool` and domain facets: cloud, devops.
- Re-rendered module documentation from validated source-backed metadata.

## Earlier history

## 2026-08-31

- Added `cloud/helm` to the curated OpenDevIndex v0.1 catalog.
- Created the initial source-backed knowledge module.
- Verified metadata structure and required references with the repository validator.
