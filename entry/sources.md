# Sources

Verified for the Docker deep-dive review on **2026-09-06**.

OpenDevIndex prefers primary documentation, specifications, and canonical repositories. Version-sensitive statements in this module should be rechecked against the upstream pages below before future edits.

## Docker architecture and Engine

- **Docker Engine documentation** — https://docs.docker.com/engine/ (`documentation`)
  - Engine scope, daemon/API model, storage, networking, runtime operations, and current platform behavior.
- **Docker architecture overview** — https://docs.docker.com/get-started/docker-overview/ (`documentation`)
  - Client/server architecture, daemon, client, registries, images, containers, and underlying container technology.
- **Moby Engine repository** — https://github.com/moby/moby (`repository`)
  - Canonical open-source engine implementation used as the source-level reference for Docker Engine internals.
- **Docker CLI repository** — https://github.com/docker/cli (`repository`)
  - Canonical source for the `docker` command-line client.

## Security and isolation

- **Docker Engine security** — https://docs.docker.com/engine/security/ (`documentation`)
  - Namespaces, cgroups, daemon attack surface, capabilities, and host hardening considerations.
- **Docker rootless mode** — https://docs.docker.com/engine/security/rootless/ (`documentation`)
  - Rootless daemon/container execution and its relationship to user namespaces.

## Storage and networking

- **Docker networking overview** — https://docs.docker.com/engine/network/ (`documentation`)
  - Container networking, user-defined networks, published ports, DNS, and driver concepts.
- **Docker storage drivers** — https://docs.docker.com/engine/storage/drivers/ (`documentation`)
  - Image/container layers, copy-on-write behavior, and classic storage-driver concepts.
- **Docker containerd image store** — https://docs.docker.com/engine/storage/containerd/ (`documentation`)
  - Current containerd-backed image storage, snapshotters, and Engine-version-sensitive defaults.

## Build and application composition

- **Docker BuildKit documentation** — https://docs.docker.com/build/buildkit/ (`documentation`)
  - Build graph execution, caching, parallelism, frontends, and modern image-build behavior.
- **Docker Compose documentation** — https://docs.docker.com/compose/ (`documentation`)
  - Multi-container application definitions, services, networks, volumes, and lifecycle commands.

## Open container standards

- **OCI Image Specification** — https://specs.opencontainers.org/image-spec/ (`standard`)
  - Image manifests, indexes, configurations, descriptors, and filesystem layers.
- **OCI Runtime Specification** — https://specs.opencontainers.org/runtime-spec/ (`standard`)
  - Runtime bundles, container configuration, lifecycle operations, and low-level runtime behavior.

## Maintenance notes

The following facts are especially likely to age and should be revalidated during future reviews:

- Docker Engine image-store defaults;
- containerd integration details;
- BuildKit/Buildx feature behavior;
- rootless-mode limitations;
- Compose capabilities;
- Docker Desktop packaging/licensing boundaries;
- supported storage/network backends and daemon configuration.

The module intentionally avoids treating secondary tutorials, marketing pages, or generated text as authority for implementation-sensitive claims.
