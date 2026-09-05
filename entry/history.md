# History

## 2026-09-06 — flagship deep-dive upgrade

- Upgraded `tool/docker` from schema v1 overview metadata to schema v3.
- Replaced the generated overview with a standalone technical deep dive covering Engine architecture, containerd/OCI boundaries, images and layers, BuildKit, runtime isolation, storage, networking, Compose, security, performance, failure modes, alternatives, and learning paths.
- Added deliberate graph relationships to `concept/containers`, `tool/containerd`, `tool/podman`, `cloud/kubernetes`, and `opensource/linux-kernel`.
- Expanded the source set from two general references to Docker architecture, security, rootless, networking, storage, BuildKit, Compose, canonical source repositories, and OCI specifications.
- Marked the module with the protected `deep-dive` tag so automated catalog refreshes cannot silently overwrite curated depth.

## Earlier history

### 2026-08-31 — v0.1

- Reviewed `tool/docker` against the current OpenDevIndex catalog and taxonomy.
- Recorded canonical kind `tool` and domain facets: containers, devops.
- Re-rendered module documentation from validated source-backed metadata.

### 2026-08-31 — initial publication

- Added `tool/docker` to the curated OpenDevIndex v0.1 catalog.
- Created the initial source-backed knowledge module.
- Verified metadata structure and required references with the repository validator.
