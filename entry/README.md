# containerd

> containerd is a container lifecycle daemon and API that manages content, images, snapshots, containers, tasks, runtimes, and plugins beneath higher-level platforms such as Docker and Kubernetes.

containerd occupies a layer that is easy to misunderstand. It is not primarily a developer-facing application platform, and it is not itself the low-level OCI process runtime. It is the long-running service between higher-level systems and lower-level runtime/storage components.

A useful first approximation is:

```text
Docker Engine / Kubernetes kubelet / platform client
                    |
                    v
               containerd API
                    |
        +-----------+------------+
        |           |            |
        v           v            v
 content/images  snapshots   runtime/tasks
        |           |            |
        |           |            v
        |           |       runtime shim
        |           |            |
        |           |            v
        |           |         OCI runtime
        |           |            |
        +-----------+------------+
                    |
                    v
                host kernel
```

The boundaries matter. A registry pull problem, snapshotter failure, CRI configuration error, runtime-shim crash, OCI runtime failure, and application exit are different failure classes even though a user may experience all of them as “the container did not start.”

## What containerd is

containerd provides a daemon, APIs, client libraries, and a plugin system for core container-host responsibilities such as:

- content acquisition and storage;
- image metadata;
- filesystem snapshots;
- container metadata;
- live process/task lifecycle;
- runtime integration;
- eventing and introspection;
- namespaces for multiple consumers;
- garbage collection and lifecycle coordination;
- Kubernetes CRI integration;
- metrics and operational endpoints.

It is intentionally narrower than Docker Engine. Docker adds a developer-oriented product surface around image builds, networks, volumes, Compose workflows, UX, and other features. containerd is designed to be embedded or consumed by higher-level systems.

## Why containerd exists

Container platforms need a stable host service that can keep track of container-related state without forcing every higher-level product to directly implement:

- OCI content storage;
- image unpacking;
- snapshot management;
- runtime process supervision;
- low-level runtime invocation;
- restart/reconnect behavior;
- Kubernetes CRI plumbing;
- storage-driver and runtime extensibility.

Separating those responsibilities gives higher-level systems a reusable lifecycle layer and gives low-level runtimes a narrower interface.

The design also isolates lifecycles. Running workloads should not automatically die just because the management daemon restarts. Runtime shims are an important part of that separation.

## What containerd is not

### Not Docker

Docker Engine uses containerd, but Docker and containerd are not interchangeable products.

Docker normally provides a broader user-facing workflow:

```text
Docker CLI / API
      |
 Docker Engine
      |
  containerd
      |
 runtime / kernel
```

containerd by itself does not try to reproduce the full Docker developer experience.

### Not runc

`runc` is a low-level OCI runtime implementation. Its job is much closer to “create this configured container process according to the OCI runtime model.”

containerd sits above that level. It tracks images, snapshots, containers, tasks, namespaces, plugins, and process supervision, then delegates low-level execution through runtime integrations such as `runc`-based Runtime v2 shims.

### Not Kubernetes

Kubernetes schedules and reconciles desired workload state across nodes. containerd is node-local infrastructure.

Kubernetes kubelet can use the Container Runtime Interface (CRI) to ask containerd to manage images, pod sandboxes, and containers on that node.

### Not a stable general-purpose CLI product

The bundled `ctr` tool is primarily for debugging and understanding containerd's native API. containerd maintainers explicitly do not treat `ctr` as the project's stable end-user product interface.

For human-oriented container workflows, tools such as `nerdctl` may be more suitable. For Kubernetes runtime debugging, `crictl` speaks CRI rather than the native containerd API.

## Architecture: daemon plus plugins

containerd's core is deliberately small. Much of its functionality is supplied by plugins loaded by the daemon.

Conceptually:

```text
containerd daemon
    |
    +-- content service/plugin
    +-- metadata service/plugin
    +-- snapshotter plugins
    +-- runtime/task plugins
    +-- CRI plugins
    +-- event/introspection services
    +-- transfer/image services
    +-- NRI integration
    +-- proxy/external plugins
```

This architecture allows different storage backends, runtime implementations, and integrations to coexist without making every implementation part of one monolithic core.

Plugin boundaries are also operational boundaries. A daemon can start while an optional plugin is skipped because its prerequisites are absent. Operators should distinguish “containerd is running” from “the plugin required by this workload is healthy and configured.”

## Native API and clients

containerd exposes APIs over a local service endpoint, commonly a Unix socket on Linux.

Higher-level consumers can use:

- the containerd Go client API;
- native gRPC services;
- the Kubernetes CRI plugin/API path;
- specialized tools such as `ctr`, `nerdctl`, or `crictl` depending on the layer being debugged.

A useful debugging rule is to use the client that matches the interface under investigation:

```text
native containerd API problem -> ctr / native client
human container workflow      -> nerdctl (non-core)
Kubernetes CRI problem         -> crictl / kubelet logs
application problem            -> application logs and process state
```

Using the wrong client can make two views of the same host appear inconsistent because containerd namespaces and CRI abstractions may differ.

## Namespaces

containerd namespaces isolate metadata and state between different consumers of the same daemon.

Common examples include:

- `k8s.io` for Kubernetes CRI workloads;
- `moby` for Docker/Moby clients;
- `default` or another client-selected namespace for native containerd usage.

The namespace is part of API context, not a Linux kernel namespace. It is a **containerd tenancy/organization boundary** for objects such as images and containers.

This distinction is important:

```text
containerd namespace -> isolates containerd object views between clients
Linux namespace      -> isolates process views of kernel resources
```

A common operational surprise is running `ctr` in one namespace and not seeing Kubernetes images or containers stored under `k8s.io`.

### Content sharing and namespace policy

containerd can share underlying content blobs while still presenting namespaced image/container metadata. The metadata plugin can be configured with different content-sharing policies.

Sharing saves bandwidth and disk when consumers use identical content, but content visibility policy matters in multi-consumer threat models. Operators should treat namespace behavior and content-sharing configuration as security-relevant, not merely cosmetic naming.

## Core object model

Understanding containerd becomes much easier once its major objects are separated.

### Content

The content store holds immutable blobs addressed by digest.

Examples include:

- OCI manifests;
- image indexes;
- image configuration blobs;
- compressed filesystem layers;
- other descriptor-addressed artifacts.

A digest identifies bytes. The content store does not by itself mean those bytes are an image that has been unpacked and made runnable.

### Descriptor

OCI-style descriptors identify content by media type, digest, size, and optional metadata.

Descriptors connect higher-level objects to content without requiring every subsystem to duplicate blob data.

### Image

A containerd image object is metadata that names and points to image content.

An image reference such as a registry name is therefore distinct from:

- the manifest/index blob;
- downloaded layer blobs;
- unpacked filesystem snapshots;
- a container object;
- a running task.

This explains why “image exists” and “image is unpacked for this snapshotter/platform” are separate conditions.

### Snapshot

A snapshot is a filesystem view managed by a snapshotter.

Snapshotters abstract storage implementations such as overlay-based or other filesystem/storage-specific backends. They typically manage lifecycle states such as preparing writable filesystem views and committing reusable snapshots.

An image can be present in the content store but still require unpacking through a snapshotter before a task can use its root filesystem.

### Container

A container object is persistent metadata describing a container identity and configuration.

It can exist without a running process.

Think of it as a durable record that can include references to:

- image metadata;
- snapshot/root filesystem information;
- OCI runtime specification/configuration;
- labels and extensions;
- runtime selection.

### Task

A task represents the live runtime process side of a container.

The useful distinction is:

```text
container -> metadata/configuration object
task      -> executing process lifecycle
```

Creating container metadata does not necessarily start anything. A task must be created and started for a process to run.

### Sandbox

Modern containerd releases also expose sandbox-oriented APIs and integrations. Sandboxes are particularly relevant to CRI/pod-style execution where multiple containers may share lifecycle or isolation context.

Because sandbox/shim behavior has evolved across containerd releases, operators should check the documentation for the deployed major/minor version before assuming a one-container/one-shim implementation detail.

## Content flow: pull to runnable root filesystem

A simplified image flow is:

```text
registry
   |
   v
resolver / transfer path
   |
   v
content store
   |
   +-- index/manifest
   +-- config
   +-- compressed layers
   |
   v
image metadata
   |
   v
unpack
   |
   v
snapshotter
   |
   v
prepared root filesystem
```

There are several independent failure points:

- registry DNS/TLS/authentication;
- manifest/platform selection;
- digest verification;
- content download;
- decompression;
- snapshotter capacity/metadata;
- filesystem mount support;
- disk/inode exhaustion.

Treating all of these as “image pull failed” loses useful diagnostic information.

## Content-addressed storage

Content-addressed blobs provide integrity and deduplication properties: identical bytes produce the same digest and can be reused.

This enables efficient sharing of layers across images and, depending on namespace/content-sharing policy, across clients.

It also means garbage collection must understand reachability. A blob can be physically present while no durable image/container reference protects it forever.

## Garbage collection and leases

containerd manages resource lifecycle so unused content, snapshots, and metadata can eventually be reclaimed.

Garbage collection depends on references between objects and metadata. Long-running operations can use leases to keep temporary resources protected while a workflow is in progress.

Operational consequences include:

- do not treat internal content directories as a permanent user-managed archive;
- do not manually delete random files under containerd's root;
- do not assume an unreferenced blob will remain forever;
- investigate leaked references/leases if storage does not reclaim as expected.

Manual mutation of containerd's internal storage can corrupt metadata relationships or create stale mounts/handles.

## Snapshotters

Snapshotters provide the filesystem layer between image content and runtime root filesystems.

A snapshotter is responsible for storage lifecycle operations rather than registry transport. Different snapshotters can implement different backing technologies and performance characteristics.

The default on many Linux installations is an overlayfs-based snapshotter, but the correct backend depends on kernel/filesystem support and platform requirements.

### Snapshotter choice affects performance

Storage behavior can change substantially with:

- copy-on-write implementation;
- backing filesystem;
- metadata operations;
- image layer count;
- unpack concurrency;
- write amplification;
- inode availability;
- remote/lazy-pull designs;
- garbage-collection pressure.

A workload that is CPU-light but filesystem-metadata-heavy can be bottlenecked by snapshotter behavior.

### Snapshotter failures

Typical symptoms include:

- image downloaded but unpack fails;
- task creation fails while mounting rootfs;
- stale mounts after crashes;
- “device busy” cleanup errors;
- snapshot metadata present while backing data is missing;
- disk/inode exhaustion.

Diagnosis should include the configured snapshotter, backing filesystem, kernel support, mount state, and containerd plugin status.

## Runtime v2 and shims

containerd separates daemon management from runtime process supervision through runtime/shim interfaces.

In the common OCI path:

```text
containerd
    |
Runtime v2 integration
    |
   shim
    |
 OCI runtime (for example runc)
    |
 container process
```

The shim owns process-facing responsibilities such as IO and exit-status handling and allows the workload lifecycle to be decoupled from the main containerd daemon.

This is why a container process can continue while containerd is restarted and later be reconnected to, assuming the runtime/shim path remains healthy.

### Why the shim matters operationally

If containerd is healthy but a runtime shim is wedged, only specific workloads may fail.

If containerd restarts, healthy shims help preserve running tasks.

If the low-level runtime fails during create/start, the failure can occur before the application process exists at all.

The process tree and logs should therefore be inspected at the right layer.

## OCI runtime boundary

containerd commonly delegates low-level execution to OCI-compatible runtime implementations.

The OCI Runtime Specification defines the runtime configuration and lifecycle model. containerd is responsible for higher-level lifecycle/state coordination and preparing what the runtime needs.

A useful boundary is:

```text
containerd decides/tracks lifecycle
        |
        v
OCI runtime creates/manages isolated process according to runtime config
```

Different runtimes can implement the same broad interface while providing different isolation technologies or platform behavior.

## Kubernetes CRI integration

containerd includes native CRI support so Kubernetes kubelet can use it as a node container runtime.

The flow is approximately:

```text
Kubernetes control plane
        |
     kubelet
        |
       CRI
        |
containerd CRI services
        |
 +------+----------------+
 |                       |
image/snapshot path   runtime/sandbox path
 |                       |
 +-----------+-----------+
             |
             v
        node workloads
```

CRI is a different API surface from containerd's native API.

That distinction explains why:

- `crictl` and `ctr` can show different conceptual views;
- CRI configuration may affect Kubernetes while native `ctr` operations still work;
- the `k8s.io` containerd namespace is commonly associated with CRI-managed objects;
- pod sandbox networking and Kubernetes lifecycle semantics live above the raw container/task model.

## CRI configuration in containerd 2.x

containerd 2.x documentation uses configuration version 3 as the recommended format. Earlier version-2 configuration remains supported and can be converted, but plugin IDs/configuration paths changed across the major-version boundary.

This matters during upgrades: blindly copying a containerd 1.x configuration into a 2.x troubleshooting guide can produce misleading conclusions even if compatibility conversion lets the daemon start.

Always inspect the effective config generated by the installed version.

A common starting point is:

```bash
containerd config default
```

Treat the generated output as version-specific configuration, not a timeless template.

## Runtime classes and Kubernetes

CRI can map Kubernetes runtime classes to different containerd runtime configurations.

That enables a node to select different runtimes or runtime settings for different workloads when the platform is configured appropriately.

Failure modes therefore include not only “runtime unavailable,” but also “requested runtime class resolves to the wrong or missing runtime configuration.”

## cgroups

containerd, CRI configuration, the selected OCI runtime, kubelet, and systemd/cgroup policy all meet at the cgroup boundary.

On systemd-based hosts, Kubernetes/container-runtime documentation commonly recommends aligned systemd cgroup handling rather than two independent managers competing over the same hierarchy.

Cgroup-driver mismatch can surface as:

- pod startup failures;
- resource accounting surprises;
- node instability;
- inconsistent CPU/memory enforcement;
- upgrade-specific regressions.

Debug the whole node policy rather than changing one setting in isolation.

## Networking

containerd's native core is not a Docker-style network-management product.

For Kubernetes CRI workloads, networking is typically integrated through the CRI path and CNI plugins/configuration.

This produces a layered failure model:

```text
containerd task starts?
      |
      +-- yes --> sandbox/network setup succeeds?
                         |
                         +-- CNI config/plugin
                         +-- namespace/interface
                         +-- routes/firewall
                         +-- DNS/service layer
```

A workload can have a healthy container runtime process and still have broken pod networking.

Conversely, CNI errors may prevent a pod sandbox from becoming usable even though containerd itself is otherwise healthy.

## NRI

The Node Resource Interface (NRI) provides an integration point for plugins that adjust container configuration or react to lifecycle events.

In modern containerd 2.x documentation, NRI is integrated as a containerd plugin and can be used with CRI containers and other containerd domains/namespaces.

NRI expands extensibility but also expands the operational trust boundary. A plugin that mutates resource or runtime configuration should be treated as privileged node infrastructure.

## Transfer service

Recent containerd generations include a transfer service for image/content transfer workflows.

The important architectural point is that registry transfer can be separated from local content/snapshot/runtime state. Operators should avoid assuming that every image pull implementation path is identical across clients and versions.

For example, `ctr` behavior is not a stable promise for how every higher-level consumer performs transfers.

## Persistent root versus runtime state

containerd distinguishes persistent data from ephemeral runtime state.

Typical Linux defaults are conceptually:

```text
/var/lib/containerd   -> persistent root
/run/containerd       -> runtime state
```

Persistent root can contain:

- content blobs;
- metadata databases;
- snapshots;
- plugin-owned persistent data.

Runtime state can contain:

- sockets;
- PIDs;
- runtime/shim state;
- mount-related state;
- data that should not need to survive reboot.

The exact internal paths are implementation details. External programs should use supported APIs instead of watching or editing those directories directly.

## Metadata database

containerd uses metadata services to connect higher-level objects such as images, containers, snapshots, content references, and namespaces.

This metadata is as important as raw layer blobs. Copying only selected files out of `/var/lib/containerd` is not equivalent to a supported backup/restore procedure.

If metadata is corrupted, content bytes may still exist while containerd can no longer safely reason about ownership and lifecycle.

## Events

containerd publishes events for lifecycle changes across services and plugins.

Higher-level systems can consume event streams to observe state changes, but events should not be treated as the only durable source of truth. Consumers need reconnection/reconciliation logic because a temporary disconnection must not permanently desynchronize desired and observed state.

This is a recurring distributed-systems principle: event streams accelerate reconciliation; they do not remove the need for authoritative state queries.

## Observability

containerd exposes operational signals including logs, plugin state, events, and Prometheus-format metrics when configured.

Useful signals include:

- daemon health/startup logs;
- loaded/skipped plugin messages;
- runtime/shim process state;
- CRI/kubelet errors;
- image transfer latency/errors;
- snapshotter activity;
- task exits;
- garbage-collection/storage pressure;
- gRPC/API failures;
- container-level metrics exposed through configured endpoints.

An effective incident investigation correlates containerd logs with kubelet/runtime/application logs rather than reading one source in isolation.

## `ctr`, `nerdctl`, and `crictl`

These tools sit at different layers.

### `ctr`

`ctr` ships with containerd and is valuable for native API debugging and learning.

Examples:

```bash
ctr plugins ls
ctr namespaces ls
ctr images ls
ctr containers ls
ctr tasks ls
```

For Kubernetes-managed objects, specify the relevant namespace when appropriate, for example:

```bash
ctr -n k8s.io images ls
```

Do not build production automation around undocumented `ctr` output stability. The project explicitly treats it as a debugging/introspection tool rather than its main supported product interface.

### `nerdctl`

`nerdctl` is a separate project that offers a more Docker-like human-facing CLI over containerd.

It is useful when the goal is a general-purpose container user experience rather than inspecting raw containerd APIs.

### `crictl`

`crictl` is a Kubernetes CRI debugging tool.

Use it when the question is “what does kubelet/CRI see?” rather than “what objects exist through containerd's native API?”

This distinction avoids many false discrepancies during debugging.

## Reliability model

### Daemon restart should not equal workload restart

A key design goal of the shim architecture is to decouple running task lifetime from the containerd daemon process.

If containerd is restarted, healthy workloads can remain running and the daemon can reconnect to runtime/shim state.

This does not mean every failure is transparent. Corrupted runtime state, dead shims, broken sockets, or incompatible upgrades can still disrupt reconnection.

### Persistent state must remain internally consistent

Container images and snapshots are not independent random files. Metadata and references matter.

Filesystem-level manipulation under containerd's root can create states the daemon cannot safely reconcile.

### Plugin health is part of service health

A running daemon with a failed snapshotter or disabled CRI plugin may be useless to the workload that depends on that plugin.

Read startup logs and plugin lists when diagnosing node problems.

## Common failure modes

### containerd service will not start

Check:

- configuration syntax/version;
- plugin configuration;
- socket/path permissions;
- root/state directory access;
- incompatible runtime binaries;
- filesystem prerequisites;
- stale runtime state after abnormal shutdown;
- package/major-version mismatch.

Do not delete state directories as a first troubleshooting step; that can turn a recoverable configuration problem into data loss.

### CRI unavailable while containerd is running

Possible causes include:

- CRI plugin disabled or failed to initialize;
- wrong endpoint configured in kubelet/crictl;
- incompatible or stale config section names;
- CNI/runtime prerequisites missing;
- plugin startup error.

Native `ctr` success does not prove CRI is healthy.

### Image present but Kubernetes still pulls

Check namespace, CRI image identity, platform, digest/tag resolution, pull policy, and whether the expected content is available/unpacked through the snapshotter used by CRI.

Seeing an image through a native client in another namespace is not sufficient proof that kubelet's CRI view will reuse it.

### Image pull succeeds but unpack fails

Investigate:

- snapshotter;
- backing filesystem support;
- disk/inode capacity;
- permissions;
- decompression/content integrity;
- platform/manifest mismatch.

Transfer success and snapshot preparation are separate stages.

### Task create/start fails

Investigate:

- OCI runtime binary and runtime class;
- runtime shim logs/state;
- OCI spec/config;
- mounts;
- cgroups;
- namespaces;
- seccomp/LSM policy;
- root filesystem preparation.

If the task never started, application logs may not exist because the application process was never created.

### Task exits immediately

Once runtime creation succeeds, shift focus toward:

- application command/entrypoint;
- signal handling;
- missing files/configuration;
- permissions;
- architecture mismatch;
- application dependencies.

The failure layer has moved from containerd infrastructure to the workload itself.

### Disk usage keeps growing

Possible sources include:

- content blobs;
- snapshots;
- image references;
- leases/references preventing GC;
- build-related content from higher-level tools;
- logs outside containerd's own storage;
- persistent application storage.

Measure each path before manually deleting anything.

### Stale mounts or `EBUSY`

Abnormal process termination, external processes holding filesystem references, or unsupported inspection of internal directories can interfere with cleanup.

Inspect mount holders and runtime state first. Directly mutating containerd plugin directories can make the problem worse.

### Namespace confusion

If `ctr images ls` appears empty while Kubernetes is running many images, check the namespace:

```bash
ctr namespaces ls
ctr -n k8s.io images ls
```

This is one of the most common conceptual debugging mistakes.

## Security boundaries

containerd is privileged node infrastructure. Control of its API can often lead to control of container execution on the host.

A secure deployment should consider:

- socket ownership and filesystem permissions;
- who can access the native containerd API;
- kubelet/CRI endpoint trust;
- runtime and shim binaries;
- plugin supply chain;
- snapshotter permissions and mount behavior;
- registry credentials;
- content integrity and image provenance;
- cgroup/user-namespace/runtime configuration;
- NRI and other privileged node extensions;
- host kernel security.

### Protect the containerd socket

Treat access to the containerd control socket as highly privileged.

A user or workload able to create tasks with powerful mounts, namespaces, or runtime settings may be able to escape normal workload restrictions by design, because the service exists to create privileged host-level container constructs.

### Registry credentials

Image acquisition may require registry credentials. Store and distribute them using platform-supported secret mechanisms rather than embedding long-lived credentials in images or ad-hoc scripts.

### Content integrity is not provenance

Digest verification proves that downloaded bytes match a requested digest. It does not prove that the publisher is trustworthy or that the image is vulnerability-free.

Supply-chain controls such as signatures, attestations, SBOMs, policy enforcement, and protected registries solve different problems.

### Plugins extend the trust boundary

Snapshotters, runtime shims, NRI components, and proxy plugins can execute with significant node privileges.

Installing a plugin is therefore not equivalent to installing an unprivileged user-space library. Versioning, provenance, compatibility, and permissions should be reviewed like other host infrastructure.

## Performance characteristics

containerd itself is rarely the only determinant of container performance. The complete path includes registry/network, content store, snapshotter, runtime, kernel, and higher-level orchestration.

### Cold-start latency

Cold starts can be dominated by:

- DNS/TLS/registry latency;
- image size and layer count;
- concurrent download limits;
- decompression;
- content verification;
- snapshot preparation;
- filesystem metadata performance;
- runtime/shim startup;
- CNI/network setup;
- application initialization.

Optimizing only daemon CPU usage can miss the actual bottleneck.

### Warm starts

If content is local and snapshots are already prepared, runtime creation can be much faster. Cache effectiveness therefore depends on stable content digests, node image reuse, snapshotter behavior, and garbage-collection pressure.

### Content deduplication

Content-addressed storage can reduce duplicate transfer and disk use when images share blobs.

Actual savings depend on image construction, compression, content-sharing policy, and whether higher-level systems produce reusable layers.

### Snapshotter cost

Copy-on-write and metadata behavior can materially affect write-heavy workloads. Databases and other storage-sensitive services should be benchmarked on their actual persistent-volume path rather than assuming container rootfs performance represents production storage.

## Upgrade and compatibility considerations

containerd has explicit API and release-stability policies, but major releases can remove deprecated components and change configuration conventions.

Notable containerd 2.x-era considerations include:

- configuration version 3 is recommended for 2.x;
- version-2 config remains supported but plugin IDs/structure can differ;
- long-deprecated Runtime v1 paths were removed in 2.0;
- older release-bundle conventions were removed;
- CRI/runtime/sandbox capabilities have evolved;
- third-party snapshotters/runtimes/plugins need their own compatibility checks.

An upgrade plan should test:

1. daemon configuration;
2. plugin loading;
3. snapshotter compatibility;
4. runtime/shim compatibility;
5. CRI behavior with the target Kubernetes version;
6. CNI and cgroup configuration;
7. workload restart/reconnect behavior;
8. storage and garbage collection;
9. metrics/observability;
10. rollback constraints.

## Operational workflow

A disciplined node-runtime investigation can proceed layer by layer.

### 1. Confirm daemon health

```bash
systemctl status containerd
journalctl -u containerd
```

### 2. Check plugin state

```bash
ctr plugins ls
```

Look for required snapshotter/runtime/CRI-related failures rather than assuming every skipped optional plugin is fatal.

### 3. Check namespaces

```bash
ctr namespaces ls
```

### 4. Inspect native objects

```bash
ctr -n <namespace> images ls
ctr -n <namespace> containers ls
ctr -n <namespace> tasks ls
```

### 5. If Kubernetes is involved, switch to the CRI view

Use kubelet logs and `crictl` so the investigation matches the interface Kubernetes actually uses.

### 6. Trace the failure layer

```text
registry -> content -> image -> unpack/snapshot -> container metadata
-> task/shim/runtime -> network/sandbox -> application
```

Stop changing layers once evidence points to a specific boundary.

## Common conceptual mistakes

### “containerd is just runc with a daemon”

Too narrow. containerd also manages content, images, snapshots, metadata, APIs, namespaces, plugins, CRI integration, events, and lifecycle coordination.

### “containerd is Docker without the CLI”

Too broad. Docker Engine adds product-level behavior and workflows that are intentionally outside containerd's scope.

### “If `ctr` works, Kubernetes runtime is healthy”

False. `ctr` uses containerd's native API; Kubernetes uses CRI. The CRI plugin, namespace, runtime class, CNI, or kubelet path can still be broken.

### “If an image blob exists, it is ready to run”

Not necessarily. Image metadata, platform selection, unpacking, and snapshotter state are separate concerns.

### “A container object means a process is running”

No. The persistent container object and live task are distinct.

### “containerd namespaces are Linux namespaces”

No. containerd namespaces partition API-visible object state; Linux namespaces isolate kernel resource views for processes.

### “It is safe to clean `/var/lib/containerd` manually”

No. Internal directories contain coordinated content, metadata, snapshot, and plugin state. Use supported lifecycle operations and investigate references before deleting data.

### “Restarting containerd must restart every container”

The shim architecture is specifically designed to decouple running task lifetime from the daemon, although recovery still depends on healthy runtime state.

## Where containerd fits well

containerd is a strong fit when a platform needs:

- a production container lifecycle service;
- OCI-compatible image/runtime integration;
- pluggable snapshotters and runtimes;
- Kubernetes CRI support;
- an embeddable native client/API;
- separation between higher-level orchestration and low-level runtimes;
- multi-consumer namespaced state on a host.

## When containerd is not the right direct interface

A developer may prefer another layer when the need is:

- a polished Docker-like CLI experience;
- Compose-style local application workflows;
- full build UX;
- cluster scheduling/reconciliation;
- a low-level single-container OCI runtime API;
- a stable human-readable command output contract for automation.

Choose the interface that matches the layer rather than forcing containerd to act like a different product.

## Ecosystem map

### Docker

Docker Engine uses containerd beneath its broader engine/developer workflow.

### Kubernetes

Kubernetes kubelet integrates through CRI. containerd is one common node runtime implementation, not the scheduler or control plane.

### OCI runtimes

Low-level runtimes implement the process-execution boundary beneath containerd runtime/shim integrations.

### Snapshotters

Snapshotter plugins provide filesystem snapshot behavior and can be local, filesystem-specific, or more specialized.

### CNI

For Kubernetes/CRI workloads, CNI plugins supply network setup above the raw task/runtime layer.

### NRI

NRI provides a node-resource/runtime configuration extension point.

### nerdctl

A separate project that provides a human-friendly, Docker-like CLI for containerd.

### crictl

A Kubernetes SIG Node tool for inspecting/debugging CRI implementations.

## Learning path

A useful progression is:

1. understand the container process model, Linux namespaces, and cgroups;
2. distinguish image, content blob, snapshot, container, and task;
3. learn OCI Image and Runtime concepts;
4. inspect containerd namespaces and plugins;
5. learn the content store and snapshotter boundary;
6. understand Runtime v2, shims, and low-level OCI runtimes;
7. use `ctr` only as a native debugging/learning tool;
8. learn CRI and inspect Kubernetes workloads with `crictl`;
9. study CNI, cgroup policy, and runtime classes;
10. learn storage/GC, observability, and upgrade operations;
11. then study advanced plugins, NRI, alternative snapshotters, and custom platform integrations.

## What to learn next

Recommended OpenDevIndex neighbors:

- `concept/containers` — kernel/OCI mental model beneath containerd;
- `tool/docker` — higher-level engine and developer workflow using containerd;
- `cloud/kubernetes` — orchestration layer that can use containerd through CRI.

## Authoritative sources

Primary references for this module include:

- containerd official site — https://containerd.io/
- containerd source repository — https://github.com/containerd/containerd
- Getting Started — https://github.com/containerd/containerd/blob/main/docs/getting-started.md
- Operations Guide — https://github.com/containerd/containerd/blob/main/docs/ops.md
- Releases and stability policy — https://github.com/containerd/containerd/blob/main/RELEASES.md
- CRI configuration — https://github.com/containerd/containerd/blob/main/docs/cri/config.md
- NRI documentation — https://github.com/containerd/containerd/blob/main/docs/NRI.md
- OCI Runtime Specification — https://specs.opencontainers.org/runtime-spec/
- Kubernetes CRI documentation — https://kubernetes.io/docs/concepts/containers/cri/

## Verification and maintenance

This module was reviewed on **2026-09-05** against current containerd project documentation, release policy, CRI configuration guidance, OCI runtime documentation, and Kubernetes CRI documentation.

Facts most likely to age are configuration/plugin IDs, CRI/runtime integration details, sandbox/NRI behavior, supported snapshotters, release compatibility, and CLI examples. The stable anchor is the architecture: containerd is the node-local lifecycle/API layer coordinating content, images, snapshots, metadata, tasks, shims/runtimes, plugins, and higher-level clients.
