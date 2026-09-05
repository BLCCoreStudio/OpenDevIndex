# Kubernetes

> Declarative container orchestration platform whose API, controllers, scheduler, and node agents continuously reconcile application and infrastructure state across a cluster.

Kubernetes is easiest to understand as an **API-driven control system**, not as a command that launches containers on many machines. Users and higher-level tools submit desired state to the Kubernetes API. The control plane stores that state, controllers continuously compare desired state with observed state, the scheduler chooses placement for new Pods, and kubelets on worker nodes turn assigned Pod specifications into running workloads through a container runtime.

That reconciliation model is the organizing idea for the entire platform.

---

## 1. What Kubernetes is

Kubernetes is an open-source platform for orchestrating containerized workloads across a cluster of machines. It provides APIs and control loops for workload placement, rollout, service discovery, networking, storage attachment, configuration, security policy, failure recovery, and extensibility.

It does **not** replace every component in a distributed system. Kubernetes normally delegates important work to other layers:

- a CRI-compatible container runtime such as containerd creates and supervises containers;
- a pod-network implementation provides node and Pod networking;
- CSI drivers integrate persistent storage systems;
- cloud-controller integrations connect to infrastructure-provider APIs where applicable;
- applications still own their own data consistency, request handling, domain logic, and most application-level recovery semantics.

The stable OpenDevIndex address for this module is `cloud/kubernetes`.

## 2. Why Kubernetes exists

Running one container on one machine is straightforward. Operating many services across many machines creates a different class of problem:

- deciding where new workloads should run;
- replacing failed processes and failed nodes;
- rolling out new versions without manually touching every host;
- providing stable service discovery while individual Pod identities change;
- attaching storage to workloads that move;
- separating application intent from machine-specific configuration;
- enforcing policy across teams and namespaces;
- exposing a common automation surface to operators, controllers, and platform tools.

Kubernetes addresses these problems by moving the primary interface from **host-by-host imperative operations** to **declarative API objects plus reconciliation**.

Instead of saying "SSH to node 17 and start three processes," the user typically declares an object such as a Deployment with three replicas. Controllers then keep trying to make the cluster match that declaration.

This distinction explains both Kubernetes' power and much of its complexity.

---

## 3. The core mental model: desired state and reconciliation

A useful simplified flow is:

```text
human / CI / controller
        |
        v
   Kubernetes API
        |
        v
 authentication -> authorization -> admission
        |
        v
       etcd
        |
        +--------------------+
        |                    |
        v                    v
   controllers           scheduler
        |                    |
        |                    v
        |                Pod -> Node binding
        |                    |
        +----------+---------+
                   |
                   v
                 kubelet
                   |
          +--------+--------+
          |        |        |
          v        v        v
         CRI      CNI      CSI
          |        |        |
          v        v        v
      containers  network  storage
```

This is intentionally simplified, but it captures the main control flow.

### Step 1: a client submits desired state

A user might run `kubectl apply`, a GitOps controller might reconcile manifests from a repository, or a custom controller might create an API object programmatically.

All of those paths ultimately interact with the Kubernetes API.

### Step 2: the API server processes the request

The API server is the central front door to cluster state. Requests pass through access-control stages such as authentication, authorization, and admission before accepted object state is persisted.

The API server is therefore not merely a REST wrapper around etcd. It is a policy and consistency boundary for the Kubernetes object model.

### Step 3: desired state is stored

Persistent API state is backed by etcd. Controllers and other components observe changes through the API rather than treating etcd as a normal application database.

### Step 4: controllers reconcile

Controllers watch relevant objects and perform work to reduce the difference between desired and observed state.

For a Deployment, for example, the Deployment controller manages ReplicaSets, and ReplicaSets in turn drive the existence of the desired number of Pods.

### Step 5: the scheduler assigns unscheduled Pods

A newly created Pod normally has no node assignment. The scheduler filters nodes that cannot satisfy the Pod and scores feasible nodes to choose a placement, then records a binding through the API.

### Step 6: kubelet realizes node-local state

The kubelet on the selected node watches for Pods assigned to that node. It coordinates with the container runtime and other node services to make those Pods real, then reports status back through the API.

### Step 7: reconciliation never really stops

A cluster is not "configured once." State changes continuously:

- Pods terminate;
- nodes disappear;
- images change;
- a Deployment is updated;
- an autoscaler changes replica count;
- a volume becomes unavailable;
- a readiness probe starts failing;
- a controller notices a missing dependent object.

Kubernetes repeatedly observes and reacts.

This means the platform is generally **eventually convergent**, not a single synchronous transaction that instantly makes the entire cluster match a manifest.

---

## 4. Cluster architecture

A Kubernetes cluster is normally described as a **control plane** plus one or more **worker nodes**.

### Control plane

The control plane makes cluster-wide decisions and maintains API state.

Core components include:

#### kube-apiserver

The API server exposes the Kubernetes HTTP API and acts as the central coordination point for clients and control-plane components.

Important implications:

- almost every meaningful cluster operation becomes an API operation;
- API latency and availability affect the whole control plane;
- authorization and admission policy live on the request path;
- controllers should work through the API rather than modifying backing state directly.

#### etcd

etcd is the consistent key-value backing store for Kubernetes API data.

Operationally, etcd is one of the most critical stateful components in a self-managed control plane. Losing all recoverable etcd state means losing the persisted desired and observed cluster state needed to reconstruct normal control-plane operation.

A real production recovery plan therefore includes tested etcd backup and restore procedures, not merely filesystem snapshots taken without understanding consistency.

#### kube-scheduler

The scheduler watches for Pods that have not yet been assigned a node. It evaluates feasible nodes and selects a placement according to resource availability and scheduling policy.

Scheduling is not "pick the node with the most free CPU." Inputs can include:

- resource requests;
- node selectors;
- node affinity and anti-affinity;
- Pod affinity and anti-affinity;
- topology spread constraints;
- taints and tolerations;
- volume topology;
- priority and preemption;
- scheduler plugins and profiles.

#### kube-controller-manager

The controller manager runs many control loops that implement Kubernetes API behavior.

Examples include controllers concerned with nodes, replication, endpoints, namespaces, service accounts, Jobs, and other resource lifecycles.

The key pattern is more important than the exact list: **a controller observes API state and acts to move the system toward the desired state**.

#### cloud-controller-manager

Where a cluster integrates with a supported infrastructure provider, cloud-controller components can separate cloud-specific control logic from the core Kubernetes control plane.

Not every Kubernetes cluster needs this component.

### Worker nodes

Worker nodes execute workload Pods.

#### kubelet

The kubelet is the primary Kubernetes node agent.

It is responsible for making the node-local reality of assigned Pods correspond to Pod specifications. It coordinates container lifecycle, probes, mounted volumes, status reporting, and node-level resource enforcement with the runtime and operating system.

The kubelet is not the cluster scheduler. It normally runs what has already been assigned to its node.

#### container runtime

Kubernetes delegates container lifecycle operations through the Container Runtime Interface (CRI).

A CRI-compatible runtime such as containerd can pull images, create Pod sandboxes, start containers, and report runtime status.

This boundary matters because **Kubernetes does not require Docker Engine on worker nodes**. Docker-built OCI-compatible images can still run in Kubernetes through another compatible runtime.

#### service networking data plane

Kubernetes Service abstractions require a data-plane implementation that directs virtual service traffic toward current backends.

`kube-proxy` is the traditional Kubernetes component for this role, but some networking systems implement Service forwarding through their own data plane instead.

#### Pod networking implementation

Kubernetes defines the networking model but relies on networking implementations to create Pod network interfaces, routes, policy enforcement, and related data-plane behavior.

#### storage plugins

CSI drivers connect Kubernetes volume APIs to concrete storage systems.

---

## 5. Control plane versus data plane

A useful operational separation is:

```text
control plane = decide and record what should happen
data plane    = carry workload traffic and execute workload processes
```

The boundary is not perfectly clean, but it helps diagnose failures.

For example:

- if the API server is unavailable, existing application Pods may continue serving traffic for a while because their processes and network paths already exist;
- however, controllers cannot normally reconcile new desired state through an unavailable API;
- if the scheduler is unavailable, already scheduled Pods can continue running, but new unscheduled Pods remain pending;
- if a node's runtime fails, the control plane may still be healthy while workloads on that node fail to start or recover.

This is why "the cluster is down" is usually too vague to be a useful diagnosis.

---

## 6. Kubernetes API object model

Kubernetes is built around API resources rather than opaque orchestration scripts.

A typical object contains:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: web
          image: example/web:1.4.2
```

### `apiVersion`

Identifies the API group and version used for the object schema.

### `kind`

Identifies the resource type, such as Pod, Deployment, Service, ConfigMap, or CustomResourceDefinition.

### `metadata`

Carries object identity and metadata such as name, namespace, labels, annotations, owner references, and finalizers.

### `spec`

Usually describes desired state supplied by the user or another controller.

### `status`

Usually describes observed state reported by Kubernetes components or controllers.

The distinction between `spec` and `status` is central to reconciliation. Controllers compare what the object asks for with what the system currently reports.

### Object identity and concurrency

Important object metadata includes concepts such as:

- name and namespace;
- UID;
- resource version;
- generation;
- labels and annotations;
- owner references;
- finalizers.

These fields support lifecycle management, selection, optimistic concurrency, garbage collection, and safe deletion workflows.

### Labels and selectors

Labels are structured key-value metadata used heavily for grouping and selection.

Selectors connect many Kubernetes abstractions:

- Deployments select ReplicaSets and Pods;
- Services select backend Pods;
- operational tooling selects sets of objects for querying or policy.

Misaligned labels and selectors are therefore a common cause of apparently mysterious "nothing is connected" failures.

### Namespaces

Namespaces partition namespaced API objects and provide a scope for policy, quotas, and access control.

They are not a universal security boundary by themselves. Isolation depends on RBAC, network policy, Pod security controls, resource quotas, secrets handling, and infrastructure configuration.

---

## 7. Controllers and ownership

Kubernetes controllers usually do not mutate every low-level object directly in one giant transaction. Higher-level objects often own or drive lower-level objects.

A common chain is:

```text
Deployment
   |
   v
ReplicaSet
   |
   v
Pods
```

Changing a Deployment's Pod template normally causes the Deployment controller to create or scale ReplicaSets, which in turn maintain Pods.

This layered ownership is why manually editing controller-owned child resources is often ineffective or short-lived: the owning controller can reconcile them back toward its own desired state.

### Owner references

Owner references let Kubernetes model ownership between objects and support garbage collection of dependent resources.

### Finalizers

A finalizer can prevent physical deletion of an object until a controller completes required cleanup work.

An object stuck in `Terminating` often means the deletion request was accepted but one or more finalizers have not completed.

Deleting finalizers blindly can bypass cleanup and leak external resources. Diagnose the owning controller first.

---

## 8. Pods: the scheduling unit

A Pod is Kubernetes' basic scheduling unit.

A Pod can contain one or more containers that intentionally share parts of their execution environment, such as networking and mounted volumes.

A Pod is **not** intended to be treated like a durable virtual machine identity.

Higher-level controllers usually create replacement Pods when instances fail or when a rollout changes the template.

This has several consequences:

- applications should not depend on a specific Pod name remaining forever;
- stable access should normally use a Service or another discovery mechanism;
- persistent application data should not depend on writable container filesystems surviving replacement;
- stateful identity should use an appropriate workload and storage design.

---

## 9. Workload controllers

Different workload APIs encode different lifecycle semantics.

### Deployment

Deployments are the common choice for stateless or replaceable application replicas.

They provide declarative rollout and rollback behavior by managing ReplicaSets.

Typical uses:

- web frontends;
- APIs;
- worker services where any healthy replica can replace another.

### ReplicaSet

ReplicaSets maintain a requested number of matching Pods.

Most users do not manage ReplicaSets directly when a Deployment already owns that responsibility.

### StatefulSet

StatefulSets are designed for workloads that need stable identity, ordered behavior, or stable storage association.

They are useful for some databases, replicated stateful services, and systems where interchangeable anonymous replicas are not sufficient.

StatefulSet does not magically make a database correct, replicated, or backed up. Application-level distributed-system semantics still matter.

### DaemonSet

A DaemonSet maintains Pods across a set of eligible nodes, commonly one per node.

Typical uses include:

- node monitoring agents;
- log collectors;
- networking components;
- storage/node plugins.

### Job and CronJob

Jobs represent finite work that should run to completion. CronJobs create Jobs according to a schedule.

Batch semantics are different from continuously running services, so forcing all workloads through Deployments is usually a modeling error.

---

## 10. Scheduling in detail

The default scheduler works through a multi-stage framework.

At a high level:

1. identify candidate nodes;
2. filter out nodes that cannot satisfy hard requirements;
3. score feasible nodes according to active policies and plugins;
4. select a node;
5. bind the Pod to that node through the API.

If no feasible node exists, the Pod remains unscheduled rather than being silently forced onto an unsuitable node.

### Resource requests

Resource requests are important scheduler inputs.

For CPU and memory, the scheduler reasons about declared requests rather than assuming current instantaneous usage is a safe predictor of future demand.

A cluster can therefore have low observed CPU usage while a Pod remains Pending because declared requests no longer fit on any eligible node.

### Resource limits

Limits are primarily runtime enforcement constraints rather than placement promises.

On Linux, container runtime configuration typically maps CPU and memory constraints onto kernel cgroups.

CPU limits commonly cause throttling; memory limits can result in out-of-memory termination under pressure.

### Node selectors and affinity

Node selectors and node affinity let workload authors constrain or prefer placement based on node labels and topology.

Use them when placement is semantically required, not merely to micromanage ordinary balancing.

### Pod affinity and anti-affinity

These rules can attract or repel Pods relative to other workloads.

They are useful for co-location or failure-domain separation, but complex affinity rules can significantly reduce the set of feasible placements.

### Topology spread constraints

Topology spread constraints let workloads express distribution goals across zones, nodes, or other topology domains.

They are often a clearer reliability mechanism than large ad hoc anti-affinity expressions.

### Taints and tolerations

Taints mark nodes as unsuitable for ordinary Pods unless the Pod has an appropriate toleration.

A toleration permits scheduling onto a tainted node; it does not force the scheduler to choose that node.

### `nodeName`

Directly assigning `.spec.nodeName` bypasses normal scheduling.

It is therefore a sharp tool. If the real requirement can be expressed through labels, affinity, taints, or other scheduling constraints, those mechanisms preserve more of Kubernetes' placement logic.

### Priority and preemption

Priority can influence scheduling order and allow higher-priority workloads to displace lower-priority workloads when necessary.

Priority is not a substitute for capacity planning. Overusing high priority merely converts resource shortage into a different failure mode.

---

## 11. Resources, QoS, and capacity planning

Kubernetes makes a distinction between **what a workload asks the scheduler to reserve conceptually** and **what the runtime may enforce**.

### Requests

Requests help answer: "Can this Pod reasonably fit on this node?"

### Limits

Limits answer: "What ceiling should the runtime and kernel enforce for this container or Pod resource?"

### Actual usage

Actual usage answers a different question: "What is the workload consuming right now?"

Those three values should not be conflated.

A healthy production platform normally needs:

- representative requests;
- carefully justified limits;
- monitoring of actual usage and throttling/OOM behavior;
- headroom for node and zone failures;
- quotas and policy where teams share capacity.

Bad requests can reduce utilization or create unschedulable Pods. Bad limits can create throttling, OOM loops, or noisy failure patterns.

---

## 12. Container lifecycle and probes

Kubelet can run startup, readiness, and liveness probes. They answer different questions.

### Startup probe

"Has this application finished starting?"

A startup probe can protect slow-starting applications from premature liveness failure.

### Readiness probe

"Should this instance currently receive traffic?"

A failed readiness probe removes the Pod from normal Service backend readiness without necessarily restarting the container.

### Liveness probe

"Is this container stuck in a state where restart is an appropriate recovery action?"

Repeated liveness failure can restart the container.

### Why probe design matters

A probe is part of the control system.

A bad liveness probe can turn a transient dependency outage into a restart storm. A readiness probe that checks too many downstream dependencies can remove every replica from service at exactly the moment degraded service would have been preferable.

Probe endpoints should represent the recovery semantics you actually want.

---

## 13. Graceful termination

Pod deletion is normally a lifecycle, not an instantaneous kill.

Applications should understand:

- process signals;
- termination grace periods;
- connection draining;
- readiness transitions;
- preStop hooks where they are genuinely needed;
- shutdown ordering for sidecars and dependencies.

The goal is to make ordinary rollout, scaling, drain, and eviction events unsurprising to the application.

---

## 14. Networking mental model

Kubernetes networking is layered.

A simplified model is:

```text
external client
      |
      v
LoadBalancer / Gateway / Ingress
      |
      v
    Service
      |
      v
 EndpointSlices
      |
      v
     Pods
      |
      v
 Pod network / CNI implementation
```

### Pod networking

Pods need network connectivity implemented by the cluster's networking stack.

The exact dataplane can vary substantially between clusters.

### Service

A Service provides a stable logical endpoint for a changing set of backends.

Services decouple client discovery from the lifecycle of individual Pods.

### EndpointSlice

EndpointSlices represent scalable sets of network endpoints associated with Services.

Service routing implementations watch Services and endpoint information to program their data plane.

### DNS

Cluster DNS commonly gives Services and Pods discoverable DNS names according to Kubernetes conventions.

A large class of "network" incidents are actually DNS, selector, endpoint, readiness, or policy failures, so diagnosis should follow the layers rather than assume packets are always the first problem.

### NetworkPolicy

NetworkPolicy is a Kubernetes policy API for controlling allowed traffic at the Pod network level.

The API object existing does not by itself guarantee enforcement. The installed network implementation must support and enforce the relevant policy semantics.

### Ingress and Gateway API

Ingress is the older Kubernetes API for HTTP/HTTPS ingress routing.

Gateway API provides a broader, role-oriented family of APIs for traffic-routing and infrastructure integration. It is implemented through controllers rather than by the API objects alone.

### LoadBalancer Services

`type: LoadBalancer` can ask an integrated environment to provision or connect an external load-balancing resource.

The exact behavior depends on the infrastructure and controller implementation.

---

## 15. Networking failure diagnosis

When traffic fails, isolate the layer:

```text
Does the Pod process listen?
        |
        v
Is the Pod Ready?
        |
        v
Does the Service selector match?
        |
        v
Are EndpointSlices populated?
        |
        v
Does Service routing work?
        |
        v
Does NetworkPolicy allow the path?
        |
        v
Does DNS resolve correctly?
        |
        v
Does Gateway / Ingress / LB route correctly?
```

This is more efficient than changing random CNI settings before verifying whether the Service has any backends.

Useful commands include:

```bash
kubectl get pods -o wide
kubectl get svc
kubectl get endpointslices
kubectl describe svc <service>
kubectl get networkpolicy
kubectl get events --sort-by=.lastTimestamp
```

The commands are diagnostic views of the object graph; they are not a substitute for understanding which layer should own the failure.

---

## 16. Storage model

Containers are replaceable, but many applications need durable data.

Kubernetes separates workload identity from storage provisioning through volume APIs.

### PersistentVolume

A PersistentVolume represents provisioned storage available to the cluster.

### PersistentVolumeClaim

A PersistentVolumeClaim represents a workload's request for storage.

### StorageClass

A StorageClass describes a class of storage and the provisioner/parameters used for dynamic provisioning.

### CSI

The Container Storage Interface allows Kubernetes to integrate storage systems through external drivers rather than embedding every provider directly in core Kubernetes.

### Binding and topology

Storage can constrain scheduling. A Pod that requires a volume cannot simply run on any node if the storage system or topology does not permit attachment there.

This is one reason scheduler and storage behavior must be understood together.

### Reclaim policy

Storage lifecycle after claim release depends on reclaim policy and provisioner behavior.

Choosing `Delete` versus `Retain` has consequences for data-loss risk and manual cleanup.

### Stateful applications

Kubernetes can provide stable storage plumbing, but it does not replace application-level concerns such as:

- replication;
- transaction semantics;
- leader election;
- quorum;
- backups;
- point-in-time recovery;
- data migration;
- restore testing.

A StatefulSet plus a PVC is not a complete database reliability strategy.

---

## 17. Configuration: ConfigMaps and Secrets

ConfigMaps and Secrets allow configuration data to be represented as API objects and delivered to workloads.

### ConfigMap

Use ConfigMaps for non-secret configuration that belongs in cluster object state.

### Secret

Secret objects are intended for sensitive data, but the word "Secret" should not be interpreted as an automatic guarantee of encryption, least privilege, safe application logging, or secure external distribution.

Security depends on:

- API access policy;
- encryption-at-rest configuration where required;
- secret rotation;
- node and workload access;
- how applications read and log values;
- whether secrets are copied into images, manifests, shell history, or CI logs.

For high-assurance systems, external secret-management integrations may be appropriate.

---

## 18. API request security path

A useful access-control model is:

```text
request
  |
  v
authentication
  |
  v
authorization
  |
  v
admission
  |
  v
persist / act
```

### Authentication

Authentication establishes the requesting identity.

Depending on cluster configuration, identities can come from client certificates, bearer tokens, service-account tokens, external identity integrations, or other supported mechanisms.

### Authorization

Authorization decides whether an authenticated identity may perform the requested operation.

RBAC is a common authorization model.

### RBAC objects

RBAC uses four central object kinds:

- Role;
- ClusterRole;
- RoleBinding;
- ClusterRoleBinding.

The important operational principle is **least privilege**. Broad cluster-admin access is easy to grant and difficult to reason about later.

### Admission

Admission runs after authentication and authorization and can validate or mutate accepted object requests according to cluster policy.

Built-in admission controllers and admission webhooks can enforce policy that cannot be expressed through basic RBAC alone.

### Pod Security Admission

Pod Security Admission can enforce Pod Security Standards at namespace boundaries.

It helps constrain dangerous Pod configurations but should be part of a larger security model rather than treated as the only workload-security layer.

---

## 19. Workload security boundaries

Kubernetes workloads ultimately execute processes on machines. The strength of isolation depends on the container runtime, kernel, workload configuration, and surrounding infrastructure.

Important controls include:

- running as non-root where practical;
- minimizing Linux capabilities;
- using seccomp profiles;
- avoiding privileged containers unless strictly required;
- constraining host namespace access;
- avoiding unnecessary `hostPath` mounts;
- using read-only filesystems where compatible;
- limiting service-account permissions;
- enforcing NetworkPolicy where supported;
- protecting admission webhook credentials and configuration;
- constraining image provenance and registry access.

A privileged Pod with host mounts can cross boundaries that ordinary namespaced containers cannot.

The container boundary should therefore not be mistaken for a VM-strength tenant boundary by default.

---

## 20. Supply-chain considerations

Kubernetes frequently automates image rollout, so image trust becomes a cluster security concern.

Useful controls can include:

- immutable image digests for high-assurance deployments;
- private or controlled registries;
- vulnerability scanning;
- signed image or provenance policies;
- admission checks;
- least-privilege pull credentials;
- avoiding mutable `latest` tags for reproducible releases.

Kubernetes can enforce or integrate many of these policies, but it cannot make an untrusted artifact trustworthy simply by scheduling it.

---

## 21. Extensibility model

A major reason Kubernetes became a platform rather than only an orchestrator is that its API and reconciliation model are extensible.

### CustomResourceDefinition

CRDs let operators add new API resource kinds to a cluster.

A CRD defines data shape and API storage; it does not by itself implement useful behavior.

### Custom controllers and Operators

A controller watches custom or built-in resources and reconciles external or cluster state.

The "Operator" pattern usually means packaging domain-specific operational knowledge into controllers plus custom resources.

### Admission webhooks

Webhooks can validate or mutate API requests.

Because they sit on the API request path, poorly designed admission webhooks can become a control-plane availability or latency problem.

### Scheduler framework

The scheduler exposes plugin extension points for queueing, filtering, scoring, binding, and related scheduling phases.

### CRI

CRI separates kubelet from the concrete container runtime.

### CSI

CSI separates Kubernetes storage APIs from concrete storage providers.

### Networking integrations

Pod networking and policy are provided by cluster networking implementations rather than one hard-coded universal dataplane.

This delegated architecture gives Kubernetes portability, but it also means two Kubernetes clusters can behave differently in networking, storage, identity, and observability despite exposing the same core API.

---

## 22. Kubernetes and containerd

Kubernetes and containerd occupy different layers.

```text
Kubernetes
  |
  | desired state, scheduling, orchestration
  v
kubelet
  |
  | CRI
  v
containerd
  |
  | runtime / image / snapshot / task lifecycle
  v
OCI runtime + Linux kernel
```

Kubernetes should not be explained as if it directly implements Linux container isolation itself.

Containerd should not be explained as if it performs cluster scheduling or Deployment reconciliation.

Keeping these boundaries clear makes runtime failures much easier to diagnose.

Related OpenDevIndex module: `tool/containerd`.

---

## 23. Kubernetes and Docker

Docker and Kubernetes are also different layers.

Docker is commonly used to build and test container images and provides its own developer-facing container platform.

Kubernetes orchestrates workloads across clusters and communicates with node runtimes through CRI.

An image built by Docker can be stored in an OCI-compatible registry and executed by a Kubernetes node runtime without Docker Engine being the runtime on that node.

Related OpenDevIndex module: `tool/docker`.

---

## 24. Observability

Kubernetes produces several distinct classes of operational signal:

- API object status and conditions;
- Events;
- component metrics;
- kubelet and node metrics;
- application metrics;
- container stdout/stderr logs;
- control-plane logs;
- runtime, CNI, and CSI logs;
- distributed traces from applications and infrastructure where configured.

No single signal is sufficient.

### `kubectl get`

Useful for current summarized object state.

### `kubectl describe`

Useful for detailed object state, conditions, events, and relationships.

### Events

Events provide recent diagnostic context but should not be treated as a durable audit or logging database.

### Logs

A Pod restart can erase the simplest view of current container output. Production logging normally needs a cluster-level collection and retention design.

### Metrics

Control-plane and node metrics help separate API latency, scheduler behavior, kubelet health, resource pressure, and application symptoms.

### Distributed tracing

For microservice request-path debugging, cluster health alone cannot explain application-level latency propagation. Application tracing can complement Kubernetes infrastructure telemetry.

---

## 25. A practical debugging workflow

Kubernetes incidents become easier when diagnosis follows ownership boundaries.

### 1. Start with the high-level workload

```bash
kubectl get deployment,statefulset,daemonset,job
```

Ask whether the controller reports the desired number of ready/available replicas.

### 2. Inspect Pods

```bash
kubectl get pods -o wide
kubectl describe pod <pod>
```

Check phase, conditions, restart count, node assignment, image state, mounts, probe failures, and recent events.

### 3. If the Pod is Pending, diagnose scheduling

Look for:

- insufficient requested resources;
- affinity or selector mismatch;
- taints without tolerations;
- topology constraints;
- unbound storage;
- quota or policy rejection.

### 4. If the Pod is scheduled but not starting, diagnose the node boundary

Look at:

- kubelet;
- container runtime;
- image pulls;
- CNI setup;
- CSI mounts;
- sandbox creation;
- node pressure.

### 5. If the Pod is running but traffic fails, follow the networking chain

```bash
kubectl get pods
kubectl get svc
kubectl get endpointslices
kubectl get networkpolicy
```

Verify readiness, selectors, endpoints, DNS, policy, and ingress/gateway layers.

### 6. If control-plane operations fail, test the API path

Separate:

- client authentication;
- authorization;
- admission;
- API server availability;
- etcd health;
- controller or scheduler health.

### 7. Do not delete evidence first

Immediately deleting Pods, removing finalizers, restarting every control-plane component, or flushing networking state can destroy the evidence needed to identify the original failure.

---

## 26. Common failure modes

### Pods stuck Pending

Typical causes:

- resource requests do not fit;
- node constraints are too strict;
- required volumes cannot bind;
- taints block placement;
- scheduler is unhealthy;
- quota or admission policy rejects supporting objects.

### CrashLoopBackOff

This is a symptom of repeated container failure and restart behavior, not a root cause.

Investigate application exit status, configuration, secrets, dependencies, probes, filesystem permissions, and resource limits.

### ImagePullBackOff

Typical causes:

- image name or tag does not exist;
- registry authentication fails;
- node cannot reach the registry;
- rate limits or registry outages;
- architecture/platform mismatch.

### Service has no traffic

Typical causes:

- selector does not match Pods;
- Pods are not Ready;
- EndpointSlices are empty;
- target ports are wrong;
- policy blocks the path;
- application listens only on an unexpected interface or port.

### DNS failures

A workload may be healthy while cluster DNS or upstream resolver behavior is not.

Check DNS Pods, Services, network reachability, resolver configuration, and query load.

### CNI failures

Pods can be scheduled but fail during sandbox network setup when the node networking implementation is unhealthy or misconfigured.

### CSI failures

Pods can remain Pending or stuck in container creation when volume provisioning, attachment, or mount operations fail.

### Node pressure and eviction

Memory, disk, PID, or other node pressure can trigger evictions or block new work.

The right response is capacity and workload diagnosis, not simply recreating the same Pods indefinitely.

### Stuck namespace or object deletion

Finalizers often explain objects that remain in terminating state.

Find the controller that owns the unfinished cleanup before removing finalizers manually.

---

## 27. High availability

A highly available Kubernetes cluster requires more than "three control-plane nodes."

### API server

Multiple API-server instances can provide redundancy behind an appropriate endpoint/load-balancing design.

### etcd quorum

etcd uses quorum-based consensus. Member count, placement, latency, disk performance, backup, and restore procedures materially affect control-plane reliability.

Adding etcd members is not a general performance scaling strategy; quorum systems trade coordination cost for fault tolerance.

### Scheduler and controller manager

Multiple scheduler/controller-manager instances can use leader election so a healthy instance performs active control work while another can take over.

### Failure domains

Control-plane instances should not all depend on the same single physical or infrastructure failure domain if high availability is a real requirement.

### Backups

High availability reduces some failures. It does not replace backups.

A replicated mistake, bad deletion, corrupted state, credential compromise, or catastrophic provider failure can affect every live replica.

---

## 28. etcd backup and disaster recovery

etcd stores Kubernetes API state and should have a deliberate recovery plan.

Important practices include:

- take consistent snapshots using supported etcd tooling;
- protect snapshots because they can contain sensitive Kubernetes state;
- store backups outside the failure domain of the live control plane;
- document the exact restore procedure;
- test restore rather than assuming a snapshot is useful;
- coordinate API-server and etcd state correctly during disaster recovery.

A backup that has never been restored in a test environment is an unverified recovery hypothesis.

---

## 29. Pod disruptions and maintenance

Not all Pod termination is failure.

Voluntary disruption can happen during:

- node drain;
- cluster upgrade;
- autoscaling;
- administrative maintenance;
- rollout and rescheduling.

### PodDisruptionBudget

A PodDisruptionBudget can constrain some voluntary disruptions so too many replicas are not intentionally removed at once.

It is not a universal availability guarantee. It cannot prevent every involuntary failure, and a badly chosen budget can also block legitimate maintenance.

### Draining nodes

Node drain is a workload lifecycle event. Applications should be designed to terminate and reschedule without depending on one machine forever.

---

## 30. Upgrades and version skew

Kubernetes consists of multiple independently running components, so version compatibility matters during upgrades.

Operational rules are release-sensitive. Always read the version-skew policy and upgrade documentation for the exact releases involved.

For kubeadm-managed clusters, the documented upgrade flow generally stages control-plane and worker upgrades rather than treating the entire cluster as one atomic package update.

Important upgrade preparation includes:

- read release notes;
- verify API deprecations and removals;
- check admission webhooks and CRDs;
- verify CNI, CSI, and runtime compatibility;
- back up critical application state and control-plane state;
- test workloads against the new version;
- drain nodes where required;
- monitor rollout and control-plane health.

Skipping unsupported version transitions can turn a routine upgrade into a recovery exercise.

---

## 31. API evolution and deprecation

Kubernetes API stability is stronger than "every field exists forever."

APIs move through maturity levels and can be deprecated or removed according to project policy.

Platform operators should track:

- deprecated API versions;
- feature gates;
- removed beta APIs;
- CRD conversion requirements;
- webhook compatibility;
- client-library compatibility;
- manifests generated by old tooling.

A cluster upgrade can succeed while an application deployment later fails because its manifests still use a removed API version.

---

## 32. Performance characteristics

Kubernetes performance is not one number.

### API server

Potential bottlenecks include request volume, expensive list/watch patterns, admission latency, serialization, authentication/authorization overhead, and backing-store performance.

### etcd

etcd is sensitive to storage latency and quorum communication. Slow persistence can surface as control-plane latency.

### Scheduler

Scheduler performance depends on Pod arrival rate, cluster size, active scheduling plugins, and how many nodes must be evaluated.

### Controllers

Controllers depend heavily on efficient watches, work queues, retry behavior, and avoiding hot reconciliation loops.

### kubelet

Node-level scale depends on container count, image operations, filesystem/runtime performance, probes, logging, and node resource pressure.

### Networking

Service count, endpoint count, policy complexity, dataplane implementation, conntrack behavior, and underlying network design all matter.

### Storage

Provisioning latency, attach/mount behavior, storage topology, IOPS, and CSI implementation can dominate stateful workload startup time.

### Application architecture

Kubernetes can schedule more replicas, but it cannot remove application bottlenecks such as database contention, synchronized caches, lock contention, or poor sharding.

---

## 33. Autoscaling

Kubernetes supports multiple forms of scaling through built-in APIs and ecosystem controllers.

### Horizontal Pod Autoscaler

HPA adjusts replica count based on observed metrics according to configured policy.

### Cluster/node autoscaling

Node capacity can be adjusted by external or provider-integrated autoscaling systems.

### Important feedback-loop risk

Autoscaling creates another controller in the system.

A poor signal or slow dependency can create oscillation:

```text
latency rises
   -> HPA adds replicas
   -> startup load increases
   -> dependency overload rises
   -> readiness falls
   -> effective capacity falls
```

Scaling policy must therefore be designed with application behavior, startup cost, request limits, and downstream capacity in mind.

---

## 34. Managed Kubernetes versus self-managed Kubernetes

Kubernetes can be operated directly or consumed through managed services.

### Managed service advantages

Depending on provider and service tier:

- reduced control-plane maintenance;
- integrated upgrades and infrastructure provisioning;
- provider-specific identity, load balancing, and storage integrations;
- simpler initial high-availability setup.

### Managed service trade-offs

- provider-specific behavior and APIs;
- version timing controlled partly by the provider;
- less access to some control-plane internals;
- cost model and operational constraints;
- portability is not automatic merely because the workload API is Kubernetes.

### Self-managed advantages

- maximum control over topology, components, and upgrade timing;
- ability to run in environments unsupported by a managed provider;
- deep customization where genuinely required.

### Self-managed trade-offs

You own more of:

- etcd;
- certificates;
- control-plane availability;
- upgrades;
- runtime compatibility;
- network and storage integrations;
- monitoring;
- disaster recovery.

Choosing Kubernetes does not eliminate operations. It changes which operations are standardized and which remain yours.

---

## 35. Trade-offs

### Strengths

- declarative API model;
- mature reconciliation patterns;
- broad ecosystem;
- portable workload primitives;
- extensible controllers and APIs;
- standardized runtime and storage boundaries;
- strong automation surface for platform engineering.

### Costs

- large conceptual surface area;
- distributed control-plane failure modes;
- networking and storage behavior varies by implementation;
- misconfiguration can create security or reliability failures at cluster scale;
- small systems can inherit more operational complexity than they need;
- debugging often requires understanding several independent layers.

### Where Kubernetes can be excessive

For a small application with a few processes, one deployment target, and limited scaling requirements, a simpler platform may be easier to operate and safer for the team.

Kubernetes pays off when its standardized orchestration, API, extensibility, isolation, scheduling, and multi-workload control model solve real problems rather than merely adding fashionable infrastructure.

---

## 36. Alternatives and adjacent systems

The relevant alternative depends on what problem Kubernetes is being used to solve.

Possible alternatives or adjacent approaches include:

- simpler VM/service-manager deployment;
- Docker Compose for single-host development or small deployments;
- Docker Swarm for simpler container clustering;
- HashiCorp Nomad for workload scheduling with a different operational model;
- cloud-provider container platforms that intentionally expose less Kubernetes surface area;
- serverless/FaaS platforms where the application fits event-driven constraints;
- PaaS systems that hide orchestration details behind application-centric interfaces.

Comparisons should focus on desired operational model rather than raw feature counts.

---

## 37. Common mistakes

### Treating Pods like VMs

Pods are replaceable scheduling units. Durable identity and data require explicit design.

### Editing controller-owned Pods directly

The owning controller can recreate or overwrite them. Change the higher-level desired state.

### Omitting resource requests

The scheduler cannot make good placement decisions when workloads provide no useful resource intent.

### Setting every limit aggressively

Overly tight CPU limits cause throttling; tight memory limits can cause OOM churn.

### Using liveness probes as dependency checks

This can amplify downstream outages into restart storms.

### Assuming readiness means healthy forever

Readiness means "eligible for traffic now," not "the application is globally correct."

### Granting cluster-admin broadly

Convenience today becomes an incident-response problem later.

### Assuming Secret means encrypted everywhere

Secrets still require storage, access, rotation, and application-handling controls.

### Using privileged Pods without a precise reason

Privileged access can collapse important host/container boundaries.

### Relying on `hostPath` for durable application data

That couples data to a node and bypasses many normal storage lifecycle guarantees.

### Assuming NetworkPolicy is automatically enforced

The network implementation must support the policy semantics.

### Confusing Docker with the Kubernetes runtime layer

Kubernetes uses CRI-compatible runtimes; Docker-built images do not imply Docker Engine must run on the node.

### Deleting finalizers to "unstick" resources without diagnosis

This can leak infrastructure or skip required cleanup.

### Treating a green control plane as proof the application is healthy

Kubernetes can be healthy while the application is failing at DNS, data, dependency, or business-logic layers.

### Treating a healthy application Pod as proof the platform is healthy

Existing Pods can continue to serve while scheduler, controller, API, or etcd problems prevent future reconciliation.

---

## 38. Small workflow example

Create a simple Deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: web
          image: nginx:1.29
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: 100m
              memory: 64Mi
```

Apply and inspect:

```bash
kubectl apply -f deployment.yaml
kubectl rollout status deployment/web
kubectl get deployment,replicaset,pods
```

The point of the example is the object chain:

```text
manifest
  -> Deployment desired state
  -> ReplicaSet reconciliation
  -> Pod creation
  -> scheduler binding
  -> kubelet execution
```

The CLI is merely one client of the API.

---

## 39. Debugging command map

### Object state

```bash
kubectl get <resource>
kubectl describe <resource> <name>
```

### Change history

```bash
kubectl rollout status deployment/<name>
kubectl rollout history deployment/<name>
```

### Logs

```bash
kubectl logs <pod>
kubectl logs <pod> --previous
```

`--previous` can be especially useful for a container that restarted before you inspected it.

### Events

```bash
kubectl get events --sort-by=.lastTimestamp
```

### Node diagnosis

```bash
kubectl get nodes
kubectl describe node <node>
```

### API inspection

```bash
kubectl api-resources
kubectl explain deployment.spec
```

The goal is to ask the API what objects exist and what the controllers report before modifying the cluster blindly.

---

## 40. Learning path

A productive Kubernetes learning order is:

### Stage 1: prerequisites

Understand:

- Linux processes and namespaces;
- containers and OCI images;
- TCP/IP, DNS, and HTTP;
- filesystems and block/network storage;
- basic distributed-system failure concepts.

OpenDevIndex next hop: `concept/containers`.

### Stage 2: object model

Learn:

- Pod;
- Deployment;
- Service;
- ConfigMap;
- Secret;
- namespace;
- labels/selectors;
- `spec` versus `status`.

### Stage 3: reconciliation

Understand why controllers continuously converge desired and observed state.

This is more important than memorizing `kubectl` commands.

### Stage 4: scheduling and resources

Learn:

- requests and limits;
- node selection;
- taints/tolerations;
- affinity;
- topology spread;
- priority;
- disruptions.

### Stage 5: networking and storage

Learn:

- Service and EndpointSlice;
- cluster DNS;
- Pod networking;
- NetworkPolicy;
- Gateway/Ingress;
- PV/PVC;
- StorageClass;
- CSI.

### Stage 6: security

Learn:

- authentication;
- RBAC;
- service accounts;
- admission;
- Pod Security Admission;
- security contexts;
- secret handling.

### Stage 7: operations

Learn:

- kubelet and runtime boundaries;
- control-plane components;
- observability;
- backup/restore;
- upgrades;
- high availability;
- common node/CNI/CSI failures.

### Stage 8: extension

Learn:

- CRDs;
- controllers/operators;
- admission webhooks;
- scheduler extensions;
- platform APIs and GitOps patterns.

---

## 41. What to learn next

### Containers

Read `concept/containers` to understand the Linux and OCI execution model beneath Kubernetes Pods.

### containerd

Read `tool/containerd` to understand the runtime object model and CRI boundary beneath kubelet.

### Docker

Read `tool/docker` to understand the developer/build/container tooling layer that commonly produces images later deployed through Kubernetes.

Then continue into:

- Linux cgroups and namespaces;
- DNS and service networking;
- distributed consensus and etcd;
- container networking;
- CSI and storage systems;
- identity and PKI;
- observability and SRE;
- GitOps and platform engineering.

---

## 42. Related OpenDevIndex modules

Machine-readable relationships are recorded in `entry.yaml`.

Current deliberate edges:

- `related-to -> concept/containers`
- `integrates-with -> tool/containerd`
- `compatible-with -> tool/docker`

These relationships represent architecture and workflow boundaries rather than generic keyword similarity.

---

## 43. Verification notes

This deep-dive was reviewed on **2026-09-06** against current upstream Kubernetes documentation and canonical project sources.

The following areas are intentionally treated as version-sensitive and should be rechecked before operational decisions:

- supported Kubernetes release and version-skew rules;
- feature-gate maturity and defaults;
- API deprecations/removals;
- scheduler plugin behavior;
- Gateway API maturity and implementation support;
- CNI/CSI/CRI compatibility;
- kubeadm upgrade procedure;
- security defaults;
- admission behavior;
- autoscaling features;
- storage migration and deprecation status.

The stable mental models that should age more slowly are:

- desired state versus observed state;
- API-driven reconciliation;
- controller ownership;
- scheduler placement versus kubelet execution;
- CRI/CNI/CSI delegation boundaries;
- Services decoupling discovery from Pod identity;
- persistent storage being separate from Pod lifecycle;
- security depending on multiple explicit trust boundaries.

---

## 44. Source map

Primary references are maintained in [`sources.md`](sources.md).

Key upstream references include:

- Kubernetes components: https://kubernetes.io/docs/concepts/overview/components/
- Kubernetes objects: https://kubernetes.io/docs/concepts/overview/working-with-objects/
- Kubernetes scheduler: https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/
- Resource management: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
- Workload probes: https://kubernetes.io/docs/concepts/workloads/pods/probes/
- Services and networking: https://kubernetes.io/docs/concepts/services-networking/
- Persistent volumes: https://kubernetes.io/docs/concepts/storage/persistent-volumes/
- Container Runtime Interface: https://kubernetes.io/docs/concepts/containers/cri/
- API access control: https://kubernetes.io/docs/reference/access-authn-authz/
- RBAC: https://kubernetes.io/docs/reference/access-authn-authz/rbac/
- Pod Security Admission: https://kubernetes.io/docs/concepts/security/pod-security-admission/
- etcd operations: https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/
- kubeadm upgrades: https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/

For release-sensitive operational work, prefer the documentation for the exact Kubernetes version in use rather than assuming a current-page default applies to an older cluster.
