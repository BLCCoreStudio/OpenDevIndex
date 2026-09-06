# Helm

> Kubernetes package manager and release-management tool that renders versioned charts into Kubernetes resources, applies them through the API, and records release history for upgrades and rollbacks.

Helm is easiest to understand as a **client-side packaging, rendering, and release-management layer on top of the Kubernetes API**. It does not replace Kubernetes controllers, the scheduler, the container runtime, or a GitOps reconciler. A chart describes a reusable Kubernetes application package; values configure an instance of that package; Helm renders templates into Kubernetes manifests; and a release records one installed instance and its revision history.

That distinction—**chart versus values versus rendered manifest versus release versus live Kubernetes objects**—is the core mental model for the entire tool.

---

## 1. What Helm is

Helm packages Kubernetes application definitions into **charts** and manages installed chart instances as **releases**.

A typical Helm workflow can:

- create a chart;
- resolve chart dependencies;
- merge default and user-supplied values;
- render Go templates into Kubernetes manifests;
- install those resources through the Kubernetes API;
- record release metadata and revision history;
- upgrade a release with new chart content or values;
- roll back to an earlier revision;
- uninstall release-managed resources;
- distribute charts through traditional chart repositories or OCI registries.

The stable OpenDevIndex address for this module is `cloud/helm`.

Helm is a **tool**, not an in-cluster application platform. Modern Helm does not require the historical Tiller server used by Helm 2. The Helm client and reusable Go library interact directly with the Kubernetes API using the caller's Kubernetes credentials.

---

## 2. Why Helm exists

Raw Kubernetes YAML is explicit, but application deployments quickly become repetitive.

A non-trivial application may need:

- Deployments or StatefulSets;
- Services;
- ServiceAccounts and RBAC;
- ConfigMaps and Secrets;
- PersistentVolumeClaims;
- Ingress or Gateway resources;
- Jobs for migrations;
- monitoring resources;
- PodDisruptionBudgets;
- autoscaling policy;
- environment-specific names, images, replicas, hosts, resources, and feature switches.

Copying those manifests for every environment creates drift and makes versioned reuse difficult.

Helm addresses that problem by giving Kubernetes resources a package boundary:

```text
chart
  + default values
  + templates
  + dependencies
  + metadata
        |
        v
user-supplied values
        |
        v
Helm rendering
        |
        v
Kubernetes manifests
        |
        v
Kubernetes API
        |
        v
release record + live resources
```

The package abstraction is useful when an application has a repeatable Kubernetes shape but needs controlled variation between installations.

---

## 3. The four objects to keep separate

Many Helm mistakes come from treating several different things as if they were the same object.

### Chart

A **chart** is the reusable package definition.

It contains metadata, default values, templates, optional dependencies, documentation, CRDs, tests, and other package files.

### Values

**Values** are configuration inputs used while rendering the chart.

They may come from the chart's `values.yaml`, parent charts, user-supplied files, or command-line overrides.

### Rendered manifests

The **rendered manifests** are concrete Kubernetes API objects produced after template evaluation.

Kubernetes never executes a Helm template. Helm resolves the template before sending resources to the API server.

### Release

A **release** is one installed instance of a chart plus its configuration and revision history.

The same chart can be installed multiple times under different release names, namespaces, and values.

A release is not identical to one Kubernetes Deployment. A single release may own many Kubernetes resources.

---

## 4. Architecture

Modern Helm has two main software layers:

```text
Helm CLI / another Go client
          |
          v
      Helm library
          |
     render + release logic
          |
          v
 Kubernetes client library
          |
          v
 Kubernetes API server
          |
          +-------------------+
          |                   |
          v                   v
   workload resources    release records
                         (normally Secrets)
```

### Helm client

The CLI provides commands such as:

- `helm install`;
- `helm upgrade`;
- `helm rollback`;
- `helm uninstall`;
- `helm template`;
- `helm lint`;
- `helm package`;
- `helm pull`;
- `helm push`;
- `helm dependency`;
- `helm history`;
- `helm get`;
- `helm test`.

It also manages local configuration, repository information, registry credentials, plugins, and chart-development workflows.

### Helm library

Helm's Go library implements rendering and release actions and can be embedded by other software rather than invoked only through the command-line binary.

### Kubernetes API

Helm ultimately manages Kubernetes API objects. Kubernetes authentication, authorization, admission, API compatibility, and controller behavior still apply.

Helm cannot bypass Kubernetes RBAC simply because the manifests came from a chart.

### Release storage

Helm records release information so it can inspect history, calculate upgrades, and roll back revisions.

The normal cluster-backed storage driver uses Kubernetes Secrets. Helm also exposes other storage drivers. Because release records can contain rendered configuration and chart data, access to release storage is a security concern rather than harmless bookkeeping.

---

## 5. Chart anatomy

A simplified chart can look like:

```text
mychart/
├── Chart.yaml
├── values.yaml
├── values.schema.json
├── charts/
├── crds/
├── templates/
│   ├── _helpers.tpl
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── NOTES.txt
│   └── tests/
└── README.md
```

Not every chart uses every file.

### `Chart.yaml`

Contains package metadata such as chart name, chart version, description, dependencies, and other chart fields.

### `values.yaml`

Defines default configuration exposed to chart consumers.

Good defaults should make common installation paths understandable without hiding dangerous production assumptions.

### `values.schema.json`

Can validate the shape and types of values before rendering/install operations.

Schema validation is especially useful for large public charts because a misspelled or wrongly typed value can otherwise be silently ignored or produce a surprising manifest.

### `templates/`

Contains files evaluated through Helm's template engine.

### `charts/`

Contains packaged dependencies when they are materialized locally.

### `crds/`

Contains CustomResourceDefinition resources that need special lifecycle handling.

CRDs should not be treated as ordinary namespaced application objects because changing or deleting an API definition can affect data and controllers outside one release's local lifecycle.

---

## 6. Chart versions versus application versions

Helm distinguishes package versioning from application versioning.

### Chart version

The chart version represents the version of the Helm package itself.

Change it when the chart package changes in a way that should produce a new package artifact.

### Application version

A chart can also advertise an application version.

The application version is informational metadata; it does not replace the chart version and should not be assumed to control image resolution automatically.

A chart can change without the underlying application version changing, and an application can change while a chart author decides how that maps to package releases.

---

## 7. Template engine

Helm templates use Go templates plus Helm/Sprig functions and Helm-specific built-in objects.

A small example:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "myapp.fullname" . }}
spec:
  replicas: {{ .Values.replicaCount }}
  template:
    spec:
      containers:
        - name: app
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
```

The template is not a Kubernetes object until it is rendered.

### Important built-in objects

Common objects include:

- `.Values` — merged user/chart configuration;
- `.Chart` — chart metadata;
- `.Release` — release name, namespace, revision, install/upgrade state;
- `.Capabilities` — information about Kubernetes capabilities available to the renderer;
- `.Files` — non-template files packaged in the chart;
- `.Template` — information about the current template.

### Pipelines and functions

Helm templates support pipelines and helper functions for quoting, defaults, string manipulation, YAML generation, indentation, lookup, and other rendering tasks.

A template should remain readable. A chart that embeds a small programming language in every YAML file is technically flexible but operationally difficult to review.

---

## 8. Values precedence

Values may come from several layers.

The practical rule is that **more specific user input overrides less specific defaults**.

A common precedence chain is:

```text
chart values.yaml
      |
      v
parent/subchart configuration
      |
      v
user values files (-f / --values)
      |
      v
command-line overrides (--set and related flags)
```

When several user files or override arguments are supplied, later/more specific input can replace earlier values according to Helm's merge behavior.

### Why precedence matters

A rendered value can be different from what you see in the chart's default `values.yaml` because another layer changed it.

When debugging configuration, inspect the release's effective values rather than assuming defaults are active:

```bash
helm get values <release>
helm get values <release> --all
```

### Prefer structured values files for durable configuration

`--set` is convenient for a small override, but large production configurations are easier to review and version when represented in explicit values files or generated through a controlled pipeline.

---

## 9. Designing values well

Values are an API exposed by the chart author.

A good values interface should be:

- predictable;
- documented;
- schema-validated where practical;
- stable enough for automation;
- explicit about security-sensitive defaults;
- organized around user intent rather than internal template implementation details.

### Avoid leaking every implementation detail

Exposing hundreds of low-level toggles can make a chart theoretically configurable but impossible to reason about.

### Avoid magic coupling

If two values must always be changed together, encode or document that relationship clearly.

### Prefer clear types

Boolean, integer, string, list, and map confusion is a recurring source of rendering errors. JSON Schema can catch many mistakes before the API server sees the generated object.

---

## 10. Named templates and helper functions

Reusable snippets are normally defined in helper templates such as `_helpers.tpl`.

They are commonly used for:

- names;
- labels;
- selectors;
- image references;
- annotations;
- service-account naming;
- repeated metadata.

Named templates reduce copy/paste but can also hide important behavior if overused.

A useful rule is to abstract repetition without making a Kubernetes reviewer chase ten helper calls to understand one manifest.

---

## 11. Subcharts and dependencies

Charts can depend on other charts.

Dependencies are declared in chart metadata and resolved into a dependency graph.

Typical commands include:

```bash
helm dependency update ./mychart
helm dependency build ./mychart
helm dependency list ./mychart
```

### Lock dependency versions

A reproducible release process should avoid accidentally resolving an unexpected dependency version at deployment time.

Use explicit version constraints deliberately and keep dependency lock artifacts under review where the workflow expects deterministic builds.

### Parent and child values

Parent charts can supply configuration to subcharts, but subchart value scope has rules. Global values can deliberately expose configuration across chart boundaries.

Deep dependency trees can create configuration surfaces that are difficult to audit. Prefer composition that remains understandable.

---

## 12. Library charts

A library chart packages reusable template primitives rather than directly installable application resources.

This can standardize common labels, containers, probes, security contexts, or object fragments across a chart ecosystem.

Library charts are useful when multiple charts intentionally share conventions, but they create another dependency and versioning boundary. Treat them like reusable software libraries, not invisible copy/paste replacement.

---

## 13. Rendering versus applying

Helm has two conceptually separate stages:

```text
chart + values
      |
      v
   render
      |
      v
Kubernetes YAML
      |
      v
    apply
      |
      v
live API objects
```

### Render locally

```bash
helm template my-release ./mychart -f values-prod.yaml
```

This is extremely useful because it separates template correctness from cluster-side behavior.

### Lint

```bash
helm lint ./mychart
```

Linting catches chart-level issues but does not prove that the rendered resources are valid for every target cluster or that the application works.

### Dry-run behavior

Dry-run modes can help inspect generated resources and API interactions, but they should not be treated as a substitute for staging validation.

Admission policies, runtime controllers, storage provisioners, webhooks, and external systems may behave differently once resources are actually created.

---

## 14. Install lifecycle

A simplified install path is:

```text
helm install
    |
    v
load chart + dependencies
    |
    v
merge values
    |
    v
validate values/templates
    |
    v
render manifests
    |
    v
run applicable pre-install hooks
    |
    v
submit resources to Kubernetes
    |
    v
optionally wait for readiness
    |
    v
run applicable post-install hooks
    |
    v
record release revision
```

The exact mechanics depend on Helm version, flags, resource kinds, hooks, and cluster behavior.

A successful API submission does not automatically mean the application is healthy. Kubernetes controllers can accept a Deployment while its Pods later fail image pulls or readiness checks.

---

## 15. Releases and revisions

Every installed release has a name and revision history.

Useful commands:

```bash
helm list
helm status <release>
helm history <release>
helm get all <release>
helm get manifest <release>
helm get values <release>
```

### Revision

An install starts a release history. Upgrades and rollbacks create new revisions.

This matters because rollback is a **new release action based on previous release information**, not a magical rewind of every external side effect in the system.

---

## 16. Upgrade model

A normal upgrade combines a chart version and configuration to produce a new desired manifest set for the release.

```bash
helm upgrade myapp ./chart -f values-prod.yaml
```

Common concerns include:

- removed Kubernetes APIs;
- immutable fields;
- changed selectors;
- CRD schema changes;
- stateful storage migrations;
- hooks;
- value-key renames;
- manual changes to live objects;
- image compatibility;
- application database migrations.

### `--install`

A common deployment pattern is:

```bash
helm upgrade --install myapp ./chart -f values-prod.yaml
```

This makes the command install when the release does not yet exist and upgrade when it does.

Convenient idempotent-looking CLI behavior does not make all underlying application migrations idempotent. Database and external-system changes still need their own safety design.

---

## 17. Rollback model

A rollback selects a previous release revision and creates a new revision based on that state.

```bash
helm history myapp
helm rollback myapp 3
```

### Rollback is not time travel

Helm cannot automatically undo every side effect produced since revision 3.

Examples that may need separate recovery logic:

- schema migrations;
- object-store writes;
- external DNS changes;
- cloud resources created by operators;
- irreversible data conversion;
- CRD schema evolution;
- Jobs whose effects already completed.

Design applications so package rollback and data rollback are not falsely treated as the same operation.

---

## 18. Uninstall model

`helm uninstall` removes resources considered part of the release according to Helm's lifecycle and policies.

Some resources may intentionally survive, and some external effects are not represented as Helm-managed Kubernetes objects.

Before automating destructive uninstall in production, understand:

- persistent volume reclaim behavior;
- resource retention annotations/policies;
- CRDs;
- operator-created child resources;
- hook-created resources;
- cloud resources created indirectly;
- application data ownership.

---

## 19. Hooks

Hooks let chart authors run resources at specific points in the release lifecycle.

Examples include:

- `pre-install`;
- `post-install`;
- `pre-upgrade`;
- `post-upgrade`;
- `pre-rollback`;
- `post-rollback`;
- `pre-delete`;
- `post-delete`;
- `test`.

Hooks are Kubernetes resources marked with Helm annotations.

### Common uses

- database migration Jobs;
- pre-upgrade backups;
- smoke tests;
- cleanup steps;
- initialization tasks.

### Hooks are a sharp tool

A hook can make a release depend on procedural ordering that is not obvious from the normal Kubernetes object graph.

A failed migration hook can block a release. A hook that is not safely repeatable can make retries dangerous. A hook that creates persistent side effects may not be undone by rollback.

Use hooks when lifecycle ordering is genuinely required, not as a substitute for a well-designed controller or application startup model.

---

## 20. Hook ordering and cleanup

Hook resources can have weights and deletion policies that influence ordering and lifecycle.

When debugging hook behavior, inspect:

```bash
helm get hooks <release>
kubectl get jobs,pods
kubectl describe job <hook-job>
```

Do not immediately delete a failed hook Job before collecting logs and exit status; it often contains the strongest evidence of the real deployment failure.

---

## 21. CRDs

CustomResourceDefinitions are a special package-lifecycle concern.

Helm supports a chart `crds/` directory for CRDs that must exist before templates using those custom resources are created.

### Why CRDs are special

A CRD defines an API that may be shared by:

- multiple releases;
- multiple namespaces;
- operators;
- existing custom resources containing durable state.

Deleting a CRD can delete or orphan data depending on the environment and lifecycle.

Therefore chart authors should treat CRD installation, upgrade, conversion, and removal as API migration work—not ordinary manifest churn.

---

## 22. Kubernetes ownership boundary

Helm manages resources through Kubernetes; Kubernetes controllers then manage their own child state.

Example:

```text
Helm release
    |
    v
Deployment
    |
    v
ReplicaSet
    |
    v
Pods
```

Helm normally manages the Deployment object, not every transient Pod directly.

If a Pod fails, the root cause may be:

- the chart rendered a bad Deployment;
- admission mutated/rejected it;
- the scheduler cannot place the Pod;
- kubelet/runtime cannot start it;
- storage or networking failed;
- application startup failed.

Do not blame "Helm" for every post-install workload failure without following the Kubernetes ownership chain.

Related OpenDevIndex module: `cloud/kubernetes`.

---

## 23. Resource ownership and conflicts

Helm tracks which Kubernetes resources belong to a release using metadata conventions and release state.

Conflicts arise when:

- two releases try to own the same resource;
- a resource already exists outside Helm;
- another controller rewrites fields;
- a GitOps reconciler manages the same object;
- an operator owns a child resource Helm also tries to manage.

Modern Helm provides explicit mechanisms for some ownership-adoption scenarios, but taking ownership should be a deliberate migration because future upgrade/uninstall operations can then affect that resource.

The safest model is usually **one clear declarative owner per field/resource boundary**.

---

## 24. Helm and GitOps

Helm and GitOps solve overlapping but different problems.

### Helm

Helm provides:

- package format;
- value merging;
- templating;
- dependency management;
- release actions;
- chart distribution.

### GitOps controller

A GitOps controller typically provides:

- continuous reconciliation from version control;
- drift correction;
- pull-based cluster synchronization;
- policy around promotion and environments.

A GitOps system can use Helm charts as an input format.

### Avoid dual ownership

If a human runs `helm upgrade` directly while a GitOps controller continuously enforces a different desired chart/version/values set, one system can undo the other.

Choose a clear operational owner for production reconciliation.

---

## 25. Drift

Kubernetes resources can change after Helm installs them:

- an operator mutates them;
- an admission webhook adds fields;
- an autoscaler changes replica count;
- a person uses `kubectl edit`;
- another deployment tool changes the same resource.

Helm upgrade behavior has evolved across major versions to reason about live state more accurately, and current Helm 4 introduces additional apply-strategy changes.

The stable principle is: **do not assume the stored release manifest is always identical to the live object**.

Before a risky upgrade, inspect both rendered intent and current live state.

---

## 26. Distribution: chart repositories

Traditional Helm repositories serve packaged charts and an index describing available versions.

Typical workflow:

```bash
helm repo add example https://charts.example.com
helm repo update
helm search repo example
helm pull example/mychart
```

A repository is a distribution mechanism. It does not by itself prove chart quality, security, provenance, or compatibility.

---

## 27. Distribution: OCI registries

Modern Helm can store and retrieve charts from OCI-compatible registries.

A typical reference looks like:

```text
oci://registry.example.com/charts/myapp
```

OCI distribution has useful operational properties:

- reuse of existing registry infrastructure;
- digest-addressable artifacts;
- familiar authentication models;
- integration with artifact promotion pipelines.

Current Helm 4 documentation includes additional OCI digest and supply-chain improvements. Exact commands and feature support should be checked against the installed Helm minor version.

---

## 28. Chart provenance and integrity

Helm supports provenance metadata and verification workflows for packaged charts.

Integrity verification helps answer:

- is this the chart artifact that was signed/published by the expected source?
- did the package change after signing?

It does **not** answer:

- is the chart free of malicious templates?
- are the container images safe?
- are the default RBAC permissions appropriate?
- is the application free of vulnerabilities?

Supply-chain security is layered.

A strong pipeline can combine:

- immutable chart versions or digests;
- provenance/signature verification;
- controlled registries;
- policy checks on rendered manifests;
- image signatures/provenance;
- vulnerability scanning;
- admission policy.

---

## 29. Security model

Helm's effective Kubernetes permissions are normally the permissions of the Kubernetes identity it uses.

That means a Helm command capable of rendering a ClusterRole is not automatically allowed to create that ClusterRole.

Kubernetes authentication, RBAC, and admission still decide what can be accepted.

### Least privilege

A deployment identity should have only the permissions required by the release workflow.

Using cluster-admin for every CI deployment makes chart development easy at the cost of a much larger blast radius.

### Review cluster-scoped resources

Pay special attention to:

- ClusterRoles;
- ClusterRoleBindings;
- CRDs;
- namespaces;
- admission webhooks;
- APIService resources;
- StorageClasses;
- cluster-wide networking policy/resources.

One chart release can otherwise affect workloads far beyond its namespace.

---

## 30. Secrets and release metadata

Values can contain secrets, and rendered manifests can contain secret material.

Helm release records may preserve chart and configuration information. Treat access to release storage as sensitive.

Avoid casually putting plaintext credentials into:

- checked-in values files;
- shell history through `--set`;
- CI command logs;
- rendered debug output;
- ticket attachments;
- release metadata when a safer external secret flow is available.

Kubernetes Secret resources are base64-encoded API objects, not an automatic end-to-end secret-management solution.

---

## 31. Template security

Helm templates are code-like transformation logic applied before API submission.

A malicious or poorly reviewed chart can render highly privileged Kubernetes resources.

Before installing an untrusted chart:

1. inspect chart metadata and source;
2. inspect default values;
3. render it locally;
4. search for privileged/host access and cluster-wide RBAC;
5. inspect hooks;
6. inspect CRDs;
7. inspect image registries and tags/digests;
8. run policy/security tooling against rendered manifests;
9. install first in an isolated test environment where practical.

`helm install` should not be treated like installing a harmless UI theme.

---

## 32. Common chart security risks

Look for:

- privileged containers;
- `hostNetwork`, `hostPID`, or `hostIPC`;
- broad `hostPath` mounts;
- wildcard ClusterRole permissions;
- automatic cluster-admin bindings;
- default ServiceAccounts with excessive privileges;
- mutable image tags;
- untrusted image registries;
- Secrets embedded directly in values;
- hooks that run privileged Jobs;
- admission webhooks installed cluster-wide;
- CRDs that expand the cluster API surface.

The chart is a package for infrastructure permissions as much as it is a package for application YAML.

---

## 33. Dependency and supply-chain risks

A parent chart can pull in subcharts that create resources not obvious from the top-level templates.

Before approving an update:

- review dependency version changes;
- verify lockfile changes;
- inspect transitive chart behavior;
- re-render with production values;
- compare manifests;
- verify image references introduced by dependencies.

A one-line dependency bump can produce a large operational delta.

---

## 34. Testing charts

Testing should happen at multiple layers.

### Syntax and chart validation

```bash
helm lint ./mychart
```

### Deterministic rendering

```bash
helm template test ./mychart -f values-test.yaml > rendered.yaml
```

Then validate the output with Kubernetes-aware schema or policy tools.

### Cluster-side installation

Use an ephemeral or staging cluster to test:

- admission behavior;
- CRDs;
- controller interactions;
- storage provisioning;
- networking;
- hooks;
- actual application readiness.

### Helm chart tests

Charts can define test resources that run through:

```bash
helm test <release>
```

Chart tests are useful for targeted post-install validation but do not replace broader integration and application testing.

---

## 35. CI/CD workflow

A disciplined chart pipeline might look like:

```text
source change
   |
   v
helm lint
   |
   v
render representative values
   |
   v
schema / policy / security validation
   |
   v
unit / template tests
   |
   v
ephemeral cluster integration test
   |
   v
package chart
   |
   v
sign / publish immutable artifact
   |
   v
promote exact artifact to environments
```

The important property is artifact identity: production should deploy the same reviewed chart package/digest that passed validation, not rebuild a semantically different package at the last step.

---

## 36. Debugging rendering failures

If Helm fails before reaching Kubernetes, isolate the rendering layer.

Useful commands:

```bash
helm lint ./chart
helm template debug ./chart -f values.yaml --debug
helm show values <chart>
```

Common causes:

- missing required values;
- wrong value type;
- nil map access;
- invalid template syntax;
- bad indentation;
- helper-template naming mistakes;
- dependency not downloaded;
- incompatible chart API/version assumptions.

Do not troubleshoot kubelet or CNI when Helm never produced valid manifests.

---

## 37. Debugging API/admission failures

If rendering succeeds but installation fails during API submission, inspect:

- Kubernetes API error text;
- RBAC;
- admission policy;
- deprecated/removed APIs;
- immutable-field changes;
- resource ownership conflicts;
- CRD availability;
- namespace existence;
- quota/limit policy.

Useful approach:

```bash
helm template debug ./chart -f values.yaml > rendered.yaml
kubectl apply --dry-run=server -f rendered.yaml
```

Server-side dry-run can expose many API and admission errors without creating resources, subject to the behavior of installed admission components.

---

## 38. Debugging a failed release

Start with release state:

```bash
helm status <release>
helm history <release>
helm get all <release>
```

Then move to Kubernetes ownership:

```bash
kubectl get events --sort-by=.lastTimestamp
kubectl get pods -o wide
kubectl describe pod <pod>
kubectl logs <pod>
```

If hooks are involved:

```bash
helm get hooks <release>
kubectl get jobs
```

The goal is to determine which boundary failed:

```text
chart parsing?
values merge?
template rendering?
API/RBAC/admission?
Kubernetes controller?
scheduler?
node/runtime/storage/network?
application itself?
```

---

## 39. Failure mode: upgrade timeout

An upgrade can time out while Kubernetes continues reconciling resources.

Possible causes include:

- Pods never become Ready;
- a Job/hook does not finish;
- PVC provisioning stalls;
- image pull fails;
- scheduling is impossible;
- an admission/controller dependency is slow;
- application probes are incorrect.

A timeout is a symptom. Check workload status and events rather than simply increasing the timeout indefinitely.

---

## 40. Failure mode: immutable field

Some Kubernetes fields cannot be changed in place.

A chart update can render a manifest that is individually valid YAML but impossible to apply to an existing object.

Typical remediation depends on the resource and data impact:

- create a new object;
- change naming/versioning strategy;
- explicitly recreate a replaceable resource;
- migrate state before replacement.

Never automate deletion of a stateful resource merely to make Helm green without understanding its persistence semantics.

---

## 41. Failure mode: removed Kubernetes API

A chart that rendered successfully against an older cluster may reference an API version removed by a newer Kubernetes release.

This is why cluster upgrades and chart maintenance are connected.

Before upgrading Kubernetes:

- inventory deployed chart versions;
- render/test them against the target API set;
- update charts using deprecated APIs;
- check CRDs and webhooks;
- verify Helm/Kubernetes version support policy.

---

## 42. Failure mode: values drift

A release may have accumulated overrides across several upgrades.

If operators do not understand which values are being reused, reset, or newly supplied, an upgrade can unexpectedly preserve or discard old configuration.

Before a critical change:

```bash
helm get values <release> --all
helm show values <new-chart>
```

Then explicitly construct the intended next configuration instead of relying on memory.

---

## 43. Failure mode: hook migration

Database migrations are a classic pre/post-upgrade hook use case and a classic rollback trap.

Questions to answer before release:

- Is the migration backward-compatible with the old application version?
- Is it idempotent if the Job retries?
- Can it resume after partial success?
- What happens if the app rollout fails after the migration succeeds?
- Is rollback safe?
- Is a backup actually restorable?

Helm can sequence the Job; it cannot design the data migration for you.

---

## 44. Failure mode: resource owned by another release

Helm may reject a resource that already has ownership metadata associated with another release or no compatible Helm ownership.

This is useful protection against accidental cross-release deletion.

Do not solve the error by blindly overwriting ownership annotations. First determine which deployment system should own the resource for its full future lifecycle.

---

## 45. Performance characteristics

Helm performance depends on more than template rendering speed.

### Chart rendering

Large template sets, complex functions, repeated lookups, and huge values structures add local CPU/memory cost.

### API operations

A release with hundreds or thousands of objects generates substantial Kubernetes API traffic during install and upgrade.

### Admission

Every submitted object may pass through validating/mutating admission, adding latency beyond Helm itself.

### Kubernetes reconciliation

Even after Helm has sent resources, real rollout time is dominated by scheduler, image pulls, storage, networking, probes, and application startup.

### Release metadata size

Very large rendered releases can strain the normal Kubernetes-backed storage limits. Helm exposes alternate storage strategies for special cases, but a giant release is also an architectural signal that package boundaries may deserve review.

---

## 46. Release granularity

A useful chart/release boundary should balance atomic change with blast radius.

### One giant release

Advantages:

- one command for a whole stack;
- shared values are easy to coordinate.

Costs:

- huge upgrade blast radius;
- slower rendering/apply;
- tangled ownership;
- rollback couples unrelated services;
- one failed hook can block everything.

### Many tiny releases

Advantages:

- independent lifecycle;
- smaller blast radius.

Costs:

- dependency coordination;
- more release metadata;
- cross-service version compatibility must be managed elsewhere.

The right boundary often follows independent application ownership and release cadence rather than repository folder structure.

---

## 47. Plugins

Helm can be extended with plugins.

Plugins can add commands or integrate external tooling. Current Helm 4 also introduces major changes to the plugin architecture, including a newer plugin model and optional WebAssembly-based execution paths.

Because plugins execute as tooling in the deployment environment, treat them as supply-chain dependencies:

- pin trusted sources/versions;
- inspect installation scripts or packages;
- limit credentials available to plugin processes;
- update deliberately;
- verify signatures where the plugin ecosystem supports it.

---

## 48. Go SDK

The Helm library can be embedded in Go applications.

This is useful for:

- platform tooling;
- custom deployment services;
- controllers that need chart rendering;
- testing and automation beyond shelling out to the CLI.

Embedding Helm also means the application inherits responsibility for:

- Kubernetes credentials;
- Helm storage configuration;
- version compatibility;
- error handling;
- release locking/concurrency semantics;
- upgrade testing.

Use the SDK when Helm behavior is genuinely part of application logic, not merely to avoid invoking a stable CLI in a simple pipeline.

---

## 49. Helm 2, Helm 3, and Helm 4 mental model

Historical differences matter because old tutorials remain common.

### Helm 2

Used an in-cluster server called **Tiller**. This changed the trust model and operational architecture substantially.

Helm 2 is obsolete and should not be used as the mental model for modern deployments.

### Helm 3

Removed Tiller and moved release operations to the client/library interacting directly with the Kubernetes API. Release data is normally stored in-cluster, with Secrets as the default Kubernetes-backed driver.

### Helm 4

Helm 4 is the current major generation at this review date. It preserves the basic modern client/library + Kubernetes API model while introducing breaking CLI/library changes and newer capabilities such as redesigned plugins, OCI improvements, status/apply changes, and additional value/chart features.

The exact Helm 4 behavior evolves by minor version. Read the current migration/changelog and version-support documents before upgrading a production automation stack from Helm 3.

---

## 50. Version skew with Kubernetes

Helm is compiled against Kubernetes client libraries, and the project publishes a support policy describing the Kubernetes versions each Helm line supports.

Do not assume that "Helm renders YAML" means every Helm version is forward-compatible with every Kubernetes cluster.

Compatibility concerns include:

- client API behavior;
- removed Kubernetes APIs;
- server-side apply behavior;
- discovery/capabilities;
- authentication plugins;
- CRD schemas;
- third-party plugins and SDK consumers.

Pin and test Helm as part of the cluster toolchain.

---

## 51. Chart compatibility across Helm major versions

Chart compatibility is not the same as CLI/plugin/SDK compatibility.

Helm 4 documentation explicitly maintains compatibility goals for existing charts while introducing new chart capabilities and architecture changes.

A chart that renders correctly under both versions does not prove that:

- automation flags are unchanged;
- plugin behavior is unchanged;
- SDK imports/APIs are unchanged;
- apply/update semantics are identical.

Test the whole release workflow when changing Helm major versions.

---

## 52. Helm versus Kustomize

Helm and Kustomize overlap in manifest customization but use different models.

### Helm

- package + template model;
- values API;
- chart dependencies;
- release history;
- install/upgrade/rollback lifecycle;
- package distribution.

### Kustomize

- transformation/overlay model over Kubernetes YAML;
- no Helm-style package release history by itself;
- tends to preserve more of the original resource structure rather than embed logic in Go templates.

Choose based on package/release needs and team workflow, not ideology. They can also be composed by higher-level delivery systems.

---

## 53. Helm versus raw manifests

Raw manifests are often sufficient when:

- the application is small;
- variation between environments is minimal;
- package reuse is not required;
- explicit YAML is more valuable than templating.

Helm becomes more useful when:

- many installations share a common package;
- configuration must be parameterized;
- dependencies need packaging;
- release revisions/rollback workflows are valuable;
- charts are distributed to other teams or users.

Do not introduce a templating language merely to avoid duplicating three obvious YAML fields.

---

## 54. Helm versus an Operator

Helm manages installation/release actions. An Operator/controller continuously reconciles domain-specific state.

Use Helm to install an Operator, but do not confuse the two control loops.

If a custom resource needs continuous lifecycle management—backups, failover, membership changes, version orchestration—a controller can be a better long-running owner than increasingly elaborate Helm hooks.

---

## 55. Helm versus a GitOps controller

Helm can be used imperatively from CI:

```text
CI -> helm upgrade -> Kubernetes API
```

A GitOps system typically keeps a persistent reconciliation loop:

```text
Git -> GitOps controller -> Kubernetes API
              ^
              |
          continuous
```

A GitOps controller may consume Helm charts but own release synchronization itself.

If Git is meant to be the source of truth, direct production Helm mutations outside that reconciler should be tightly controlled.

---

## 56. Common mistakes

### Treating Helm as a Kubernetes runtime

Helm renders and submits resources. Kubernetes controllers and node components execute them.

### Treating a chart as a container image

A chart can reference many container images and many Kubernetes objects. It is an orchestration package, not an executable image format.

### Using `--set` for large secret-heavy production configuration

This is difficult to review and can leak values through command history/logging.

### Making templates too clever

Complex nested conditionals and dynamic name generation can make security review harder than writing explicit resources.

### Hiding incompatible defaults

A chart should not silently create privileged or destructive production resources behind a seemingly harmless boolean.

### Assuming rollback reverses database changes

It usually cannot.

### Treating hooks as a general workflow engine

Hooks are lifecycle integration points, not a replacement for controllers or robust migration tooling.

### Installing CRDs casually

CRDs create cluster-wide APIs and often outlive one namespace or release.

### Letting two systems own the same resources

Direct Helm, GitOps, operators, and manual kubectl can fight over fields/resources.

### Updating chart dependencies without rendering the diff

A dependency bump can add privileged or cluster-scoped objects.

### Assuming lint means deployable

Lint cannot emulate every target cluster, admission controller, CSI/CNI implementation, or application runtime failure.

### Using mutable chart/image references in a promotion pipeline

Reproducibility requires immutable artifact identity.

---

## 57. Small example chart

`Chart.yaml`:

```yaml
apiVersion: v2
name: web
version: 0.1.0
appVersion: "1.4.2"
```

`values.yaml`:

```yaml
replicaCount: 2
image:
  repository: ghcr.io/example/web
  tag: "1.4.2"
service:
  port: 80
```

`templates/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Release.Name }}
  template:
    metadata:
      labels:
        app: {{ .Release.Name }}
    spec:
      containers:
        - name: web
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
```

Render it before installing:

```bash
helm lint ./web
helm template demo ./web
```

Install it:

```bash
helm install demo ./web
```

Upgrade values:

```bash
helm upgrade demo ./web --set replicaCount=3
```

Inspect history:

```bash
helm history demo
```

The educational point is not the syntax. It is the object transformation:

```text
chart + values
     -> rendered Deployment
     -> Kubernetes API object
     -> Kubernetes controllers create Pods
     -> Helm records release revision
```

---

## 58. Safer production upgrade checklist

Before a critical Helm upgrade:

1. identify the exact chart artifact/version/digest;
2. inspect release history and current values;
3. read chart release notes;
4. resolve and review dependency changes;
5. render with the intended production values;
6. compare the rendered resource diff;
7. inspect cluster-scoped resources, RBAC, hooks, and CRDs;
8. test against the target Kubernetes version;
9. verify image and chart provenance where required;
10. validate database migration/rollback semantics;
11. confirm backups for stateful changes;
12. deploy first to a representative non-production environment;
13. monitor Kubernetes rollout and application health;
14. keep a recovery plan that does not assume Helm rollback can reverse external state.

---

## 59. Learning path

### Stage 1: Kubernetes first

Understand:

- API objects;
- Deployments and StatefulSets;
- Services;
- ConfigMaps and Secrets;
- RBAC;
- CRDs;
- controller reconciliation.

OpenDevIndex next hop: `cloud/kubernetes`.

### Stage 2: basic Helm model

Learn:

- chart;
- values;
- template;
- release;
- revision.

### Stage 3: chart development

Learn:

- `Chart.yaml`;
- `values.yaml`;
- built-in objects;
- helper templates;
- values schema;
- dependencies;
- library charts.

### Stage 4: release operations

Learn:

- install;
- upgrade;
- rollback;
- uninstall;
- history;
- `helm get`;
- waiting/timeouts.

### Stage 5: lifecycle edges

Learn:

- hooks;
- CRDs;
- Jobs/migrations;
- ownership conflicts;
- storage drivers.

### Stage 6: supply chain

Learn:

- OCI registries;
- repositories;
- provenance;
- immutable digests;
- dependency pinning;
- image policy.

### Stage 7: platform integration

Learn:

- CI/CD;
- GitOps;
- policy validation;
- plugins;
- Go SDK;
- Helm/Kubernetes version skew.

---

## 60. Related OpenDevIndex modules

Machine-readable relationships are recorded in `entry.yaml`.

Current deliberate edge:

- `integrates-with -> cloud/kubernetes`

This is intentionally narrow. Helm's central architectural relationship is Kubernetes; additional graph edges should be added only when they explain a real package, deployment, or ownership boundary rather than generic ecosystem proximity.

---

## 61. Verification notes

This deep-dive was reviewed on **2026-09-05** against the current Helm documentation and canonical repository.

At the review date, Helm 4 is the current major generation. The following details are version-sensitive and should be rechecked before operational decisions:

- exact Helm 4 minor version and CLI flags;
- apply/update strategy;
- plugin runtime and compatibility;
- chart API-version support;
- Helm-to-Kubernetes version skew;
- OCI features;
- storage-driver behavior;
- SDK package/API compatibility;
- deprecated Kubernetes API handling;
- migration guidance from Helm 3.

The stable mental model should age more slowly:

- charts package Kubernetes resource templates;
- values configure a chart instance;
- Helm renders client-side before Kubernetes executes anything;
- releases record installed chart instances and revision history;
- Kubernetes RBAC/admission remain authoritative;
- rollback cannot automatically reverse arbitrary external side effects;
- hooks and CRDs require deliberate lifecycle design;
- distribution integrity is only one layer of supply-chain security.

---

## 62. Source map

Primary references are maintained in [`sources.md`](sources.md).

Key upstream references include:

- Helm documentation: https://helm.sh/docs/
- Introduction/architecture: https://helm.sh/docs/intro/introduction/
- Charts: https://helm.sh/docs/topics/charts/
- Template guide: https://helm.sh/docs/chart_template_guide/
- Hooks: https://helm.sh/docs/topics/charts_hooks/
- OCI registries: https://helm.sh/docs/topics/registries/
- Provenance: https://helm.sh/docs/topics/provenance/
- Plugins: https://helm.sh/docs/topics/plugins/
- Version support: https://helm.sh/docs/topics/version_skew/
- Helm 4 overview: https://helm.sh/docs/overview/

For a production upgrade or migration, prefer documentation corresponding to the exact Helm and Kubernetes versions in use rather than assuming the latest documentation describes an older automation stack exactly.
