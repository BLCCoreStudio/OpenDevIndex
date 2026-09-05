# Docker

> Docker is a container development platform and engine ecosystem for building OCI-compatible images, running isolated processes, managing networks and volumes, and packaging reproducible application environments.

Docker is often introduced as a command that “runs containers,” but that description hides the system model that makes Docker useful. A practical understanding requires separating the CLI, daemon, image builder, image store, runtime, registry, networking, storage, and operating-system isolation primitives.

This module focuses primarily on **Docker Engine, the Docker CLI, Docker Build/BuildKit, and Docker Compose**. Docker Desktop packages several of these components for desktop operating systems and has its own product and licensing considerations.

## What is Docker?

Docker provides a workflow for turning application files and dependencies into **images**, distributing those images through registries, and starting **containers** from them.

A container is not a miniature virtual machine. On Linux, it is fundamentally one or more host processes executed with isolation and resource-control mechanisms such as namespaces, cgroups, capabilities, and security policy. The container sees an isolated view of resources, but it still uses the host kernel.

The most useful first approximation is:

```text
source + Dockerfile
        |
        v
   Docker Build
        |
        v
      image  ----push/pull----> registry
        |
        v
   docker run
        |
        v
    container
  (isolated process)
```

Docker adds developer ergonomics, image tooling, APIs, networking, storage abstractions, lifecycle management, and integration around this operating-system container model.

## Why Docker exists

Before image-based container workflows became common, deployment frequently depended on manually reproducing machine state: package versions, system libraries, configuration, filesystem layout, and service setup.

Docker popularized a more portable packaging model:

- define an image build in source control;
- produce a versionable artifact;
- move the same image between developer machines, CI, staging, and deployment systems;
- isolate application processes from much of the host user space;
- attach explicit networking and persistent storage;
- automate lifecycle operations through a stable CLI and API.

This does not make every environment identical. Kernel behavior, CPU architecture, host security policy, storage backend, network configuration, secrets, and external services still matter. Docker reduces a large class of environment drift; it does not eliminate infrastructure differences.

## Core mental model

Four objects explain most day-to-day Docker behavior.

### Image

An **image** is an immutable, content-addressed package describing a root filesystem plus runtime configuration such as default command, environment, working directory, and metadata.

Images are composed from filesystem layers and configuration objects. Modern Docker image workflows interoperate with the OCI Image Specification.

### Container

A **container** is a runtime instance created from an image plus additional runtime configuration.

The image remains immutable. Writes made inside a normal container go to a container-specific writable layer or to mounted storage. Deleting the container removes that ephemeral writable layer, but named volumes remain unless explicitly removed.

### Registry

A **registry** stores and distributes image content. Image names such as `example/app:1.4` are human-friendly references; the underlying manifests and blobs are content-addressed.

### Docker host

The **Docker host** runs the engine components and the container processes. A client can control a local host or, when configured securely, a remote daemon.

## Client-server architecture

Docker Engine uses a client-server design.

```text
docker CLI / Compose / API client
             |
             | Docker API
             v
          dockerd
      /      |       \
 images   networks   volumes
      \      |       /
        containerd
             |
         OCI runtime
             |
       host processes
```

The main components are:

- **`docker` CLI** — translates user commands into Docker API requests.
- **`dockerd`** — the Docker daemon that manages engine objects and orchestration of lower-level components.
- **containerd** — manages container lifecycle and image-related runtime services used by Docker Engine.
- **OCI runtime** — a low-level runtime, commonly `runc` on Linux, that creates the container process according to OCI runtime configuration.
- **BuildKit** — the modern build backend used for image builds.
- **registries** — external or local services that store image manifests and blobs.

The exact implementation evolves. For example, current Docker Engine releases can use containerd both for runtime lifecycle and for the image store. On fresh Docker Engine 29.0+ installations, the containerd image store is the default, while upgraded installations may continue using classic storage drivers until migrated.

## Docker Engine versus containerd versus runc

These layers are related but solve different problems.

### Docker Engine

Docker Engine provides the developer-facing API, object model, image operations, networking, volumes, build integration, and higher-level lifecycle behavior expected by Docker users.

### containerd

containerd is a general container runtime daemon and API. Docker Engine uses it under the hood rather than reimplementing the full low-level container lifecycle itself.

### runc and other OCI runtimes

A low-level OCI runtime receives an OCI runtime bundle/configuration and creates the actual isolated process. `runc` is the most common example, but the OCI runtime interface can support alternative runtimes with different isolation models.

A useful boundary is:

```text
Docker UX/API -> container lifecycle service -> OCI process runtime -> kernel
```

## Images, layers, and content addressing

Container images are not single opaque disk images. They are assembled from content-addressed objects.

An OCI-compatible image normally includes:

- an image manifest;
- an image configuration object;
- ordered filesystem layers;
- optionally an image index that points to platform-specific image manifests.

Layers represent filesystem changes. If two images share the same content-addressed layer, the underlying blob can be reused instead of stored repeatedly.

### Image tags are references, not identities

A tag such as `latest` or `1.2` is a mutable name. It can later point to different content.

A digest such as a `sha256:` image digest identifies specific content. For environments where exact reproducibility matters, pinning image references by digest provides stronger guarantees than relying only on mutable tags.

### Multi-platform images

An image index can reference different manifests for architectures or operating systems. A registry can therefore expose one logical image name while clients select a compatible platform-specific image.

This is one reason modern image storage needs to understand manifests, indexes, attestations, and content metadata rather than only filesystem layers.

## Building images: Dockerfile, Buildx, and BuildKit

A **Dockerfile** describes image construction in a readable build language. A typical example is intentionally small:

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

The important idea is not the syntax; it is the transformation from a build context and instructions into an image graph.

Modern Docker builds use **Buildx** as the CLI-facing build interface and **BuildKit** as the build backend. BuildKit improves the older sequential builder model with features such as:

- parallel execution of independent build stages;
- avoiding unused stages;
- incremental transfer of changed build context;
- cache mounts and external cache import/export;
- secret and SSH mounts that do not need to be baked into image layers;
- multi-platform build workflows;
- richer frontends and low-level build graph execution.

### Multi-stage builds

Multi-stage Dockerfiles let a build use heavy toolchains without copying them into the final runtime image.

```dockerfile
FROM golang:1.25 AS build
WORKDIR /src
COPY . .
RUN CGO_ENABLED=0 go build -o /out/app ./cmd/app

FROM scratch
COPY --from=build /out/app /app
ENTRYPOINT ["/app"]
```

This separates **build environment** from **runtime artifact** and is one of the most effective ways to reduce image size and attack surface.

### Build cache is part of the performance model

Layer and BuildKit caches can make builds dramatically faster, but cache behavior depends on instruction order and inputs. Frequently changing files should not invalidate expensive dependency-installation steps unnecessarily.

A common pattern is therefore to copy dependency manifests first, install dependencies, and only then copy the rest of the source tree.

## Container creation and runtime lifecycle

When a user runs:

```bash
docker run --name web -p 8080:8080 example/web:1.0
```

Docker conceptually performs several steps:

1. resolve the image reference;
2. pull missing image content if necessary;
3. create container metadata and a writable layer/snapshot;
4. configure mounts, networking, environment, namespaces, cgroups, capabilities, and security settings;
5. ask lower-level runtime components to create and start the process;
6. attach logging and lifecycle tracking;
7. expose published ports according to the selected network configuration.

The container stops when its main process exits unless restart policy or a higher-level orchestrator starts it again.

This is why “keeping a container alive” by running an artificial shell loop is usually the wrong mental model. The container lifecycle should normally follow the lifecycle of the service process it exists to run.

## Linux isolation model

Docker containers rely heavily on kernel facilities.

### Namespaces

Namespaces isolate views of resources such as:

- process IDs;
- networking;
- mounts;
- hostnames;
- users;
- IPC resources.

A process inside a container can therefore see a restricted process tree and network namespace even though it is still a host process.

### Control groups

**cgroups** account for and limit resources such as CPU and memory. Resource constraints are operationally important because isolation without limits can allow one workload to starve others.

Example:

```bash
docker run --memory=512m --cpus=1.5 example/worker
```

### Capabilities and security profiles

Linux root privileges are split into capabilities. Docker drops many capabilities by default, and operators can remove more.

```bash
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE example/web
```

Other host security mechanisms such as seccomp, AppArmor, and SELinux can add policy boundaries.

Containers should therefore be treated as **process isolation**, not as an unconditional security boundary equivalent to a hardware virtual machine.

## Rootless mode and user namespaces

Traditional Docker Engine operation runs `dockerd` with root privileges. Access to its control socket is consequently highly privileged.

**Rootless mode** runs both the Docker daemon and containers inside a user namespace as a non-root user, reducing the impact of daemon or runtime compromise.

This differs from `userns-remap`, where the daemon still runs with root privileges while container user IDs are remapped.

Rootless operation has trade-offs and compatibility constraints, but it is an important option for systems where minimizing host-level daemon privilege matters.

## Storage model

Docker has three storage concepts that should not be confused.

### Image/container layer storage

The engine stores image content and container filesystem snapshots through its image-storage backend.

On current fresh Docker Engine 29.0+ installations, the **containerd image store** is the default and uses containerd snapshotters. Older or upgraded installations may still use classic storage drivers such as `overlay2`.

The storage backend is an implementation detail that can materially affect features and performance.

### Volumes

**Volumes** are Docker-managed persistent storage intended to outlive a container.

```bash
docker volume create db-data
docker run -v db-data:/var/lib/postgresql/data postgres
```

Volumes are generally the cleanest default for persistent application state that Docker should manage.

### Bind mounts

A **bind mount** exposes a specific host path inside the container.

```bash
docker run --mount type=bind,src="$PWD",dst=/workspace example/dev
```

Bind mounts are useful for development and host integration, but they couple the container to host filesystem layout and permissions. Writable bind mounts also intentionally weaken filesystem isolation because the container can change mounted host data according to host permissions.

### Writable container layer

Writing directly into the container's writable layer is appropriate for ephemeral state but is usually a poor choice for databases or durable application data.

Copy-on-write behavior can also make some write-heavy workloads less efficient than purpose-built volumes or host storage.

## Networking

A container normally gets its own network namespace with interfaces, routes, and DNS configuration.

Docker provides several network drivers and abstractions. The most common local Linux workflow uses bridge networking.

### User-defined networks

A user-defined network provides an explicit connectivity boundary and built-in service-name discovery between attached containers.

```bash
docker network create app-net
docker run -d --name db --network app-net postgres
docker run -d --name api --network app-net example/api
```

The `api` container can resolve `db` through Docker-provided DNS behavior on the network.

### Published ports

A container port is not automatically a host port.

```bash
docker run -p 127.0.0.1:8080:8080 example/web
```

publishes the container's port 8080 on host loopback port 8080.

Binding to `0.0.0.0` or omitting an address can expose the port on external host interfaces depending on platform and firewall configuration. Port publication should therefore be treated as a security decision, not merely convenience syntax.

## Docker Compose

Docker Compose defines a multi-container application declaratively.

A small `compose.yaml` might describe services, networks, and volumes:

```yaml
services:
  api:
    build: .
    ports:
      - "8080:8080"
    depends_on:
      - db
  db:
    image: postgres:17
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  db-data:
```

Then:

```bash
docker compose up -d
docker compose ps
docker compose logs -f
docker compose down
```

Compose is especially useful for local development, integration testing, demos, and smaller deployment environments where a full cluster orchestrator is unnecessary.

Compose should not be confused with Kubernetes. Both can describe multi-service systems, but their scheduling, reconciliation, networking, availability, and cluster-management models are different.

## Common workflows

### Build and run locally

```bash
docker build -t example/api:dev .
docker run --rm -p 8080:8080 example/api:dev
```

### Inspect a running container

```bash
docker ps
docker inspect <container>
docker logs <container>
docker stats <container>
```

### Execute a diagnostic command

```bash
docker exec -it <container> sh
```

`docker exec` is useful for diagnosis but should not become a hidden configuration mechanism. Durable configuration belongs in images, environment/config systems, mounted files, or deployment definitions.

### Push an image

```bash
docker tag example/api:dev registry.example.com/team/api:1.4.0
docker push registry.example.com/team/api:1.4.0
```

Production pipelines commonly add provenance, vulnerability scanning, signing/attestation, and immutable digest tracking around this step.

### Clean unused objects carefully

```bash
docker system df
docker image prune
docker container prune
```

Broad prune commands can delete cached or stopped resources you still need. Inspect usage before cleanup on shared or production hosts.

## Configuration and daemon state

On Linux, Docker daemon configuration is commonly stored in `/etc/docker/daemon.json`, though service-manager flags and platform-specific configuration also exist.

The daemon persists engine state under its data directory. With the current containerd image store, image content and snapshots can be stored under containerd's data root while other Docker state remains under Docker's data root.

This distinction matters during backup, migration, disk-capacity planning, and incident recovery. Copying only one directory is not automatically a valid backup strategy for every Engine configuration.

## Reliability and failure modes

Containers make process packaging repeatable; they do not automatically make services reliable.

Common failure modes include:

### The main process exits

The container stops because its primary process exited. Inspect:

```bash
docker ps -a
docker logs <container>
docker inspect <container>
```

A restart policy can restart a failed process, but it does not fix persistent application or dependency failures.

### Disk exhaustion

Images, stopped containers, build cache, logs, and writable layers can consume significant disk space.

Useful investigation starts with:

```bash
docker system df
```

Production hosts should monitor both Docker/containerd storage and filesystem capacity rather than relying on manual pruning.

### Permission problems on mounted data

UID/GID differences between container and host commonly break bind mounts or persistent volumes. Fixing permissions by running everything as root usually creates a larger security problem.

### DNS or network assumptions

Container addresses can change. Prefer stable service discovery through names and orchestration/network abstractions rather than embedding ephemeral IP addresses.

### Architecture mismatch

An image built only for `linux/amd64` does not automatically run natively on `linux/arm64`. Multi-platform indexes and Buildx can solve distribution, while emulation may be available with performance and compatibility costs.

### Hidden mutable dependencies

Unpinned base-image tags, package repositories, downloaded installers, and network-fetched build inputs can change even when the Dockerfile does not. Reproducible builds require controlling those inputs, not merely committing a Dockerfile.

## Security model

Docker security starts with the fact that the daemon and container runtime control host resources.

### Treat Docker daemon access as privileged

On a traditional rootful Engine, access to the Docker socket effectively grants extremely powerful host control. A user who can ask the daemon to create privileged containers or bind-mount sensitive host paths can often obtain host-level access.

For this reason:

- restrict access to the daemon socket;
- do not expose the daemon API over an unauthenticated network endpoint;
- prefer SSH or properly authenticated TLS for remote daemon access;
- understand that membership in the `docker` group on Linux is effectively root-equivalent for many threat models.

### Avoid unnecessary privilege

High-risk options include:

```text
--privileged
--pid=host
--network=host
--cap-add=ALL
-v /:/host
-v /var/run/docker.sock:/var/run/docker.sock
```

These options can be valid for specific infrastructure tooling, but they deliberately remove important isolation boundaries.

### Run application processes as non-root

A non-root user inside the container reduces the blast radius of many application compromises.

Dockerfile example:

```dockerfile
RUN useradd --system --uid 10001 appuser
USER 10001
```

This is not a complete sandbox by itself, but it is a useful defense-in-depth measure.

### Minimize image contents

Smaller runtime images reduce unnecessary packages, shells, compilers, and tools that can expand attack surface.

Multi-stage builds, explicit dependency installation, read-only filesystems where practical, and dropping capabilities all contribute to hardening.

### Protect secrets during builds

Do not pass secrets through Dockerfile `ARG` or bake credentials into image layers. Use BuildKit secret mounts or external secret-management mechanisms designed not to persist the secret in the resulting image.

### Images are supply-chain artifacts

An image can include vulnerable packages, malicious binaries, or outdated dependencies. Security programs should treat images like other software supply-chain artifacts: identify provenance, scan contents, pin trusted sources, review base images, and verify deployment policy.

## Performance characteristics

Docker overhead is usually dominated by workload and host configuration rather than “containerization” as one fixed cost.

Important factors include:

- filesystem backend and copy-on-write behavior;
- bind mounts versus volumes;
- number and size of image layers;
- image pull latency and registry locality;
- build-cache hit rate;
- build-context size;
- CPU and memory limits;
- network mode and packet-processing path;
- logging driver and log volume;
- architecture emulation for cross-platform workloads.

For build performance, BuildKit cache structure and Dockerfile ordering often matter more than micro-optimizing individual shell commands.

For runtime performance, persistent databases and write-heavy services deserve careful storage benchmarking rather than assuming the container writable layer is suitable.

## Observability

Docker exposes several useful diagnostic surfaces:

```bash
docker stats
docker logs
docker inspect
docker events
docker system df
docker info
```

These answer different questions:

- `stats` — current resource usage;
- `logs` — configured container stdout/stderr collection;
- `inspect` — object configuration and runtime metadata;
- `events` — lifecycle activity;
- `system df` — Docker-managed disk usage;
- `info` — daemon-wide runtime/storage/configuration information.

In production, container-level metrics should be integrated with host, application, and orchestrator telemetry. A healthy container process does not guarantee a healthy service.

## Docker and Kubernetes

Docker and Kubernetes occupy different layers.

Docker is primarily a container build/runtime/developer workflow. Kubernetes is a cluster orchestration platform that reconciles desired application state across nodes.

Kubernetes no longer requires Docker Engine as a node runtime, but Docker-built OCI-compatible images remain normal Kubernetes deployment artifacts.

This distinction matters because “Kubernetes removed Docker” did **not** mean Kubernetes stopped running container images built with Docker. The change concerned the runtime integration layer on Kubernetes nodes.

## Alternatives

### Podman

[Podman](https://github.com/BLCCoreStudio/OpenDevIndex/tree/tool/podman/entry) provides an OCI-focused CLI and container workflow with a daemonless architecture and strong rootless support. It is the closest direct alternative for many local and server container tasks.

### containerd + nerdctl

[containerd](https://github.com/BLCCoreStudio/OpenDevIndex/tree/tool/containerd/entry) can be used more directly with tooling such as `nerdctl` when operators want a containerd-native workflow without Docker Engine's higher-level daemon/API model.

### Kubernetes and other orchestrators

[Kubernetes](https://github.com/BLCCoreStudio/OpenDevIndex/tree/cloud/kubernetes/entry) is not a drop-in Docker replacement. It solves cluster scheduling, service discovery, rollout, reconciliation, and resilience problems beyond a single Docker host.

### Virtual machines

Virtual machines provide a stronger kernel isolation boundary because workloads normally run their own guest kernels. They cost more in startup time, memory, storage, and management overhead, but can be preferable for hostile multi-tenancy or workloads that require different kernels.

## Trade-offs

### Strengths

- widely understood container workflow and API;
- strong developer ergonomics;
- OCI-compatible image ecosystem;
- efficient local image/layer reuse;
- BuildKit-based build caching and multi-platform support;
- mature registry, CI/CD, IDE, and cloud integrations;
- Compose for approachable multi-service environments;
- broad operational tooling and documentation.

### Costs

- traditional `dockerd` is a highly privileged daemon and must be protected carefully;
- container isolation shares the host kernel and is not equivalent to VM isolation;
- storage/network behavior can vary by host platform and backend;
- mutable tags and network-dependent builds can create false confidence in reproducibility;
- bind mounts and Docker socket mounts can intentionally bypass important isolation;
- large image graphs and build caches can create substantial storage pressure;
- Docker Desktop, Docker Engine, CLI, Compose, Buildx, BuildKit, containerd, and registry concepts can blur together for new users even though they have distinct responsibilities.

## Common mistakes

- Treating a container as a lightweight VM that should run many unrelated system services.
- Persisting database state only in the container writable layer.
- Using `latest` as if it were an immutable version.
- Copying secrets into build layers.
- Mounting the Docker socket into ordinary application containers.
- Running with `--privileged` to bypass a permissions problem without understanding the missing capability or device access.
- Assuming a Dockerfile alone guarantees reproducible builds.
- Publishing every container port to all host interfaces.
- Using container IP addresses as stable service identifiers.
- Ignoring UID/GID ownership on bind-mounted files.
- Confusing Docker image portability with cross-architecture binary portability.
- Expecting restart policies to provide the same availability model as a multi-node orchestrator.

## Ecosystem

Docker connects several standards and projects:

- **OCI Image Specification** — interoperable image manifests, indexes, configurations, and layers.
- **OCI Runtime Specification** — low-level container execution model.
- **containerd** — runtime lifecycle and image services beneath Docker Engine.
- **runc** — common OCI low-level runtime on Linux.
- **BuildKit** — build execution engine.
- **Buildx** — build CLI/frontend integration.
- **Compose** — multi-container application definition and lifecycle.
- **registries** — Docker Hub, cloud registries, and self-hosted OCI-compatible registries.
- **Kubernetes** — common deployment target for OCI images built by Docker workflows.
- **Linux kernel** — namespaces, cgroups, capabilities, networking, and filesystem primitives that make Linux containers possible.

## Related OpenDevIndex modules

- [`concept/containers`](https://github.com/BLCCoreStudio/OpenDevIndex/tree/concept/containers/entry) — the underlying container model independent of Docker product boundaries.
- [`tool/containerd`](https://github.com/BLCCoreStudio/OpenDevIndex/tree/tool/containerd/entry) — runtime lifecycle layer used by Docker Engine.
- [`tool/podman`](https://github.com/BLCCoreStudio/OpenDevIndex/tree/tool/podman/entry) — closely related alternative developer/runtime workflow.
- [`cloud/kubernetes`](https://github.com/BLCCoreStudio/OpenDevIndex/tree/cloud/kubernetes/entry) — cluster orchestration and a major target for OCI images.
- [`opensource/linux-kernel`](https://github.com/BLCCoreStudio/OpenDevIndex/tree/opensource/linux-kernel/entry) — kernel isolation and resource-control primitives used by Linux containers.

## Learning path

A practical progression is:

1. Understand processes, filesystems, ports, and basic Linux permissions.
2. Build and run one image with a small Dockerfile.
3. Learn the distinction between image, container, registry, volume, and network.
4. Understand layers, tags, digests, and build cache.
5. Use Compose for a multi-service application.
6. Learn bind mounts versus volumes and user/permission mapping.
7. Learn namespaces, cgroups, capabilities, seccomp, and rootless mode.
8. Inspect containerd/OCI boundaries so Docker internals stop looking like one monolithic daemon.
9. Learn image provenance, vulnerability scanning, signing/attestation, and secret-safe builds.
10. Move to Kubernetes or another orchestrator only when multi-node scheduling/reconciliation problems justify it.

## What to learn next

For architecture depth, continue with `concept/containers`, `tool/containerd`, and the Linux kernel. For production deployment, continue with Kubernetes, registry security, image supply-chain practices, and observability.

## Authoritative sources

Primary references used for this module include:

- [Docker Engine documentation](https://docs.docker.com/engine/)
- [Docker architecture overview](https://docs.docker.com/get-started/docker-overview/)
- [Docker Engine security](https://docs.docker.com/engine/security/)
- [Rootless mode](https://docs.docker.com/engine/security/rootless/)
- [Docker networking](https://docs.docker.com/engine/network/)
- [Docker storage drivers](https://docs.docker.com/engine/storage/drivers/)
- [containerd image store](https://docs.docker.com/engine/storage/containerd/)
- [BuildKit](https://docs.docker.com/build/buildkit/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Moby Engine source](https://github.com/moby/moby)
- [Docker CLI source](https://github.com/docker/cli)
- [OCI Image Specification](https://specs.opencontainers.org/image-spec/)
- [OCI Runtime Specification](https://specs.opencontainers.org/runtime-spec/)

## Verification and maintenance

This deep dive was reviewed on **2026-09-06** against current Docker documentation and OCI specifications.

The most version-sensitive areas are:

- Docker Engine storage defaults and containerd integration;
- BuildKit/Buildx capabilities;
- Docker Desktop packaging and licensing;
- supported daemon/security configuration;
- Compose functionality;
- runtime defaults and supported host platforms.

Those claims should be rechecked against current upstream documentation during future reviews. The durable concepts—images, containers, content-addressed distribution, daemon/API boundaries, OS-level isolation, explicit networking, and persistent storage—should remain the primary mental model even as implementation details evolve.
