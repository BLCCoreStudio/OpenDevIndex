# History

## 2026-09-06 — deep-dive upgrade

- Upgraded `tool/opentofu` from schema v2 to schema v3.
- Reframed the module around OpenTofu Core, provider plugins, resource identity, dependency-aware planning, state, locking, and apply semantics.
- Added native state/plan encryption architecture, KMS/key-provider boundaries, migration/fallback behavior, key-rotation and disaster-recovery guidance.
- Documented Public OpenTofu Registry behavior, provider/module supply-chain boundaries, v1.x compatibility promises, Terraform migration paths, and portability trade-offs.
- Verified the canonical project license as `MPL-2.0` and documented Terraform as the closest indexed alternative with distinct governance and licensing.
- Added Technology Universe coverage metadata and typed relationships to Terraform and Kubernetes.
- Expanded the primary-source set to current OpenTofu documentation and the canonical repository.

## 2026-08-31 — v0.5

- Reviewed `tool/opentofu` against the current OpenDevIndex catalog and taxonomy.
- Recorded canonical kind `tool` and domain facets: cloud, developer-tools, devops.
- Re-rendered module documentation from validated source-backed metadata.
