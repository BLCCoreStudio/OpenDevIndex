# History

## 2026-09-06 — deep-dive upgrade

- Upgraded `cloud/terraform` from schema v1 to schema v3.
- Reframed the module around Terraform Core, provider plugins, resource addresses, dependency graph evaluation, plan/apply semantics, state ownership, locking, and recovery.
- Added modules, refactoring, imports, lifecycle controls, provider supply-chain security, sensitive and ephemeral values, testing, CI/CD, performance, failure modes, and disaster-recovery guidance.
- Verified the current upstream Terraform license as `BUSL-1.1` for Terraform 1.6.0 and later and documented the operationally relevant OpenTofu alternative relationship.
- Added Technology Universe coverage metadata and typed relationships to OpenTofu, Kubernetes, and Ansible.
- Expanded the primary-source set to current HashiCorp documentation and the canonical Terraform repository.

## 2026-08-31 — v0.1

- Reviewed `cloud/terraform` against the current OpenDevIndex catalog and taxonomy.
- Recorded canonical kind `tool` and domain facets: cloud, devops.
- Re-rendered module documentation from validated source-backed metadata.

## Earlier history

## 2026-08-31

- Added `cloud/terraform` to the curated OpenDevIndex v0.1 catalog.
- Created the initial source-backed knowledge module.
- Verified metadata structure and required references with the repository validator.
