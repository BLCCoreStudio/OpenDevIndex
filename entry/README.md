# Containers

> Containers are an operating-system process-isolation and packaging model that combines kernel isolation, resource controls, layered images, runtime configuration, and standardized distribution workflows.

Containers are often described as “lightweight virtual machines.” That analogy is useful only at a very high level. A Linux container is normally **not a separate kernel**. It is one or more ordinary host processes whose view of the system has been constrained by kernel mechanisms such as namespaces, cgroups, capabilities, seccomp, and filesystem isolation.

This module focuses on the **container concept and its Linux implementation model**, plus the OCI standards that make images, runtimes, and registries interoperable. Docker, Podman, containerd, Kubernetes, and individual low-level runtimes are related technologies rather than synonyms for “container.”

## What is a container?

A container is a process execution environment with a deliberately restricted view of host resources and, commonly, explicit resource limits.

A useful mental model is:

```text
application process
      |
      +-- isolated process IDs
      +-- isolated mounts / root filesystem
      +-- isolated network stack
      +-- isolated hostname / IPC view
      +-- mapped users and capabilities
      +-- CPU / memory / I/O controls
      +-- syscall and security policy
      |
      v
shared host kernel
```

The process is still scheduled by the host kernel. The isolation layer changes what the process can see and do; it does not magically turn that process into a separate machine.

A practical container system usually adds several layers around this kernel model:

```text
source code
    |
    v
image builder
    |
    v
OCI image ---- push/pull ---- registry
    |
    v
runtime / container manager
    |
    v
OCI runtime bundle + config
    |
    v
isolated process tree
```

This separation explains why “container,” “image,” “runtime,” and “registry” are different objects.

## Why containers exist

Traditional application deployment often depended on reproducing machine state: package versions, runtime libraries, filesystem layout, configuration, service accounts, and startup commands. Virtual machines improved isolation and reproducibility by packaging an entire guest operating system, but a full guest kernel is unnecessary for many workloads.

Containers provide a different trade-off:

- package application user space independently from much of the host user space;
- isolate workloads from one another while sharing a kernel;
- define resource boundaries explicitly;
- create portable image artifacts;
- move those images through standardized registries;
- start and stop workloads quickly because a separate guest OS normally does not need to boot;
- give orchestration systems a consistent unit for scheduling and lifecycle management.

Containers reduce environment drift, but they do not make environments identical. Kernel version, CPU architecture, host security policy, filesystem behavior, networking, external services, secrets, and hardware still affect the running application.

## Containers are processes, not small VMs

The distinction between containers and virtual machines is architectural.

A conventional hardware virtual machine normally contains:

```text
application
  -> guest user space
  -> guest kernel
  -> virtual hardware
  -> hypervisor / host
```

A Linux container normally contains:

```text
application
  -> container user space and filesystem view
  -> host kernel
```

This gives containers several common advantages:

- lower per-workload memory overhead;
- faster process startup;
- high density on one host;
- easy sharing of immutable image layers;
- direct use of host-kernel features.

The same design creates an important security consequence: the **kernel is a shared trust boundary**. A kernel vulnerability or dangerously privileged container configuration can collapse isolation between workloads or between a workload and the host.

Virtual machines and containers are therefore complementary rather than mutually exclusive. Many production systems run containers inside virtual machines to combine image-based application packaging with a stronger hardware-virtualization boundary between tenants or clusters.

## Core objects

### Process

The running application is ultimately one or more processes. Most container lifecycle systems treat one process tree as the primary workload. The container normally stops when its designated main process exits.

This is why container design works best when lifecycle follows a real service process instead of an artificial “keep alive” loop.

### Root filesystem

The process receives a filesystem view that is usually assembled from an image plus runtime-specific writable state and mounts.

The process may see `/`, `/etc`, `/usr`, `/var`, and application paths that look like a complete machine filesystem, but those paths are a mounted view, not proof that the container owns a separate operating system.

### Image

An image is a portable artifact used to prepare a container filesystem and runtime configuration.

Under the OCI Image Specification, an image is composed from content-addressed objects including:

- a manifest;
- a configuration object;
- ordered filesystem layers;
- optionally an image index that points to platform-specific manifests.

The image describes what should be unpacked and how the workload should normally start. It is not the running container itself.

### Layer

A layer describes filesystem changes relative to earlier layers. A later layer can add, modify, or remove paths from the final merged view.

Layering enables reuse: images that share identical content-addressed layers can share stored blobs instead of duplicating them. It also creates cache behavior that strongly influences image build performance.

### Registry

A registry stores and distributes manifests and blobs. The OCI Distribution Specification standardizes important push, pull, discovery, and content-management API behavior.

A registry is not a runtime. It distributes artifacts; another component prepares and executes them.

### Runtime configuration

An OCI runtime configuration describes the execution environment of a container: process arguments, environment, mounts, namespace configuration, resources, capabilities, and platform-specific settings.

The OCI Runtime Specification standardizes configuration, state, and lifecycle operations so higher-level tools can delegate low-level container creation to compatible runtimes.

## Linux isolation primitives

Containers are assembled from multiple kernel mechanisms. No single kernel feature called “the container subsystem” creates the whole abstraction.

### Namespaces

A Linux namespace wraps a global system resource so processes in that namespace see an isolated instance or restricted view of it.

Important namespace types include:

- **PID namespace** — isolates process ID numbering and process visibility;
- **mount namespace** — isolates the mount table and filesystem mount view;
- **network namespace** — isolates network interfaces, routing tables, sockets, firewall state, and related network resources;
- **UTS namespace** — isolates hostname and NIS domain name;
- **IPC namespace** — isolates System V IPC and POSIX message-queue resources;
- **user namespace** — maps user/group IDs and capabilities across namespace boundaries;
- **cgroup namespace** — virtualizes the cgroup path view exposed to the process;
- **time namespace** — can virtualize selected clock values on supported Linux systems.

The key idea is that namespace membership changes a process's **view** of global resources.

A simple educational example on a Linux host is:

```bash
unshare --pid --fork --mount-proc sh
```

Inside the shell, the process tree is observed through a new PID namespace. This command is not a production container runtime; it demonstrates that a container's process isolation begins with ordinary kernel namespace APIs.

### PID namespace and PID 1

The first process in a PID namespace receives PID 1 within that namespace.

PID 1 has special lifecycle responsibilities, especially around signal handling and reaping orphaned child processes. Poorly designed container entrypoints can therefore leak zombie processes or handle shutdown signals incorrectly.

This is one reason production images should have a well-defined foreground process and, when necessary, a small init process designed for container workloads.

### Mount namespace

A mount namespace gives a workload its own mount table view. Container runtimes use this together with a prepared root filesystem and bind mounts to create the filesystem environment visible to the process.

Mount isolation does not by itself make host data safe. A writable bind mount intentionally exposes selected host paths to the container and can dramatically increase the impact of a compromised workload.

### Network namespace

A network namespace can have its own interfaces, routes, firewall rules, socket namespace, and protocol-stack state.

Container networking systems connect that isolated namespace to other namespaces or the host using mechanisms such as virtual Ethernet pairs, bridges, routing, overlay networks, NAT, or platform-specific datapaths.

The application sees a normal network interface; the container platform is responsible for wiring that interface into the larger network topology.

### User namespace

User namespaces allow user and group IDs to be mapped differently inside and outside the namespace.

A process can therefore appear as UID 0 inside a namespace while mapping to an unprivileged UID outside it. This is an important building block for rootless container systems and for reducing the host impact of privilege inside a container.

User namespaces do not eliminate every privilege risk. Filesystem ownership, device access, kernel attack surface, subordinate ID ranges, and integration with other namespaces still matter.

## Resource control with cgroups

Namespaces primarily isolate views. **cgroups** primarily organize processes and control resource distribution.

On modern Linux systems, cgroup v2 provides a unified hierarchy with controllers for resources such as:

- CPU;
- memory;
- I/O;
- process counts;
- cpuset placement and related resource controls.

A workload can therefore be isolated from host resource identity by namespaces while also being constrained by cgroup policy.

This distinction matters:

```text
namespace -> what can the process see?
cgroup    -> how much can the process consume?
```

Without resource controls, a correctly namespaced process can still exhaust memory, CPU, PIDs, or I/O and disrupt neighboring workloads.

### Memory limits are not memory guarantees

A configured memory limit is a boundary, not a promise of dedicated RAM. Workloads can still suffer contention, reclaim pressure, kernel memory costs, or termination when limits are exceeded.

Applications running in containers should therefore expose memory behavior and react sensibly to constrained environments instead of assuming host-sized resources are available.

### CPU limits change latency behavior

CPU quotas and shares affect scheduling rather than turning a process into a machine with a physically dedicated virtual CPU. A workload can experience throttling and latency spikes even while its nominal CPU configuration appears sufficient.

Performance testing should use the same class of resource controls intended for production.

## Capabilities, seccomp, and host security policy

Running a process as “root” is not a single all-or-nothing privilege concept on Linux.

### Capabilities

Linux capabilities divide many traditional superuser privileges into distinct units. Container runtimes commonly start workloads with a reduced capability set.

A safer design is to grant only capabilities the workload actually needs. Adding broad capabilities because an application fails to start is often a sign that the image, filesystem ownership, port configuration, or runtime policy should be fixed instead.

### seccomp

seccomp filtering can restrict the system calls a process may invoke. Container platforms commonly use seccomp profiles to reduce reachable kernel attack surface.

A seccomp profile is not an application sandbox by itself. It is one defense layer that works with namespaces, capabilities, user IDs, filesystem restrictions, and Linux Security Modules.

### SELinux and AppArmor

Host security frameworks such as SELinux and AppArmor can add mandatory access-control policy around container processes and files.

These controls are especially important because namespace isolation answers “what does the process see?” more directly than “what actions should policy allow?”

## The OCI standards model

The Open Container Initiative separates important parts of the container ecosystem into interoperable specifications.

### OCI Image Specification

The Image Specification defines the portable image format. At a high level:

```text
image index (optional)
      |
      +--> image manifest for linux/amd64
      |
      +--> image manifest for linux/arm64
                  |
                  +--> config
                  +--> layer 1
                  +--> layer 2
                  +--> ...
```

This structure supports content addressing, multi-platform images, layer reuse, and conversion from image metadata into a runnable root filesystem and configuration.

### OCI Runtime Specification

The Runtime Specification defines the configuration, execution environment, state, and lifecycle of a container from the perspective of a low-level runtime.

A higher-level manager can prepare a runtime bundle containing a root filesystem plus `config.json`, then ask an OCI runtime to create and start the container process.

### OCI Distribution Specification

The Distribution Specification defines registry API behavior for storing and retrieving content such as image manifests and blobs.

This gives the ecosystem a standard boundary between image clients and registries rather than requiring every builder or runtime to implement a registry-specific protocol.

## Runtime stack: where different tools fit

“Container runtime” is overloaded. In practice, several layers may exist:

```text
user / orchestrator
       |
       v
high-level container manager
       |
       v
container lifecycle service
       |
       v
OCI low-level runtime
       |
       v
Linux kernel
```

Examples of different roles include:

- Docker Engine — higher-level developer and engine workflow;
- Podman — daemonless container and pod management workflow;
- containerd — container lifecycle and image/runtime services;
- `runc` and similar tools — low-level OCI process runtimes;
- Kubernetes kubelet — node agent that delegates container operations through CRI.

These tools overlap in user-facing vocabulary but live at different boundaries.

## Kubernetes and CRI

Kubernetes does not require Docker Engine to run containers.

The kubelet communicates with a node container runtime through the **Container Runtime Interface (CRI)**, a gRPC API boundary for runtime and image services. A CRI-compatible runtime implementation can then manage images, sandboxes, and containers and delegate low-level execution to OCI-compatible components.

Conceptually:

```text
Kubernetes control plane
        |
      kubelet
        |
       CRI
        |
container runtime service
        |
    OCI runtime
        |
      kernel
```

This separation is important when diagnosing failures: scheduling, CRI communication, image pulling, runtime creation, networking, and application startup are distinct layers.

## Image lifecycle

A typical image-based workflow is:

1. build an image from source and build instructions;
2. produce content-addressed layers and metadata;
3. assign one or more human-readable tags;
4. push manifests and blobs to a registry;
5. pull the image on a target host;
6. verify and unpack the image content;
7. create runtime configuration and mounts;
8. start the isolated process;
9. observe, stop, replace, or delete the runtime instance.

### Tags versus digests

Tags are convenient mutable names. Digests identify specific content.

A deployment that requires immutability should not assume that a tag such as `latest` or even a version-looking tag can never move. Content digests provide a stronger identity for exactly what was pulled.

### Multi-platform images

An OCI image index can reference different manifests for different operating systems and CPU architectures.

This lets one image reference resolve to an appropriate platform-specific image, but it does not make arbitrary binaries portable across CPU architectures. Each referenced image still has platform constraints.

## Filesystem and storage model

### Immutable image, mutable runtime

Images are treated as immutable artifacts. A running container usually adds a writable runtime layer or snapshot above the image's prepared filesystem.

That writable layer is generally ephemeral. Persistent application state should be placed on storage whose lifecycle is explicit and independent from the disposable container instance.

### Copy-on-write

Layered filesystems and snapshotters commonly use copy-on-write techniques. Reading unchanged image content can be efficient and shared; modifying files can require copy-up or new snapshot state.

This is excellent for application binaries and configuration-like files, but write-heavy databases often need purpose-designed persistent storage rather than relying on the container's ephemeral writable layer.

### Bind mounts

A bind mount maps a host path into the container.

Bind mounts are powerful because they give direct host integration. They are also a security and portability boundary because host path layout, permissions, labels, ownership, and mount options become part of application behavior.

### Volumes and orchestrated storage

Higher-level platforms commonly provide named volumes, persistent-volume abstractions, CSI-backed storage, or platform-specific persistent disk services.

The important principle is lifecycle separation:

```text
container process -> disposable
persistent data   -> independently managed
```

Deleting a workload should not accidentally be the only thing protecting or identifying business-critical data.

## Networking model

A container normally receives an isolated network namespace, but connectivity is provided by the surrounding platform.

Common pieces include:

- virtual Ethernet interfaces;
- bridges or routed networking;
- DNS/service discovery;
- port publication or load balancing;
- firewall and policy rules;
- overlay or underlay integration;
- orchestration plugins such as CNI implementations.

A container port is not automatically reachable from the host or external network. Exposure is a separate configuration decision.

### Service identity should not depend on container IPs

Container instances are replaceable, and their addresses may change. Distributed systems should generally rely on service discovery, stable names, load balancers, or orchestration abstractions instead of storing ephemeral container IP addresses as durable configuration.

## Container lifecycle

The OCI Runtime Specification models explicit lifecycle operations such as create, start, kill, and delete.

Higher-level platforms add policies around those primitives:

- restart on failure;
- health checks;
- rolling replacement;
- replica counts;
- readiness gates;
- graceful shutdown windows;
- rescheduling to another host.

A container runtime can successfully start a process while the application is still unhealthy. Runtime success and service readiness are different states.

## Signals and graceful shutdown

Containerized applications need to handle termination predictably.

Common shutdown problems include:

- shell entrypoints that do not forward signals;
- PID 1 processes that do not reap children;
- applications that ignore termination and are force-killed;
- shutdown hooks that exceed orchestration deadlines;
- stateful services that do not flush or checkpoint safely.

A reliable image should make the intended foreground process explicit and test shutdown behavior under the actual runtime or orchestrator.

## Observability

Containers add useful metadata but also add another diagnostic boundary.

Operational investigation usually needs both application and platform signals:

- stdout/stderr or structured logs;
- process exit codes;
- restart counts;
- CPU, memory, I/O, and network metrics;
- cgroup throttling or memory-pressure indicators;
- image digest and deployment revision;
- runtime events;
- node/kernel logs;
- network policy and DNS behavior;
- storage and mount state.

A container that repeatedly restarts may look like an application failure while the actual cause is memory pressure, missing storage, denied syscalls, a bad image architecture, or an unreachable registry dependency.

## Security model

Containers are a composition of isolation mechanisms, not an absolute sandbox guarantee.

A strong baseline includes:

- run as a non-root user where practical;
- use user namespaces or rootless operation when compatible;
- drop unneeded capabilities;
- apply seccomp and host mandatory-access-control policy;
- avoid privileged mode;
- avoid exposing runtime control sockets to workloads;
- mount filesystems read-only where possible;
- make writable host mounts narrow and explicit;
- set CPU, memory, PID, and I/O controls;
- keep host kernels and runtimes patched;
- use minimal, maintained base images;
- verify image provenance and vulnerability posture;
- protect registry credentials and signing keys;
- treat secrets as runtime data rather than baking them into image layers.

### Privileged containers

A privileged container deliberately disables or weakens many normal isolation boundaries. It should be treated as host-level authority for threat-model purposes unless a platform-specific design proves otherwise.

“Runs in a container” does not make privileged software low risk.

### Runtime sockets are high-value control interfaces

Mounting a Docker, containerd, or equivalent control socket into a workload can allow that workload to create or manipulate other containers and, depending on the runtime, gain effective host control.

Such sockets should not be exposed merely for convenience.

### Supply-chain security

An image can be perfectly isolated at runtime and still contain vulnerable or malicious software.

Container security therefore spans:

```text
source -> build -> dependencies -> image -> registry -> deployment -> runtime -> host
```

Digest pinning, signatures/attestations, SBOMs, vulnerability analysis, protected build infrastructure, and registry authorization address different points in that chain.

## Performance characteristics

Containers do not inherently make an application faster. They primarily change packaging, isolation, and resource management.

### Startup

Starting an isolated process is normally much faster than booting a full guest operating system, which makes rapid scaling and replacement practical.

Image pull and unpack time can still dominate cold starts. Large images, slow registries, signature verification, decompression, and storage backends all influence startup latency.

### CPU

CPU execution is generally close to normal host-process execution because instructions run directly on the host CPU. Scheduling policy, quotas, virtualization underneath the host, emulation, and security instrumentation can still affect performance.

### Memory

Containers avoid a separate guest kernel per workload, but application memory is still real host memory. Page cache behavior, shared libraries, cgroup accounting, and memory limits affect density and latency.

### Storage

Layered filesystems improve reuse and distribution efficiency, but copy-on-write behavior may penalize write-heavy or metadata-heavy workloads. Persistent databases should be benchmarked on the actual storage path used in production.

### Networking

Bridge, NAT, overlay, encryption, service-mesh proxies, firewall rules, and cross-host encapsulation can add latency or CPU cost. Network performance is therefore a property of the complete platform, not the namespace abstraction alone.

## Reliability and common failure modes

### Image pull failures

Causes include:

- registry outage;
- authentication failure;
- missing tag or digest;
- rate limiting;
- DNS or TLS failure;
- platform mismatch.

The fix depends on the registry and node path, not on application code inside the image.

### Main process exits immediately

Typical causes include invalid command configuration, missing files, permissions, architecture mismatch, or application startup failure.

The first useful artifacts are normally the process exit code, runtime logs, and the exact image digest.

### OOM termination

A workload may exceed its cgroup memory boundary even though the host still has free memory outside that cgroup.

Investigate actual working-set behavior, limit configuration, application heap settings, page cache, and orchestrator resource policy.

### CPU throttling

A service can be healthy but slow because its cgroup CPU quota is being exhausted. High request latency with low apparent host-wide CPU usage can therefore still be a container resource problem.

### Disk exhaustion

Image layers, writable snapshots, build caches, logs, and persistent volumes can fill different filesystems. Monitoring only the application volume is insufficient.

### Permission failures

User mappings, host filesystem ownership, SELinux/AppArmor labels, read-only mounts, capabilities, and rootless runtime behavior can all surface as ordinary “permission denied” errors.

### Network confusion

Common mistakes include assuming localhost refers to the host, embedding container IP addresses, publishing a port on the wrong interface, or overlooking DNS and network policy.

Inside a network namespace, `127.0.0.1` refers to that namespace's loopback interface, not automatically to the host or a sibling container.

### Mutable deployment references

Reusing mutable tags can make two nodes run different image content under the same human-readable name. Production systems that need exact reproducibility should record deployed digests.

## Common conceptual mistakes

### “A container is an image”

An image is an artifact. A container is a runtime instance prepared from image content plus runtime configuration.

### “A container has its own kernel”

A normal Linux container shares the host kernel. User space may look like another distribution, but system calls ultimately reach the host kernel.

### “Root inside a container is harmless”

Root may be constrained by namespaces, capabilities, and policy, but it remains more dangerous than a deliberately unprivileged process. Configuration determines the real boundary.

### “Namespaces automatically limit resources”

They do not. Resource controls are primarily provided by cgroups and related scheduler/kernel mechanisms.

### “Deleting the container deletes all application data”

Only ephemeral writable state normally follows container lifecycle. Volumes and external storage can outlive the container, which is exactly what persistent workloads need.

### “Container portability means identical behavior everywhere”

Images improve portability but do not abstract away CPU architecture, kernel features, security policy, storage, networking, or external dependencies.

### “Kubernetes runs Docker containers”

Kubernetes runs containerized workloads through CRI-compatible runtime services. Docker-built OCI-compatible images remain usable, but Docker Engine is not the required node runtime abstraction.

## When containers are a strong fit

Containers are especially useful when a workload benefits from:

- reproducible application packaging;
- CI/CD artifact promotion;
- high-density service hosting;
- rapid replacement and horizontal scaling;
- isolated development/test environments;
- standardized image distribution;
- orchestration across many workloads;
- immutable-infrastructure practices.

## When containers may be the wrong abstraction

Containers can be inappropriate or unnecessary when:

- the workload needs a different kernel from the host;
- a hardware-virtualization boundary is required between mutually hostile tenants;
- the application requires deep host integration that defeats isolation;
- the operational platform is simpler and safer without an image/runtime layer;
- extremely specialized real-time or device constraints conflict with the runtime stack;
- the team cannot operate the registry, runtime, observability, security, and storage layers the container platform introduces.

Using containers is an architectural choice, not a maturity badge.

## Ecosystem map

Important neighboring technologies include:

- **Docker** — developer-facing build, image, runtime, networking, storage, and Compose workflows;
- **Podman** — daemonless container and pod management with OCI interoperability;
- **containerd** — container lifecycle and image/runtime services used directly and by larger platforms;
- **runc** — widely used low-level OCI runtime implementation;
- **Kubernetes** — orchestration platform that schedules containerized workloads;
- **CRI implementations** — bridge kubelet requests to runtime/image services;
- **CNI implementations** — provide container/pod network integration;
- **CSI implementations** — connect orchestrated workloads to persistent storage;
- **OCI registries** — distribute manifests and blobs;
- **BuildKit and other builders** — produce OCI-compatible image content.

The ecosystem is intentionally layered. Troubleshooting becomes much easier when a problem is assigned to the correct layer instead of treating the entire stack as “Docker” or “Kubernetes.”

## Learning path

A practical progression is:

1. learn Linux processes, filesystems, signals, users, and permissions;
2. understand namespaces and cgroups;
3. distinguish image, container, registry, and runtime;
4. study OCI Image and Runtime concepts;
5. use a higher-level tool such as Docker or Podman;
6. inspect images, mounts, namespaces, and resource limits directly;
7. learn container networking and persistent storage;
8. study security boundaries: capabilities, user namespaces, seccomp, SELinux/AppArmor;
9. learn containerd/OCI runtime layering;
10. then study orchestration through Kubernetes, CRI, CNI, and CSI.

Learning the kernel and OCI model first prevents many tool-specific misconceptions.

## What to learn next

Recommended OpenDevIndex neighbors:

- `tool/docker` — developer and engine workflows built around containers;
- `tool/containerd` — lower-level container lifecycle and image services;
- `tool/podman` — alternative container-management model;
- `cloud/kubernetes` — scheduling and orchestration of containerized workloads;
- `opensource/linux-kernel` — the kernel primitives that underpin Linux containers.

## Authoritative sources

Primary references for this module include:

- Open Container Initiative — https://opencontainers.org/
- OCI Image Specification — https://specs.opencontainers.org/image-spec/
- OCI Runtime Specification — https://specs.opencontainers.org/runtime-spec/
- OCI Distribution Specification — https://specs.opencontainers.org/distribution-spec/
- Linux namespaces manual page — https://man7.org/linux/man-pages/man7/namespaces.7.html
- Linux user namespaces manual page — https://man7.org/linux/man-pages/man7/user_namespaces.7.html
- Linux cgroup v2 documentation — https://docs.kernel.org/admin-guide/cgroup-v2.html
- Linux capabilities manual page — https://man7.org/linux/man-pages/man7/capabilities.7.html
- Linux seccomp userspace API documentation — https://docs.kernel.org/userspace-api/seccomp_filter.html
- Kubernetes Container Runtime Interface — https://kubernetes.io/docs/concepts/containers/cri/

## Verification and maintenance

This module was reviewed on **2026-09-05** against current OCI specifications, Linux kernel/man-pages documentation, and Kubernetes CRI documentation.

Facts most likely to age are implementation details around runtime stacks, orchestration integrations, kernel features, security defaults, and supported OCI capabilities. The stable mental model—isolated processes sharing a host kernel, explicit resource control, image/runtime/distribution separation, and layered security boundaries—should remain the anchor when those implementation details change.
