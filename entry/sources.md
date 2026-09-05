# Sources

Verified on **2026-09-05**. This module prefers standards, kernel documentation, canonical Linux man-pages documentation, and official orchestration documentation.

## Container standards

- **Open Container Initiative** — https://opencontainers.org/ (`official`)
  - Organization responsible for open container image, runtime, and distribution specifications.
- **OCI Image Specification** — https://specs.opencontainers.org/image-spec/ (`standard`)
  - Defines the image manifest/index model, configuration, descriptors, filesystem layers, image layout, and conversion into runnable content.
- **OCI Runtime Specification** — https://specs.opencontainers.org/runtime-spec/ (`standard`)
  - Defines runtime configuration, execution environment, state, and lifecycle operations for containers.
- **OCI Distribution Specification** — https://specs.opencontainers.org/distribution-spec/ (`standard`)
  - Defines registry API behavior for pushing, pulling, discovering, and managing manifests and blobs.

## Linux isolation and resource control

- **Linux namespaces manual page** — https://man7.org/linux/man-pages/man7/namespaces.7.html (`documentation`)
  - Canonical Linux man-pages overview of namespace types and the isolation model used to build containers.
- **Linux user namespaces manual page** — https://man7.org/linux/man-pages/man7/user_namespaces.7.html (`documentation`)
  - Documents UID/GID mapping and capability behavior across user-namespace boundaries.
- **Linux control group v2 documentation** — https://docs.kernel.org/admin-guide/cgroup-v2.html (`documentation`)
  - Authoritative kernel documentation for hierarchical process organization and resource-control interfaces.
- **Linux capabilities manual page** — https://man7.org/linux/man-pages/man7/capabilities.7.html (`documentation`)
  - Documents the capability model that decomposes traditional superuser privileges.
- **Linux seccomp filter documentation** — https://docs.kernel.org/userspace-api/seccomp_filter.html (`documentation`)
  - Documents seccomp filtering as a mechanism for restricting reachable system calls.

## Orchestration integration

- **Kubernetes Container Runtime Interface** — https://kubernetes.io/docs/concepts/containers/cri/ (`documentation`)
  - Defines the kubelet-to-runtime API boundary used by Kubernetes nodes for container and image services.

## Source policy

Version-sensitive claims should be rechecked against the sources above before changing this module. Tool-specific defaults belong in their own modules unless they are needed to explain a stable container concept. Secondary tutorials and vendor marketing pages are intentionally avoided when standards or primary technical documentation explain the same behavior.
