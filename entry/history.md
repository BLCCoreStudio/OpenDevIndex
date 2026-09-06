# History

## 2026-09-06 — deep-dive upgrade

- Upgraded `tool/github-actions` from schema v2 to schema v3.
- Reframed the module around the hosted workflow control plane, event/ref semantics, job graphs, runners, actions, permissions, secrets, environments, caches, artifacts, and deployment boundaries.
- Added security guidance for `pull_request`, `pull_request_target`, `workflow_run`, untrusted event data, action SHA pinning, `GITHUB_TOKEN` least privilege, OIDC federation, and environment protection.
- Added hosted/self-hosted/ephemeral runner trust models, runner groups, Actions Runner Controller, network and ambient-cloud-identity risks, cache/artifact trust boundaries, and runner-compromise response.
- Added concurrency, matrices, reusable workflows, deployment architecture, supply-chain integrity, performance, failure modes, debugging, organization-scale platform design, and operational review checklists.
- Preserved `MIT` license metadata specifically for the indexed open-source `actions/runner` repository and documented that the hosted GitHub Actions service is a separate licensing/product boundary.
- Added Technology Universe coverage metadata and typed relationships to Git and Kubernetes.
- Expanded the primary-source set to current official GitHub Actions documentation and the canonical runner repository.

## 2026-08-31 — v0.2

- Reviewed `tool/github-actions` against the current OpenDevIndex catalog and taxonomy.
- Recorded canonical kind `tool` and domain facets: ci-cd, devops.
- Re-rendered module documentation from validated source-backed metadata.
