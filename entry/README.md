# Argo CD

> Declarative GitOps continuous-delivery platform for Kubernetes that renders desired application state from versioned sources, compares it with live clusters, and reconciles drift through controlled synchronization.

Argo CD is easiest to understand as a **Kubernetes reconciliation control plane for application delivery**. It does not replace Kubernetes, Git, Helm, or an image registry. Instead, it sits between versioned application definitions and one or more Kubernetes APIs, repeatedly answering three questions:

1. What should this application look like?
2. What does the cluster look like now?
3. Should Argo CD only report the difference, or reconcile it?

That distinction is the foundation for operating Argo CD safely.

## Why it matters

Traditional deployment pipelines often push directly into a cluster: a CI job receives credentials, renders manifests, calls `kubectl` or Helm, and exits. After that job ends, the pipeline usually has no durable controller watching for drift.

Argo CD changes the control model. Desired state remains versioned, the controller continues watching live state, and deployment becomes a reconciliation problem rather than a one-shot script execution problem.

This provides several practical benefits:

- deployment intent can be reviewed before it reaches a cluster;
- desired and live state can be compared continuously;
- drift becomes visible instead of remaining implicit;
- synchronization can be manual or automated;
- cluster access can be concentrated in the delivery control plane rather than distributed to every CI job;
- deployment history can be related back to source revisions;
- multi-cluster application fleets can be generated and reconciled consistently;
- policy boundaries can be expressed with projects, destinations, source allowlists, and RBAC.

None of these benefits are automatic. A badly designed Argo CD installation can centralize excessive privilege, hide real drift behind broad ignore rules, delete resources unexpectedly with pruning, or multiply mistakes across many clusters with ApplicationSets. The technology is powerful because the reconciliation loop is persistent; that is also why its failure modes deserve careful design.

---

## The shortest correct mental model

A useful simplified flow is:

```text
versioned source
     |
     v
source revision resolution
     |
     v
manifest generation
  Git / Helm / Kustomize / directory / supported plugins
     |
     v
desired Kubernetes objects
     |
     +--------------------+
     |                    |
     v                    v
live Kubernetes state   resource ownership/tracking
     |                    |
     +---------+----------+
               |
               v
        compare + health
               |
        Synced / OutOfSync
        Healthy / Degraded / ...
               |
               v
        sync decision/policy
               |
               v
 apply / create / update / prune / hooks
               |
               v
        Kubernetes API
               |
               +----> reconciliation repeats
```

The important word is **generated**. The desired state Argo CD compares against the cluster is not always the raw file content in Git. Helm charts, Kustomize overlays, directory generators, parameters, and plugins can transform source material before comparison.

Therefore:

```text
Git content != necessarily final desired Kubernetes objects
```

For debugging, always separate **source resolution**, **manifest generation**, **diffing**, **sync execution**, and **resource health**. They are different stages with different failure modes.

---

## What Argo CD is — and is not

Argo CD is:

- a Kubernetes-native continuous-delivery and GitOps reconciliation platform;
- a controller-based system that compares desired and live application state;
- a manifest-generation and synchronization control plane;
- a multi-cluster application delivery system;
- a UI, CLI, and API for application status and operations;
- a policy surface for projects, destinations, repositories, and user permissions.

Argo CD is not:

- a container runtime;
- a Kubernetes scheduler;
- a CI build system;
- an image registry;
- a secret manager by itself;
- a replacement for Git;
- a replacement for Helm when Helm's own release object semantics are specifically required;
- a guarantee that a `Synced` application is healthy;
- a guarantee that a `Healthy` application matches source state;
- a substitute for Kubernetes admission, network policy, workload identity, or supply-chain controls.

A common architecture is:

```text
developer change
    |
    v
CI: test/build/scan/publish image
    |
    v
Git change to desired deployment state
    |
    v
Argo CD observes desired revision
    |
    v
Argo CD renders + compares + syncs
    |
    v
Kubernetes controllers converge workloads
```

That division keeps **artifact production** and **cluster reconciliation** separate.

---

# Architecture

## Main control-plane components

The upstream architecture separates responsibilities into several services and controllers.

### API server

The Argo CD API server exposes the API used by the Web UI, CLI, and automation clients. It is responsible for concerns such as:

- application management and status access;
- synchronization and rollback operations;
- authentication and identity-provider integration;
- authorization/RBAC enforcement;
- repository and cluster credential management interfaces;
- webhook handling for faster source refreshes.

The API server is a control interface. It is not the component that continuously performs the application reconciliation loop.

### Repository server

The repository server is the manifest-generation boundary. Given source information such as repository URL, revision, path, chart settings, or renderer parameters, it produces Kubernetes manifests for comparison and synchronization.

Conceptually:

```text
source coordinates + renderer configuration
                  |
                  v
             repo-server
                  |
                  v
        rendered Kubernetes objects
```

This makes the repository server an important trust boundary. Inputs can include repositories and templates controlled by different teams. Custom manifest-generation plugins expand that trust boundary further because they can execute additional tooling.

### Application controller

The application controller is the heart of Argo CD's reconciliation model. It:

- watches `Application` state;
- obtains desired manifests;
- observes live Kubernetes resources;
- compares desired and live state;
- determines synchronization status;
- executes synchronization when requested or permitted by policy;
- invokes lifecycle hooks;
- tracks operation results and application status.

A user closing the browser does not stop this loop. That persistence is what distinguishes controller-driven delivery from a transient deployment script.

### ApplicationSet controller

The ApplicationSet controller generates and maintains `Application` resources from templates and generators.

It is best understood as **reconciliation one level above Applications**:

```text
ApplicationSet
      |
      v
 generator inputs
      |
      v
 templated Applications
      |
      v
 Argo CD Application reconciliation
      |
      v
 Kubernetes resources
```

This is extremely useful for fleets, but it also means a generator mistake can affect many Applications at once.

### Redis

Redis is used as a cache layer that helps reduce repeated work and pressure on Git and Kubernetes APIs. It should be treated as important operational infrastructure, but not confused with the declarative source of application intent.

### Identity integration

Argo CD can integrate with external OIDC identity providers, directly or through supported identity components such as Dex depending on installation design. Authentication establishes identity; RBAC and project policy determine what that identity is allowed to do.

---

# Core object model

Understanding Argo CD becomes much easier once the major objects are separated.

## Application

An `Application` describes one reconciliation unit. At a high level it binds:

```text
source + revision + rendering settings
                   |
                   v
            desired manifests
                   |
                   v
       destination cluster/namespace
```

Important fields include:

- project membership;
- source repository, chart, or other supported source coordinates;
- target revision;
- path/chart/rendering configuration;
- destination cluster or server;
- destination namespace;
- sync policy;
- sync options;
- diff customizations;
- retry behavior;
- optional finalizers controlling cascading deletion behavior.

An `Application` is not merely a bookmark to a Git directory. It is the durable declaration of how Argo CD should derive, compare, and optionally reconcile application state.

## AppProject

An `AppProject` is a policy boundary and organizational boundary for Applications.

Projects can restrict:

- which source repositories are trusted;
- which destination clusters and namespaces are allowed;
- which Kubernetes resource kinds are permitted or denied;
- project-scoped roles and application permissions.

For multi-team installations, project design is security architecture, not just folder organization.

## ApplicationSet

An `ApplicationSet` generates Applications from parameter sets.

Common generator families include:

- fixed lists;
- registered clusters;
- Git directories or files;
- SCM repositories;
- pull requests;
- matrix combinations;
- merge/override combinations;
- cluster-decision resources;
- plugins.

The generated `Application` objects are then reconciled by Argo CD normally.

## Desired resources

These are the Kubernetes objects produced after source resolution and rendering.

Examples:

- Namespace
- Deployment
- StatefulSet
- Service
- ConfigMap
- Secret
- Ingress or Gateway resources
- CustomResourceDefinition
- arbitrary custom resources

Argo CD compares these generated objects with live API objects.

## Live resources

Live resources are the objects currently observed from Kubernetes.

The live object may differ from the submitted desired object because of:

- API defaulting;
- mutating admission webhooks;
- controllers changing fields;
- operators updating custom resources;
- server-side apply ownership;
- external automation;
- emergency manual edits;
- fields that should never have been committed as desired state.

This is why a useful diff engine must understand Kubernetes behavior rather than compare raw YAML text.

---

# The reconciliation pipeline

A practical debugging model is to think in stages.

## Stage 1 — resolve the source

Argo CD must first identify the requested source revision.

Depending on configuration this may mean resolving:

- a Git branch;
- a Git tag;
- a commit;
- a Helm chart version;
- another supported versioned artifact reference.

Production environments generally benefit from revisions that make promotion and rollback behavior explicit. Tracking a moving branch or broad version range is operationally different from pinning an immutable revision.

A webhook can accelerate refresh when source changes, but webhook delivery should be treated as an optimization rather than the sole correctness mechanism. Periodic reconciliation remains important when events are delayed, lost, or misconfigured.

## Stage 2 — generate manifests

The repository server renders the source into Kubernetes objects.

A generation failure means the system may never reach diffing or synchronization.

Typical causes include:

- invalid YAML or templates;
- missing Helm values;
- unavailable chart dependencies;
- repository authentication failure;
- TLS or CA problems;
- unsupported renderer options;
- custom plugin failure;
- nondeterministic templates;
- incompatible tool versions.

A manifest-generation error is not a Kubernetes apply error. Diagnose the correct stage.

## Stage 3 — identify managed resources

Argo CD needs to associate live objects with the Application that manages them.

Current Argo CD resource tracking commonly uses its tracking annotation, with alternative tracking modes available for interoperability.

Resource ownership matters because Argo CD must decide:

- which live objects correspond to desired objects;
- which objects are extraneous;
- which objects may be eligible for pruning;
- whether another Application is already managing the same resource.

Ownership collisions are dangerous. Two reconcilers repeatedly writing the same object can produce oscillation, confusing diffs, or destructive outcomes.

## Stage 4 — compare desired and live state

Argo CD calculates synchronization status from the relationship between rendered desired objects and live resources.

The two most important synchronization states are conceptually:

- `Synced` — desired and tracked live state match according to comparison rules;
- `OutOfSync` — a meaningful difference exists.

This comparison is richer than textual YAML equality.

## Stage 5 — assess health

Health is a separate dimension.

Examples:

```text
Synced + Healthy
```

Desired and live state match, and the workload appears healthy.

```text
Synced + Degraded
```

The desired configuration is present, but the application is unhealthy.

```text
OutOfSync + Healthy
```

The live workload may still be functioning, but it no longer matches desired state.

Treating sync status and health as interchangeable hides important incidents.

## Stage 6 — decide whether to synchronize

A sync can be:

- manually initiated;
- automatically triggered by OutOfSync state when auto-sync is enabled;
- retried according to policy;
- triggered by drift when self-heal is enabled.

The sync policy determines whether detection becomes action.

## Stage 7 — execute the synchronization plan

Argo CD applies resources according to ordering, hooks, waves, sync options, and pruning rules.

This is where desired-state reconciliation becomes mutation of the cluster.

## Stage 8 — observe the result

After changes are submitted, Kubernetes controllers continue their own reconciliation loops.

Argo CD then observes those resulting objects and health states.

This creates nested control loops:

```text
Argo CD controller
    |
    v
Kubernetes API objects
    |
    v
Deployment / StatefulSet / Operator / other controllers
    |
    v
Pods, endpoints, volumes, cloud resources, etc.
```

A failed workload rollout can therefore be caused below Argo CD even if Argo CD successfully applied the desired objects.

---

# Sync status versus health

This distinction deserves explicit treatment.

## Sync answers

> Does the tracked live configuration match the desired configuration produced by Argo CD?

## Health answers

> Does the observed resource status look operational according to Argo CD's health logic?

These are orthogonal.

A deployment may be perfectly synchronized to a manifest that references a broken image. Conversely, a manually modified deployment may be healthy but OutOfSync.

For custom resources, health is more complicated because CRDs do not share one universal status schema. Argo CD supports custom health logic, including Lua-based customization, where the default assessment is insufficient.

Do not suppress health problems merely to make the dashboard green. Health customization should encode actual controller semantics.

---

# Diffing and drift

## Why false drift happens

Persistent OutOfSync status after a successful sync is commonly caused by one of several patterns:

- Kubernetes drops invalid or unknown fields;
- admission mutates objects;
- a controller reorders or normalizes fields;
- another controller owns a field;
- generated values are nondeterministic;
- pruning is disabled while obsolete resources remain;
- a Helm template produces random data;
- the desired manifest incorrectly includes controller-owned status.

The correct response is not automatically to ignore the field.

First ask:

1. Is the desired manifest wrong?
2. Is another controller legitimately authoritative for this field?
3. Is the resource being mutated intentionally?
4. Is the rendering process deterministic?
5. Is there an ownership conflict?

Only then decide whether diff customization is appropriate.

## Ignore differences

Argo CD can ignore selected differences using mechanisms such as JSON pointers, JQ expressions, and managed-field-manager rules.

These controls are useful for known Kubernetes/controller behavior, but broad ignore rules create a monitoring blind spot.

A dangerous anti-pattern is:

```text
persistent drift -> ignore entire field/object class -> dashboard becomes green
```

A better pattern is:

```text
persistent drift
   |
   v
identify writer + ownership semantics
   |
   v
fix source or ownership when possible
   |
   v
ignore only the minimum legitimate difference
```

---

# Synchronization modes

## Manual sync

With manual synchronization, Argo CD reports drift but waits for an explicit operation.

This is useful where:

- deployment approval is required;
- changes need a human checkpoint;
- destructive transitions need inspection;
- teams are introducing GitOps gradually.

The trade-off is slower convergence and the possibility that known drift remains unresolved.

## Automated sync

Automated sync allows Argo CD to reconcile when an Application becomes OutOfSync.

A major benefit is that a CI pipeline does not need to call Argo CD or the Kubernetes API for every deployment. The pipeline can update the desired source, and the controller converges the cluster.

Automation should be evaluated separately for each environment and failure domain.

## Self-heal

Self-heal allows live-cluster drift to trigger automated reconciliation back toward desired state.

This is useful for enforcing declarative ownership, but it changes incident procedures. An operator performing an emergency manual edit may see Argo CD revert it.

Teams should define a deliberate break-glass procedure rather than discovering this during an outage.

## Pruning

Pruning removes tracked resources that no longer exist in desired state.

Without pruning:

```text
removed from source != necessarily removed from cluster
```

With pruning enabled, source deletion can become cluster deletion.

That makes review of rename/move/delete changes especially important.

## Allow-empty

Automated pruning normally includes safety behavior around applications that render no resources. Allow-empty weakens that guard deliberately and should be enabled only when an empty desired set is a legitimate state.

---

# Sync options and apply semantics

Argo CD exposes sync options because Kubernetes mutation semantics are not one-size-fits-all.

Examples include:

- disabling prune for selected resources;
- requiring confirmation before prune/delete;
- applying only OutOfSync resources;
- pruning last;
- server-side apply;
- replace/create semantics;
- forced delete/create behavior;
- failing when a resource is already shared by another Application;
- respecting configured ignored differences during sync.

These options are operational controls, not cosmetic flags.

## Replace and force deserve special caution

Replacing or deleting/recreating a resource can cause interruption even when the desired YAML appears small.

Potential consequences include:

- recreated Pods;
- new immutable resource identities;
- Service or workload interruption;
- storage attachment changes;
- loss of fields maintained by other managers;
- outage while a replacement becomes ready.

Use destructive sync options only when their Kubernetes object-lifecycle consequences are understood.

## Server-side apply

Server-side apply can improve field-ownership behavior in some environments, especially where multiple field managers participate.

However, it does not eliminate ownership design. Managed field conflicts still need to be interpreted, not hidden.

---

# Hooks, phases, and waves

Argo CD supports synchronization hooks and waves for ordered rollout behavior.

## Phases

Common hook phases include:

- `PreSync`
- `Sync`
- `PostSync`
- `SyncFail`
- deletion-related hooks where supported

Hooks are Kubernetes resources, often Jobs, executed as part of synchronization lifecycle behavior.

Use cases include:

- database migration before application rollout;
- smoke tests after rollout;
- external notification or cleanup tasks;
- controlled failure handling.

## Waves

Sync waves provide ordering within a synchronization operation.

Lower-numbered waves run before higher-numbered waves. Negative waves can run before the default wave.

A common pattern is:

```text
wave -2: namespaces / foundational policy
wave -1: CRDs or prerequisite controllers
wave  0: application workloads
wave  1: dependent services
wave  2: validation jobs
```

Do not overuse waves to simulate a general-purpose workflow engine. They are useful for deployment ordering, but complex orchestration often belongs elsewhere.

## Deadlock pattern

A poorly designed early wave can block every later wave if it never becomes healthy.

When sync appears stuck, inspect:

- the first unsatisfied wave;
- hook status;
- health calculation;
- CRD/controller readiness;
- dependency assumptions.

---

# Helm integration

Argo CD's Helm integration is frequently misunderstood.

Argo CD uses Helm primarily to **render charts into manifests**. The lifecycle of the deployed application is then managed by Argo CD.

Conceptually:

```text
Helm chart + values
       |
       v
   helm template
       |
       v
rendered Kubernetes manifests
       |
       v
Argo CD diff + sync + health
```

This differs from directly running:

```text
helm install / helm upgrade
```

and relying on Helm's own release-management workflow as the primary controller of deployment history.

This distinction matters when debugging labels, hooks, release names, ownership, rollback expectations, and tool interoperability.

## Values precedence

Helm values can be supplied through several Argo CD configuration paths. When multiple mechanisms are combined, precedence matters. Keep the number of override layers small enough that a reviewer can predict the rendered output.

A good operational rule is:

> if a production value cannot be explained from source review without running several hidden override layers, the deployment model is too opaque.

## Nondeterministic templates

Helm templates that generate random data can produce perpetual drift because each render may differ from the previous render.

GitOps works best when the same source revision and parameters produce the same desired manifests.

---

# Git as a source of desired state

Git provides several properties Argo CD can leverage:

- immutable commits;
- reviewable diffs;
- branch and tag references;
- authorship history;
- revertable changes;
- integration with CI and policy automation.

But using Git does not automatically make a workflow GitOps-safe.

## Avoid hidden desired state

If important production configuration lives in:

- manual UI overrides;
- ad-hoc CLI parameters;
- untracked cluster edits;
- external scripts unknown to reviewers;

then Git is no longer a complete explanation of the desired deployment.

Parameter overrides may take precedence over repository state, so inspect them when rendered output does not match expectations.

## Mutable revisions

Tracking a branch such as `main` is convenient, but the meaning of that reference changes over time.

Pinning a commit or explicit release reference improves reproducibility where exact rollback and auditability matter.

The correct strategy depends on the promotion model.

---

# ApplicationSet and fleet management

ApplicationSet is where Argo CD becomes a fleet-management system.

## Generator mental model

A generator emits parameter sets. The template turns each parameter set into an `Application`.

```text
input inventory
    |
    v
generator
    |
    v
parameter sets
    |
    v
template
    |
    v
Applications
```

Examples:

### Cluster generator

Use the registered cluster inventory to create Applications per selected cluster.

### Git generator

Use repository directories or files to derive Applications.

### Pull-request generator

Create ephemeral Applications for matching pull requests.

### Matrix generator

Combine parameter sets from two generators, producing combinations.

### Merge generator

Overlay matching parameter sets to apply overrides.

## Fleet risk

The power of ApplicationSet is multiplication.

A template bug affecting one generated application definition can become:

```text
1 template mistake x 100 clusters = 100 incorrect Applications
```

Therefore changes to:

- generator selectors;
- project assignment;
- destinations;
- deletion policy;
- templated source URLs;
- templated namespaces;

should receive the same scrutiny as infrastructure code.

## Pull-request generator security

PR-based generation introduces a trust boundary between untrusted contribution content and deployment automation.

Do not assume that because a source is a pull request it is safe to interpolate into privileged fields. Project templating, repository credentials, destination scope, and generated application permissions need explicit constraints.

---

# Multi-cluster delivery

Argo CD can manage Applications across multiple Kubernetes clusters.

A useful architecture model is:

```text
             Argo CD control plane
                 /    |    \
                /     |     \
               v      v      v
         cluster A cluster B cluster C
```

This centralizes visibility and policy, but also centralizes failure impact.

Questions to decide deliberately:

- Which clusters may a given Argo CD instance control?
- Are production and non-production in the same failure domain?
- Which project can target which cluster/namespace?
- What credentials are stored and with what privilege?
- How are cluster credentials rotated?
- What happens if the Argo CD control plane is unavailable?
- Can workloads continue running independently? Usually yes, because Kubernetes keeps running already-applied workloads, but desired-state reconciliation pauses.
- How is the control plane restored after loss?

A highly available Argo CD control plane improves delivery availability, but it should not be mistaken for application-runtime availability. Existing workloads are executed by Kubernetes, not by the Argo CD server process.

---

# Projects, tenancy, and authorization

## AppProjects are policy objects

A project can constrain:

```text
source repositories
        +
destination clusters/namespaces
        +
allowed/denied resource kinds
        +
project roles
```

This makes the project the natural unit for team isolation.

## Default project caution

A permissive default project is convenient during evaluation but can undermine intended tenancy if production Applications remain there indefinitely.

For multi-team installations, create explicit projects with narrowly scoped sources and destinations.

## RBAC

Argo CD authorization is policy driven. Permissions can cover resources such as:

- applications;
- applicationsets;
- repositories;
- clusters;
- logs;
- exec;
- projects and related actions.

Treat `exec` and sync permissions as operationally sensitive. A user who can alter an Application's source or destination may gain much more power than a dashboard-only viewer.

## Kubernetes RBAC still matters

Argo CD RBAC controls what a user may ask Argo CD to do.

Kubernetes RBAC controls what Argo CD's identities can actually do to target clusters.

Both layers matter.

```text
user -> Argo CD RBAC -> Argo CD service identity -> Kubernetes RBAC -> resource mutation
```

A secure design does not rely on only one of these layers.

---

# Security model and trust boundaries

## 1. Source repository trust

A repository allowed by a project can influence generated Kubernetes resources.

Review who can write to that repository and what branch protection/review rules exist.

## 2. Repository credentials

Repository credentials are high-value secrets. Scope them narrowly and avoid sharing broader credentials than a source actually needs.

## 3. Cluster credentials

Target-cluster credentials define the blast radius of a compromised Argo CD control plane.

Least privilege at the Kubernetes layer remains important even when AppProjects are configured correctly.

## 4. Repository server

The repository server processes potentially untrusted source input and runs rendering tooling.

Custom configuration-management plugins can execute additional code. Treat plugin installation and images as part of the supply chain.

## 5. API server and identity provider

Protect the Argo CD API endpoint, configure TLS appropriately, and use explicit identity-provider audience and token rules.

Authentication proves identity; authorization still requires narrow RBAC.

## 6. Application and ApplicationSet creation

Creating or modifying Applications is often equivalent to granting controlled deployment authority.

Be especially cautious when users can template:

- project;
- destination;
- source repository;
- namespace;
- cluster;
- plugin inputs.

## 7. Secrets in Git

Argo CD does not make plaintext secrets safe merely because they are declarative.

Use an explicit secret-delivery design such as:

- external secret stores with Kubernetes operators;
- encrypted-in-Git workflows with controlled decryption;
- platform-specific secret injection.

The key requirement is that reviewers understand where secret material exists and where decryption authority lives.

---

# Resource deletion and finalizers

Deletion semantics are one of the highest-risk areas in GitOps.

Removing a manifest, deleting an Application, changing an ApplicationSet generator, or enabling pruning can all affect resource lifetime.

## Application finalizer

Applications may use Argo CD resource finalizers to cascade deletion to managed resources.

That means deleting the `Application` object itself can be materially different from simply stopping reconciliation.

Before deleting an Application, determine whether you intend to:

- delete the application definition only;
- orphan currently running resources;
- cascade-delete managed resources.

## Prune confirmation

For sensitive resources, use confirmation-oriented deletion controls where appropriate rather than assuming every desired-state removal should immediately become a destructive cluster action.

---

# Reliability and disaster recovery

## What must survive

Argo CD configuration and state are largely represented through Kubernetes resources such as:

- Applications;
- ApplicationSets;
- AppProjects;
- Secrets;
- ConfigMaps;
- cluster/repository configuration;
- relevant controller state and credentials.

The upstream CLI provides administrative export/import workflows for backup and recovery.

A backup is useful only if restore is tested.

## Control-plane outage

If Argo CD is unavailable:

- existing Kubernetes workloads generally continue running;
- new desired-state changes do not reconcile normally;
- drift detection pauses;
- auto-sync pauses;
- UI/API visibility is reduced;
- hooks and delivery operations may stop.

This makes Argo CD availability important for **delivery continuity**, but not normally a runtime dependency for already-running application Pods.

## Git outage

If a source cannot be fetched, Argo CD cannot reliably generate a fresh desired state for that source.

Cached data may help operationally, but design recovery assuming the authoritative source may be temporarily unavailable.

## Kubernetes API outage

If the target cluster API is unreachable, Argo CD cannot compare or reconcile current live state. Treat resulting status as incomplete rather than assuming the workload is healthy or unhealthy.

---

# Scaling and performance

At small scale, nearly any reasonable Argo CD topology works. At larger scale, the cost model becomes important.

Main work sources include:

- fetching repositories;
- rendering manifests;
- watching Kubernetes resources;
- diffing large object sets;
- refreshing many Applications;
- evaluating health;
- ApplicationSet generation;
- UI/API queries;
- synchronization operations.

## Monorepositories

A monorepo can cause unrelated commits to trigger refresh work for many Applications unless repository structure and refresh controls are designed carefully.

Keep application paths and generation dependencies understandable.

## Large applications

Applications containing thousands of objects increase:

- comparison cost;
- status payload size;
- sync time;
- Kubernetes API pressure;
- blast radius of a single operation.

Selective apply options may help in specific cases, but very large ownership units should also trigger an architecture review: perhaps the Application boundary itself is too broad.

## Cache behavior

Redis and internal caches reduce repetitive work. Cache problems can manifest as performance degradation or stale-looking operational behavior, so diagnose cache health separately from source correctness.

## Webhooks and reconciliation intervals

Webhooks reduce latency between source change and refresh, while periodic reconciliation provides resilience against missed events.

Do not disable periodic correctness mechanisms solely to optimize API traffic unless the operational consequences are understood.

---

# Observability

Operate Argo CD as a production control plane, not just a dashboard.

Monitor signals around:

- controller reconciliation latency;
- application sync and health counts;
- manifest-generation errors;
- repository connectivity;
- cluster connectivity;
- failed sync operations;
- queue/backlog behavior;
- API-server errors and latency;
- Redis/cache health;
- resource consumption;
- repeated OutOfSync applications;
- authentication/authorization failures.

A permanently OutOfSync application is operational debt even if nobody is paged for it. It trains operators to ignore the signal.

---

# Common failure modes

## `ComparisonError`

Likely areas:

- repository access;
- revision resolution;
- manifest generation;
- invalid renderer configuration;
- cluster discovery or API problems.

Start before the sync phase. If comparison cannot complete, there may be nothing valid to synchronize.

## Application stays OutOfSync after successful sync

Investigate:

- mutating webhooks;
- controller-owned fields;
- generated random values;
- invalid fields dropped by Kubernetes;
- disabled pruning;
- ownership conflicts;
- server-side apply field managers;
- normalization differences.

Do not immediately add an ignore rule.

## Application is Synced but Degraded

The desired configuration is present, but the workload is not healthy.

Inspect the Kubernetes workload chain:

```text
Application
  -> Deployment/StatefulSet/CR
     -> ReplicaSet/operator state
        -> Pod / volume / network / external dependency
```

## Sync operation hangs

Inspect:

- hooks;
- first unhealthy sync wave;
- Jobs that never complete;
- CRDs whose controllers are not ready;
- readiness/health customizations;
- resources waiting on external infrastructure.

## Prune deletes too much

Possible causes:

- incorrect Application ownership boundary;
- path move/rename;
- generator shrink;
- source selection mistake;
- ApplicationSet template change;
- resource tracking collision;
- destructive sync policy enabled too broadly.

Recovery starts with understanding the source change that altered the desired resource set.

## Manual cluster edit keeps disappearing

Likely self-heal or a later reconciliation is restoring source state.

Use a documented break-glass workflow rather than fighting the controller repeatedly.

## ApplicationSet unexpectedly removes Applications

Check:

- generator inventory;
- selector changes;
- SCM credentials/access errors;
- generator policy;
- deletion behavior;
- template expansion.

A generator becoming empty can be operationally significant.

## Helm app differs from `helm list`

Remember that Argo CD uses Helm as a renderer and manages application lifecycle itself. Do not assume the same release-state semantics as a direct Helm-managed installation.

---

# Debugging workflow

A disciplined sequence is faster than clicking randomly through the UI.

## 1. Inspect application summary

```bash
argocd app get <app>
```

Check:

- source/revision;
- destination;
- sync status;
- health status;
- conditions;
- resource tree;
- latest operation.

## 2. Inspect the diff

```bash
argocd app diff <app>
```

Ask which system owns each differing field.

## 3. Inspect rendered manifests

Verify what Argo CD actually generated, not what you assume the repository contains.

For Helm-based sources, reproduce the effective values and rendering logic where possible.

## 4. Inspect live Kubernetes objects

```bash
kubectl get <kind> <name> -n <namespace> -o yaml
kubectl describe <kind> <name> -n <namespace>
kubectl get events -n <namespace> --sort-by=.lastTimestamp
```

Check:

- conditions;
- events;
- field managers;
- admission mutations;
- owner references;
- finalizers;
- controller status.

## 5. Inspect controller logs

Separate logs by component:

- application controller;
- repo server;
- API server;
- ApplicationSet controller.

The failing component usually points to the failing stage.

## 6. Reproduce manifest generation

When generation fails or appears nondeterministic, reproduce the renderer outside Argo CD using the same revision and inputs.

## 7. Inspect policy only after correctness

If generation and Kubernetes behavior are correct, then inspect:

- AppProject constraints;
- Argo CD RBAC;
- Kubernetes RBAC;
- sync options;
- ignore rules;
- destination permissions.

---

# Practical CLI workflow

The exact flags should be checked against the installed release, but the stable workflow shape is:

```bash
# inspect
argocd app get my-app
argocd app diff my-app

# synchronize
argocd app sync my-app
argocd app wait my-app

# history
argocd app history my-app

# projects
argocd proj list
argocd proj get my-project

# repositories
argocd repo list

# clusters
argocd cluster list
```

For production automation, prefer declarative Application/AppProject/ApplicationSet definitions over accumulating hidden imperative configuration.

---

# Promotion models

## Branch-per-environment

```text
main/dev -> staging -> production branches
```

Advantages:

- familiar Git workflow;
- explicit environment branches.

Trade-offs:

- merges can drift;
- environment differences can become difficult to audit;
- branch state is mutable.

## Directory-per-environment

```text
environments/dev
environments/staging
environments/prod
```

Advantages:

- one repository can show promotion changes directly;
- overlays can be reviewed together.

Trade-offs:

- monorepo refresh scope and ownership need discipline.

## Immutable revision promotion

Promote an explicit image digest, chart version, commit, or generated configuration revision through environments.

Advantages:

- high reproducibility;
- easier forensic mapping.

Trade-offs:

- promotion automation must update references intentionally.

There is no universally correct topology. Choose the model that makes the intended production state easiest to explain from versioned evidence.

---

# GitOps design principles that matter in practice

## Determinism

The same revision and declared parameters should produce the same desired manifests.

## Explicit ownership

Each resource should have a clear reconciler and source of intent.

## Reviewability

A reviewer should be able to understand the effect of a source change before synchronization.

## Recoverability

Rollback and restore should be executable procedures, not assumptions.

## Least privilege

Source writers, Argo CD users, repository credentials, and cluster credentials should each receive only the access their role requires.

## Bounded blast radius

Projects, Applications, ApplicationSets, and Argo CD instances should be scoped so one mistake does not automatically become an organization-wide incident.

---

# Argo CD versus adjacent approaches

## Argo CD versus direct CI deployment

Direct CI deployment:

```text
CI -> cluster mutation -> job exits
```

Argo CD:

```text
source -> persistent controller -> repeated comparison/reconciliation
```

Direct CI can be simpler for small systems. Argo CD provides persistent drift detection and a dedicated delivery control plane.

## Argo CD versus Helm alone

Helm is primarily a Kubernetes package and release-management tool.

Argo CD can render Helm charts but then applies its own reconciliation model around the generated resources.

Use direct Helm when Helm release semantics are the desired primary abstraction. Use Argo CD when continuous declarative reconciliation and application-level drift visibility are primary requirements.

## Argo CD versus Flux

Both are Kubernetes GitOps reconciliation systems.

Typical evaluation dimensions include:

- API/object model;
- UI expectations;
- multi-tenancy model;
- source/artifact workflows;
- controller decomposition;
- Helm integration model;
- notification and automation patterns;
- fleet-management ergonomics;
- operational footprint.

Choose based on architecture and operating model, not popularity alone.

## Argo CD versus an operator

An operator usually reconciles a domain-specific custom resource into other resources or external systems.

Argo CD reconciles application desired state from versioned sources into Kubernetes.

The two often compose:

```text
Argo CD applies CustomResource
        |
        v
operator reconciles domain-specific children/external state
```

This creates nested ownership that must be reflected in health and diff expectations.

---

# Anti-patterns

## Treating the UI as the source of truth

The UI should expose and operate declarative state, not become the only place where important production configuration exists.

## One giant Application for everything

This increases sync time, status size, ownership ambiguity, and blast radius.

## One Argo CD instance with unrestricted cluster-admin everywhere

Convenient initially, dangerous at scale.

## Broad `ignoreDifferences`

This can hide real configuration drift.

## Auto-prune before ownership is understood

Pruning should be enabled after resource boundaries and deletion semantics are understood.

## Nondeterministic rendering

Random template output defeats stable desired-state comparison.

## ApplicationSets without deletion review

Fleet generators should be treated as infrastructure code with multiplication effects.

## Manual hotfixes with self-heal enabled and no break-glass process

The controller will do exactly what it was configured to do: restore desired state.

## Storing plaintext secrets because the repository is private

Repository privacy is not equivalent to a secret-management model.

---

# Operational checklist

Before production adoption, verify:

- repositories are explicitly trusted;
- source revisions and promotion strategy are documented;
- rendering is deterministic;
- AppProjects restrict destinations and sources;
- Argo CD RBAC is least privilege;
- Kubernetes service-account permissions are least privilege;
- repository and cluster credentials have rotation procedures;
- TLS and OIDC configuration are reviewed;
- custom plugins are treated as executable supply-chain components;
- secret delivery is designed separately;
- pruning policy is deliberate;
- self-heal behavior is understood by incident responders;
- break-glass procedures exist;
- ApplicationSet deletion behavior is tested;
- backups are created and restore is rehearsed;
- controller/repo-server/API/Redis health is monitored;
- persistent OutOfSync states are investigated rather than normalized;
- upgrades are tested against custom health rules, plugins, CRDs, and sync options.

---

# Learning path

## Beginner

Learn:

1. Kubernetes object reconciliation.
2. Git commits, branches, tags, and revert workflows.
3. `Application` source and destination fields.
4. Sync status versus health.
5. Manual sync and diff inspection.

Practice:

- create one Application;
- introduce a harmless drift change;
- inspect `OutOfSync`;
- sync it back;
- break a container image reference and observe `Synced` versus health behavior.

## Intermediate

Learn:

1. automated sync;
2. pruning and self-heal;
3. AppProjects;
4. RBAC;
5. Helm/Kustomize rendering;
6. hooks and waves;
7. diff customization;
8. resource tracking.

Practice:

- create separate dev/prod projects;
- restrict destinations;
- deploy a Helm chart through Argo CD;
- add a PreSync migration Job;
- reproduce one intentional diff customization.

## Advanced

Learn:

1. ApplicationSet fleet generation;
2. multi-cluster credentials and isolation;
3. HA and scaling;
4. repo-server/plugin security;
5. disaster recovery;
6. performance tuning;
7. nested controller ownership;
8. supply-chain and secret-delivery integration.

Practice:

- generate Applications across several clusters;
- simulate a generator inventory mistake safely;
- restore Argo CD configuration from backup;
- investigate a mutating-webhook drift case;
- measure reconciliation behavior for a large monorepo.

---

# Source discipline

Argo CD changes quickly enough that version-sensitive behavior should be checked against the documentation for the installed release.

Prefer, in order:

1. upstream Argo CD stable documentation;
2. upstream source repository and release notes;
3. Kubernetes documentation for underlying API semantics;
4. Helm documentation when investigating chart-rendering behavior;
5. Git documentation for source/revision behavior.

Do not treat an old blog post or copied command snippet as authoritative when it conflicts with current upstream documentation.

---

# Relationships in OpenDevIndex

- `cloud/kubernetes` — Argo CD operates by reconciling Kubernetes API resources.
- `tool/git` — Git is a primary versioned desired-state source and review/history mechanism.
- `cloud/helm` — Helm charts can be rendered as an Argo CD source while Argo CD owns application reconciliation.
- `platform/flux` — another major Kubernetes GitOps reconciliation platform and a meaningful architectural alternative.

---

# Verification

This deep-dive was reviewed against current upstream Argo CD architecture, Application, sync, project, RBAC, ApplicationSet, security, Helm integration, health, diffing, and disaster-recovery documentation on **2026-09-06**.

The module deliberately avoids hard-coding release-specific defaults where those values may change. Operational flags, supported Kubernetes versions, component defaults, and alpha/beta features should be checked against the documentation for the exact Argo CD release in use.

---

# Maintenance

Update this module when any of the following materially changes:

- Application or ApplicationSet APIs;
- sync semantics;
- default resource-tracking behavior;
- Helm/rendering integration;
- project or RBAC security model;
- repository-server/plugin trust boundaries;
- supported deployment topology;
- disaster-recovery workflow;
- current security guidance;
- major control-plane architecture.

Preserve the stable OpenDevIndex address `platform/argocd`. Deep-dive content should remain hand-curated and source-backed rather than being replaced by a generic catalog renderer.
