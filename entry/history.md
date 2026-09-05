# History

## 2026-09-05 — deep-dive upgrade

- Upgraded `concept/containers` from schema v1 to schema v3.
- Added Technology Universe coverage mapping for `cloud-devops-sre` / `containers` and `deployment`.
- Reframed the module around the process-isolation mental model instead of treating containers as lightweight virtual machines.
- Added detailed coverage of Linux namespaces, cgroup v2 resource control, capabilities, seccomp, user namespaces, filesystem/storage behavior, networking, lifecycle, observability, performance, reliability, and security boundaries.
- Added a vendor-neutral OCI model for image, runtime, and distribution specifications.
- Added Kubernetes CRI context to separate orchestration from low-level runtime behavior.
- Added deliberate graph relationships to the Linux kernel, Docker, containerd, Podman, and Kubernetes modules.
- Replaced the minimal source list with standards, kernel documentation, canonical Linux man-pages references, and official Kubernetes documentation.

## 2026-08-31 — v0.1

- Reviewed `concept/containers` against the current OpenDevIndex catalog and taxonomy.
- Recorded canonical kind `concept` and domain facets: containers, software-development.
- Re-rendered module documentation from validated source-backed metadata.

## Earlier history

### 2026-08-31

- Added `concept/containers` to the curated OpenDevIndex v0.1 catalog.
- Created the initial source-backed knowledge module.
- Verified metadata structure and required references with the repository validator.
