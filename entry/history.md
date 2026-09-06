# History

## 2026-09-06 — deep-dive

- Promoted `platform/argocd` from a compact schema-v2 overview to a schema-v3 deep technical reference.
- Reframed the module around Argo CD's actual control model: source resolution, manifest generation, desired/live comparison, health assessment, synchronization, and repeated reconciliation.
- Documented API server, repository server, application controller, ApplicationSet controller, Redis, identity integration, and their trust boundaries.
- Added Application, AppProject, ApplicationSet, resource tracking, sync policy, pruning, self-heal, hooks, waves, diff customization, health, and deletion semantics.
- Added Helm rendering behavior, Git revision strategy, multi-cluster delivery, ApplicationSet fleet risks, security, reliability, disaster recovery, scaling, observability, failure diagnosis, and operational workflows.
- Added Technology Universe coverage metadata and typed relationships to Kubernetes, Git, Helm, and Flux.
- Verified license and expanded the source set to current upstream architecture, synchronization, ApplicationSet, security, health, diffing, Helm integration, and recovery documentation.

## 2026-08-31 — v0.5

- Reviewed `platform/argocd` against the current OpenDevIndex catalog and taxonomy.
- Recorded canonical kind `platform` and domain facets: ci-cd, cloud, devops.
- Re-rendered module documentation from validated source-backed metadata.
