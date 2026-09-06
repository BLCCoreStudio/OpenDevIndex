# Terraform

> Infrastructure-as-code tool that evaluates declarative configuration into a dependency graph, coordinates provider plugins, compares configuration with prior state and remote objects, and applies planned lifecycle changes across cloud, SaaS, and infrastructure APIs.

Terraform is most useful to understand as a **stateful reconciliation and change-planning engine**, not as a script runner. Configuration describes desired managed objects and relationships. Providers translate those objects into remote API operations. State records Terraform's bindings between configuration addresses and real objects. The plan phase computes proposed actions. Apply executes an approved plan while respecting dependency ordering.

This module focuses on that execution model, because most production Terraform problems are consequences of misunderstanding state ownership, provider behavior, graph dependencies, plan freshness, or the boundary between declarative infrastructure and imperative configuration.

## Mental model

A practical Terraform run can be modeled as:

```text
configuration + variables + provider schemas
                |
                v
        evaluate expressions
                |
                v
       build dependency graph
                |
                v
prior state <-> refresh/read remote objects
                |
                v
        calculate execution plan
                |
                v
      review / policy / approval
                |
                v
       execute graph operations
                |
                v
      provider remote API calls
                |
                v
          updated state
```

Several important consequences follow:

- Terraform does not simply replay configuration top-to-bottom.
- HCL block order is usually not execution order.
- Dependencies are inferred primarily from references and can be supplemented with `depends_on` when the dependency is behavioral rather than data-driven.
- State is not a cache that can always be deleted safely; it is part of Terraform's identity mapping between addresses and remote objects.
- A plan is a computed proposal based on a particular configuration, state snapshot, provider behavior, variable set, and observed remote reality.
- Providers are independent executable plugins with their own schemas, versions, API clients, retry behavior, bugs, and release cadence.

## What Terraform Core owns

Terraform Core is responsible for the generic infrastructure lifecycle machinery. Its major responsibilities include:

- reading Terraform configuration and module calls;
- evaluating expressions and input values;
- loading provider schemas;
- tracking resource addresses and instance identities;
- reading and writing Terraform state;
- building and walking the resource dependency graph;
- generating plans;
- coordinating create, read, update, delete, import, move, and replacement decisions;
- communicating with provider plugins over the Terraform Plugin Protocol.

Terraform Core does **not** contain the implementation details for every cloud API. Those belong to providers.

## Provider architecture

Providers are separate plugin processes. Terraform Core launches them and communicates through a versioned RPC protocol implemented with Protocol Buffers and gRPC.

A provider typically defines:

- provider-level configuration such as region, endpoint, credentials, or feature flags;
- managed resource types;
- data source types;
- schemas for configuration and computed attributes;
- CRUD and import behavior;
- optional ephemeral resources and write-only arguments in newer provider implementations;
- diagnostics, timeouts, retry behavior, and API-specific normalization.

The provider is the translation boundary between Terraform's abstract resource model and the remote system's API model.

This distinction explains many confusing failures. If a cloud API changes behavior, if a provider introduces a schema migration, or if a provider interprets an API field differently, Terraform Core may be working correctly while the resulting resource behavior still changes.

### Provider process boundary

Conceptually:

```text
Terraform Core
    |
    | Terraform Plugin Protocol
    | gRPC / protobuf
    v
Provider process
    |
    | vendor-specific SDK / HTTP / RPC
    v
Remote platform API
```

Providers should therefore be treated like executable supply-chain dependencies rather than static schema files.

## Provider source addresses and versions

A provider source address identifies its registry origin and namespace, for example:

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
```

Version constraints describe acceptable versions. Once Terraform selects a provider version, `.terraform.lock.hcl` records the selected version and package checksums.

A mature repository generally commits `.terraform.lock.hcl` so provider upgrades are visible in code review.

Important distinction:

- configuration version constraints define the allowed set;
- the dependency lock file records the selected provider version and checksums;
- remote module versions are not locked by `.terraform.lock.hcl`, so module source/version strategy requires separate care.

## Configuration language

Terraform configuration is declarative, but that does not mean every value is known immediately.

Configuration commonly contains:

- `terraform` settings;
- provider requirements;
- `provider` blocks;
- `resource` blocks;
- `data` blocks;
- `module` blocks;
- `variable` and `output` blocks;
- `locals`;
- `moved`, `removed`, and `import` blocks;
- lifecycle and instance-expansion meta-arguments.

Expressions create dependency edges when one object references another.

Example:

```hcl
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "app" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
}
```

The reference to `aws_vpc.main.id` gives Terraform enough information to infer that the subnet depends on the VPC.

## Unknown values during planning

Some values cannot be known until apply time. For example, an API may assign an ID only after creating an object.

Terraform can carry unknown values through the plan rather than requiring every expression to resolve to a concrete value immediately.

This is why a plan may show:

```text
(known after apply)
```

Unknown values are a normal part of Terraform's execution model. Problems arise when an expression must be known early enough to determine resource instance addresses, provider configuration, or graph shape.

## The dependency graph

Terraform constructs a directed dependency graph and walks it in dependency order.

Graph nodes can represent resources and provider configuration. Terraform also incorporates objects that exist in state but disappeared from configuration so it can plan their destruction or removal from management.

Graph edges come from several sources, especially:

- expression references;
- explicit `depends_on` declarations;
- provider dependencies;
- lifecycle and replacement constraints;
- state relationships needed for existing objects.

Terraform validates that the graph is acyclic before execution.

### Parallel graph walking

Independent nodes can execute concurrently once their dependencies are satisfied. This is why two unrelated resources may be created in parallel even if their blocks are adjacent in the file.

Terraform exposes `-parallelism` for advanced cases, but lowering parallelism is not a general substitute for provider-side retry/backoff or correct API quota design.

## `depends_on`

Use `depends_on` for hidden behavioral dependencies Terraform cannot infer from data references.

Example:

```hcl
resource "example_service" "api" {
  depends_on = [example_policy.binding]
}
```

Do not use broad `depends_on` chains as a default ordering mechanism. Excessive explicit dependencies can:

- serialize otherwise independent work;
- increase unknown values during planning;
- create brittle coupling;
- hide the actual data flow between resources.

Prefer direct references when a real data dependency exists.

## `count` and `for_each`

`count` and `for_each` expand one configuration block into multiple resource or module instances.

Prefer `for_each` when instances have durable semantic keys:

```hcl
resource "example_user" "team" {
  for_each = {
    alice = "admin"
    bob   = "reader"
  }

  name = each.key
  role = each.value
}
```

The keys become part of the Terraform address. Stable keys therefore help avoid unintended address churn.

A common failure pattern is using `count` with an ordered list and then removing an element from the middle. Later indexes shift, and Terraform may propose replacements or rebinding that are logically unrelated to the intended change.

## Resource addresses and identity

Terraform identifies managed instances using addresses such as:

```text
aws_instance.web
aws_instance.web[0]
aws_instance.web["blue"]
module.network.aws_subnet.private["az-a"]
```

The address is Terraform's configuration-side identity. State binds that address to provider-specific remote identity.

Changing an address without declaring the move can make Terraform interpret the change as:

```text
old address disappeared -> destroy old object
new address appeared     -> create new object
```

That is why refactors must be treated as lifecycle operations, not merely source-code renames.

## State

Terraform state stores bindings between resource instances in configuration and real remote objects.

State also stores metadata and attributes needed for planning and dependency evaluation.

The default local state file is `terraform.tfstate`. Team usage normally requires a remote backend or managed remote execution/state service with appropriate access control and locking.

### State is sensitive

State can contain:

- resource identifiers;
- network topology;
- internal endpoints;
- generated credentials;
- passwords or tokens returned by providers;
- other values marked sensitive in the UI but still physically stored.

Marking a value `sensitive` primarily controls display redaction. It does not automatically remove the value from state.

State storage must therefore be secured like production configuration data or secrets infrastructure, depending on the provider and resources involved.

## Remote state and backends

A backend determines where Terraform stores state and, depending on backend capabilities, may provide state locking.

State locking prevents concurrent writers from independently modifying the same state snapshot.

Important rules:

- use a backend that supports the collaboration and locking model your team needs;
- do not assume every backend supports locking;
- avoid disabling locks to bypass a legitimate concurrent writer;
- use `force-unlock` only when the stale lock is known to be yours and the original operation is no longer running;
- protect backend credentials separately from ordinary Terraform variables where possible.

### Failed remote state persistence

If Terraform cannot persist updated remote state after an operation, recovery becomes operationally sensitive. The remote infrastructure may already have changed even though the shared state did not update successfully.

Do not immediately re-run apply blindly. First determine:

1. which remote changes completed;
2. which state version is authoritative;
3. whether Terraform wrote a local emergency state file;
4. whether state must be recovered or pushed;
5. whether a new plan proposes duplicate creation or destructive correction.

## State commands

Useful inspection and maintenance commands include:

```bash
terraform state list
terraform state show ADDRESS
terraform state pull
terraform state mv OLD NEW
terraform state rm ADDRESS
```

State mutation commands are powerful and should be reviewed as production changes.

Avoid manually editing raw JSON unless there is no safer supported path and you fully understand state lineage, serials, provider schemas, and recovery implications.

## State lineage and serial

Terraform state contains lineage and serial information used to reduce accidental overwrites of unrelated or newer state.

When manually pushing state, Terraform checks these safeguards. Forcing past them is an emergency action, not an ordinary workflow.

## Refresh and drift

Before normal planning, Terraform reads remote objects through providers so it can compare current observed reality with configuration and prior state.

Drift can come from:

- manual console changes;
- other automation systems;
- provider or API defaults;
- controllers that continuously mutate resources;
- autoscaling systems;
- policy engines;
- external lifecycle managers.

The key design question is not merely "did drift occur?" but **which system owns that field or object?**

If multiple controllers intentionally own the same mutable property, recurring Terraform diffs are a symptom of an ownership conflict.

## Plan

`terraform plan` computes proposed actions without carrying them out.

A normal plan conceptually does three things:

1. reads current remote object information;
2. compares configuration with prior state and refreshed reality;
3. produces proposed actions intended to converge managed objects toward configuration.

Plans can include:

- create;
- update in place;
- destroy;
- replace;
- read data source;
- import;
- move/refactor effects;
- output changes.

### Speculative vs saved plan

Running:

```bash
terraform plan
```

without `-out` creates a speculative plan. It is useful for review but is not itself the exact artifact later applied.

For controlled automation:

```bash
terraform plan -out=tfplan
terraform show tfplan
terraform apply tfplan
```

The saved plan binds review more closely to execution.

Saved plan files can contain sensitive information. Treat them accordingly.

## Apply

`terraform apply` executes the operations proposed by a plan.

Without a saved plan, `apply` creates a fresh plan and asks for approval unless configured otherwise.

With a saved plan, Terraform executes that plan without another interactive approval prompt.

This difference is important in CI/CD: a pipeline that generates one plan for code review but later runs a fresh automatic plan during deployment is not applying the exact reviewed artifact.

## Plan freshness

A reviewed plan is not timeless.

Between plan and apply:

- remote infrastructure can change;
- credentials or permissions can change;
- APIs can return different computed values;
- external controllers can mutate objects;
- backend state can advance due to another run.

Keep the review-to-apply window bounded and enforce one-writer semantics for a state lineage.

## Replacement

Some resource changes cannot be performed in place. A provider schema can mark an attribute or operation such that Terraform must replace the resource.

Replacement may mean:

```text
create new -> switch dependencies -> destroy old
```

or:

```text
destroy old -> create new
```

The actual order depends on lifecycle rules, provider semantics, dependencies, quotas, and whether both objects can coexist.

Review replacement plans carefully for stateful or identity-bearing systems such as databases, DNS zones, persistent volumes, IAM resources, and externally referenced endpoints.

## Lifecycle meta-arguments

Lifecycle rules can change normal replacement or drift behavior.

Common examples include:

- `create_before_destroy`;
- `prevent_destroy`;
- `ignore_changes`;
- `replace_triggered_by`.

These are not general safety switches.

### `prevent_destroy`

Useful for adding friction around destruction of critical resources, but it is not a backup strategy and does not protect a resource if its entire configuration is removed in every possible workflow.

### `ignore_changes`

Useful when another system intentionally owns selected attributes, but dangerous when used broadly to silence unexplained drift.

Every ignored field should have a documented alternative owner.

### `create_before_destroy`

Can reduce downtime when replacement resources may coexist, but may fail because of:

- unique names;
- account quotas;
- exclusive bindings;
- IP or DNS constraints;
- remote platform restrictions.

## Modules

A module is a collection of Terraform resources managed together.

Every configuration has a root module. Root modules can call child modules.

Good modules encapsulate a useful infrastructure abstraction while keeping important operational choices visible.

Typical module interfaces consist of:

- input variables;
- output values;
- resource definitions;
- provider requirements;
- documented constraints and assumptions.

### Avoid over-abstracting

A module that exposes nearly every underlying provider argument can become a thin indirection layer with little value.

A module that hides every operational control can become impossible to adapt safely.

Good module boundaries usually correspond to an architectural responsibility, for example:

- VPC/network foundation;
- Kubernetes cluster baseline;
- application service infrastructure;
- database platform;
- identity or policy bundle.

## Module versioning

Reusable modules are APIs.

Breaking changes can include:

- renaming resources without `moved` blocks;
- changing `for_each` keys;
- changing variable types;
- changing defaults that alter infrastructure;
- removing outputs;
- changing provider assumptions;
- introducing new destructive lifecycle behavior.

Version modules and document upgrade paths accordingly.

## `moved` blocks

Use `moved` blocks to declare resource or module address refactors:

```hcl
moved {
  from = aws_instance.old
  to   = aws_instance.web
}
```

Terraform can then reinterpret existing state under the new address rather than planning destroy/create solely because the source address changed.

For reusable modules, keeping historical `moved` blocks preserves upgrade paths for users coming from older versions.

Removing a still-needed move declaration can itself become a breaking change.

## `removed` blocks

A `removed` block can declaratively remove an object from Terraform management and control whether the underlying object is destroyed.

This is useful when ownership moves to another system, but it must be explicit whether the intent is:

```text
stop managing object, keep remote object
```

or:

```text
stop managing object and destroy it
```

Confusing those two intents is a serious production risk.

## Importing existing infrastructure

Terraform can adopt existing remote resources.

Modern configuration-driven import uses `import` blocks that bind a remote identity to a Terraform resource address.

Example:

```hcl
import {
  to = aws_s3_bucket.logs
  id = "existing-logs-bucket"
}

resource "aws_s3_bucket" "logs" {
  bucket = "existing-logs-bucket"
}
```

A safe import workflow is:

1. identify the exact remote object;
2. define the destination resource address;
3. create configuration matching the intended managed settings;
4. plan;
5. inspect unexpected updates or replacements;
6. apply the import;
7. re-plan until Terraform is stable.

Importing does not automatically mean the written configuration matches every important remote setting.

## Workspaces

Terraform CLI workspaces allow multiple state instances for the same configuration.

They can be useful for some environment patterns, but they are not a universal environment-isolation mechanism.

Separate root configurations or repositories can be preferable when environments differ materially in:

- credentials;
- provider accounts;
- policy boundaries;
- topology;
- module versions;
- blast radius;
- deployment cadence.

Choose the isolation model based on ownership and failure domains, not only directory convenience.

## Sensitive data

Terraform needs access to credentials and often processes sensitive values.

Important distinction:

```text
sensitive = hidden from normal UI output
```

is not equivalent to:

```text
value is absent from state and plan artifacts
```

Terraform's newer ephemeral value mechanisms can omit selected temporary values from state and plan artifacts when both Terraform and the provider/resource support the required model.

As of the documentation reviewed on 2026-09-06:

- ephemeral variables and child-module outputs are available in Terraform 1.10+;
- provider-defined write-only resource arguments are supported in Terraform 1.11+;
- ephemeral resources are provider-defined and are not universally available.

Do not assume all provider secrets automatically use ephemeral or write-only mechanisms.

## Secret-handling principles

Prefer:

- short-lived workload identity instead of long-lived static cloud keys;
- environment or workload credential chains rather than hardcoded HCL secrets;
- restricted remote state access;
- backend encryption and transport security;
- ephemeral/write-only constructs where supported;
- secret rotation that does not require exposing values in logs or review artifacts.

Avoid:

- committing `.tfstate`;
- committing saved plans containing secrets;
- placing passwords directly in `.tf` or `.tfvars` files committed to Git;
- printing sensitive outputs with raw/JSON commands into CI logs;
- granting broad state-read access merely because a user can read configuration.

## `.terraform.lock.hcl`

The dependency lock file records selected provider versions and checksums.

Commit it for root configurations so provider changes are reviewable and reproducible across machines.

For multi-platform teams or build systems, ensure the lock file contains the required platform checksums using supported provider lock workflows rather than bypassing checksum verification.

## Provider supply-chain security

Terraform registry providers are executable binaries. Security considerations include:

- provider namespace/source correctness;
- version constraints;
- checksum verification;
- signature provenance;
- private or filesystem mirrors;
- compromised developer credentials publishing provider releases;
- malicious or abandoned community providers;
- provider plugins inheriting powerful cloud credentials from the Terraform process.

A Terraform provider running with production credentials can usually perform whatever the corresponding API credentials authorize.

Review provider changes like privileged dependency updates.

## Provider aliases

Multiple configurations of the same provider can be declared with aliases, for example for regions or accounts.

Module/provider wiring must be explicit enough that a module cannot accidentally operate in the wrong account, region, cluster, or subscription.

For high-risk environments, include account/tenant identity checks in the provider or pipeline design where available.

## Validation and formatting

Useful local checks include:

```bash
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

`validate` checks Terraform configuration structure and provider schema relationships after required providers/modules are initialized. It does not prove that a production apply is safe.

## Terraform tests

Terraform includes a native testing framework for modules.

Tests can execute plan- or apply-oriented runs and assertions using test-specific state.

Use tests for invariants such as:

- required tags or labels;
- generated naming rules;
- security-group policy;
- module outputs;
- conditional topology;
- resource count and relationships.

Remember that apply-based tests can create real infrastructure and therefore need isolated credentials, cleanup, quotas, and cost controls.

## Static policy and review

Production Terraform pipelines often add checks beyond Terraform itself, such as:

- HCL linting;
- provider/module allowlists;
- policy-as-code;
- security scanners;
- cost estimation;
- plan JSON review;
- destructive-change gates;
- protected environment approval.

These controls complement Terraform's plan; they do not replace understanding the proposed resource lifecycle.

## CI/CD workflow

A robust automation flow commonly looks like:

```text
pull request
  -> fmt / validate / tests / security checks
  -> terraform plan
  -> publish human-readable + machine-readable plan evidence
  -> review / policy / approval
  -> protected merge
  -> produce final non-speculative saved plan
  -> approval if required
  -> apply the exact saved plan
  -> persist state
  -> post-apply verification
```

The exact workflow depends on the backend and platform, but the important invariants are:

- serialize writes to one state lineage;
- bind apply to reviewed code and variables;
- prevent untrusted pull requests from obtaining production credentials;
- preserve logs without leaking secrets;
- make destructive actions conspicuous;
- retain state recovery capability.

## Pull-request security boundary

Never expose production cloud credentials to untrusted pull-request code merely to generate a plan.

Terraform configuration can invoke provider functionality and, depending on the environment and enabled features, may interact with local files, data sources, provisioners, external programs, or remote APIs.

Treat infrastructure pull requests as code execution and privilege-boundary events, not only text diffs.

## Provisioners

Provisioners execute imperative actions associated with resource lifecycle.

They are useful for narrow escape-hatch cases but often make infrastructure harder to reason about because Terraform cannot fully model the side effects.

Prefer purpose-built mechanisms such as:

- cloud-init/user-data;
- immutable images;
- configuration-management systems;
- Kubernetes controllers/operators;
- deployment systems;
- provider-native resources.

Use provisioners only when the side effect, failure semantics, idempotency, credentials, and retry behavior are understood.

## Terraform and configuration management

Terraform and Ansible overlap at the edges but have different centers of gravity.

Terraform is strongest when managing resource lifecycle through provider APIs and a persistent state model.

Ansible is commonly used for configuration management and imperative orchestration across hosts and services.

A useful ownership split can be:

```text
Terraform -> provision VM/network/IAM/load balancer
Ansible   -> configure software inside the VM
```

Avoid having both systems independently manage the same resource property without a deliberate coordination model.

## Terraform and Kubernetes

Terraform can provision:

- managed Kubernetes clusters;
- cloud networking and IAM around clusters;
- Kubernetes resources through providers.

But Kubernetes controllers continuously reconcile cluster objects, while Terraform typically runs periodically.

This can create ownership conflicts for fields mutated by controllers, admission systems, autoscalers, or operators.

For large application fleets, a common pattern is:

```text
Terraform -> cluster and foundational infrastructure
GitOps / Kubernetes controllers -> continuously reconciled application resources
```

The exact boundary is organizational, but it should be explicit.

## Terraform and OpenTofu

OpenTofu is a community-governed open-source infrastructure-as-code project with substantial Terraform heritage and compatibility goals.

Terraform releases from version 1.6.0 onward are distributed under Business Source License 1.1 in the upstream Terraform repository. The current license identifies a four-year change date to MPL-2.0 for each covered version and restricts certain competitive hosted or embedded uses.

This licensing history is materially relevant when choosing Terraform versus OpenTofu for products, managed services, distributions, or long-lived open-source platform strategies.

Compatibility should be verified for the specific versions, providers, state operations, language features, and workflows in use rather than assumed indefinitely.

## Performance and scale

Terraform performance can be affected by:

- number of resource instances;
- provider API latency;
- provider rate limits and retries;
- large state files;
- high graph fan-out;
- expensive data sources;
- repeated module expansion;
- slow refresh operations;
- remote backend latency;
- provider schema initialization;
- excessive explicit dependencies reducing concurrency.

### Split state by operational boundary

Do not split state merely to make files smaller.

Useful boundaries often correspond to:

- independent ownership teams;
- different credentials/accounts;
- different change cadence;
- different blast radius;
- stable interfaces between layers.

For example:

```text
foundation network state
cluster platform state
application service state
```

This can reduce lock contention and blast radius, but it introduces cross-state interfaces that must be versioned and managed.

## Cross-state coupling

Reading outputs from another state can create a hidden API between infrastructure stacks.

Treat exposed outputs like a contract. Excessive remote-state coupling can make independent deployment difficult.

Where appropriate, publish stable integration data through platform-native discovery mechanisms such as:

- DNS;
- parameter stores;
- secret stores;
- service registries;
- cloud resource tags;
- well-defined deployment metadata.

## API rate limits

Terraform graph parallelism can generate bursts of API requests.

Do not blindly lower global parallelism as the first response to rate limiting. Investigate:

- provider retry/backoff implementation;
- account quotas;
- API concurrency constraints;
- unusually expensive data sources;
- duplicated refresh work;
- provider bugs;
- unnecessary graph fan-out.

## Failure modes

### Concurrent applies

Symptoms:

- lock contention;
- stale plans;
- state write conflicts;
- contradictory resource operations.

Response:

- enforce one writer per state;
- restore locking rather than bypassing it;
- cancel or serialize duplicate automation jobs.

### Resource created but state write failed

Symptoms:

- remote object exists;
- shared state does not record it;
- next plan proposes another create.

Response:

- stop automatic retries;
- inspect local emergency state and remote object identity;
- recover state or import deliberately.

### Address refactor causes destroy/create

Cause:

- resource/module address changed without a `moved` declaration.

Response:

- add `moved` block or perform a reviewed state move;
- re-plan before apply.

### Provider upgrade creates widespread diffs

Possible causes:

- schema migration;
- changed defaults;
- normalization behavior;
- API compatibility changes;
- newly computed fields;
- bug fixes exposing previous drift.

Response:

- isolate provider upgrades;
- read provider release notes;
- inspect representative resources;
- roll forward or pin deliberately rather than editing state to hide diffs.

### Permanent drift

Symptoms:

- every plan wants to change the same field back;
- another controller later changes it again.

Response:

- establish a single field owner;
- redesign ownership or narrowly use `ignore_changes` when external ownership is intentional.

### Dependency cycle

Terraform rejects cyclic graphs.

Fix the architecture rather than trying to force statement order. Cycles often reveal two components that require a bootstrap phase or a weaker interface.

### `for_each` key churn

Changing stable keys changes resource addresses.

Use semantic durable keys and migrate addresses with `moved` blocks where appropriate.

### Provider credential mismatch

Symptoms:

- plan runs against wrong account/region;
- unexpected mass create/destroy;
- data sources return surprising objects.

Response:

- verify account identity before planning;
- use explicit provider aliases;
- isolate environment credentials;
- include environment identity in CI safeguards.

### Stale saved plan

A plan can become invalid or unsafe after state or remote reality changes.

Regenerate the plan when its assumptions no longer hold.

## Debugging workflow

When a plan is surprising, avoid immediately applying to "see what happens."

Use a staged workflow:

1. confirm workspace/backend and target account;
2. inspect `terraform version` and provider selections;
3. inspect `.terraform.lock.hcl` changes;
4. run `terraform validate`;
5. generate a fresh plan;
6. isolate the first unexpected resource diff;
7. inspect that resource in state;
8. inspect the remote API object;
9. check provider release notes and schema changes;
10. inspect dependency references and lifecycle rules;
11. fix configuration, ownership, state mapping, or provider version deliberately;
12. regenerate the entire plan.

Useful commands include:

```bash
terraform providers
terraform providers schema -json
terraform state list
terraform state show ADDRESS
terraform show -json tfplan
terraform graph
terraform console
```

Enable detailed Terraform/provider logging only when needed and protect logs because they may expose sensitive operational data.

## Destructive-plan review

For every destroy or replacement, ask:

- Is the address change intentional?
- Is this resource stateful?
- Is there a backup or recovery path?
- Can old and new resources coexist?
- Are external systems referencing the old identity?
- Will DNS, IAM, certificates, IPs, or persistent storage change?
- Is the destroy caused by a provider upgrade or configuration refactor rather than an actual product requirement?

## Disaster recovery

A Terraform disaster-recovery plan should include:

- backend backup/versioning strategy;
- state access recovery;
- provider and module version reconstruction;
- credentials/bootstrap recovery;
- remote object inventory;
- import procedures;
- tested restore documentation.

Terraform configuration without recoverable state may not be sufficient to reconstruct ownership mappings safely.

## Anti-patterns

Avoid:

- storing state in Git;
- using one giant state for unrelated organizations or failure domains;
- generating a reviewed plan and then applying a different unreviewed plan;
- using `-target` as routine deployment architecture;
- disabling state locking to get around another active run;
- broad `ignore_changes` to silence unexplained drift;
- manually editing JSON state as normal maintenance;
- unpinned provider upgrades in production;
- treating provider binaries as harmless metadata;
- mixing Terraform and another controller on the same fields without ownership rules;
- embedding long-lived credentials in HCL;
- using provisioners as the default configuration-management layer;
- refactoring resource addresses without explicit migration.

## When targeted operations are appropriate

`-target` is primarily an exceptional recovery or troubleshooting tool, not a normal partial-deployment mechanism.

Frequent dependence on targeting often indicates the state or module boundary is too broad or the deployment architecture lacks independent lifecycle units.

## Operational checklist

Before merging:

- format and validate configuration;
- review provider and lock-file changes;
- verify module versions;
- run appropriate Terraform tests;
- generate a plan against the correct backend/account;
- inspect replacements and destroys;
- review security and policy checks;
- verify secrets are not exposed in artifacts.

Before apply:

- confirm state lock ownership;
- confirm reviewed commit and variables;
- confirm environment identity;
- confirm plan freshness;
- apply the exact approved saved plan where the workflow supports it;
- ensure backup/recovery is available for stateful changes.

After apply:

- confirm state persisted successfully;
- verify critical remote resources;
- monitor service health;
- run a new plan when appropriate to identify unexpected residual drift.

## Learning path

### Beginner

Learn:

- providers;
- resources and data sources;
- variables and outputs;
- `init`, `plan`, `apply`, and `destroy`;
- state basics;
- direct expression dependencies.

### Intermediate

Learn:

- modules;
- `for_each` and `count`;
- provider aliases;
- remote backends and locks;
- lifecycle rules;
- imports;
- `moved` blocks;
- dependency lock files;
- CI planning workflows.

### Advanced

Learn:

- Terraform graph internals;
- provider protocol and schema behavior;
- state recovery and migration;
- reusable-module compatibility;
- cross-state interfaces;
- provider supply-chain controls;
- policy-as-code;
- large-estate state partitioning;
- drift ownership;
- sensitive/ephemeral value semantics;
- disaster recovery and incident response.

## Relationships

### OpenTofu

`tool/opentofu` is the closest indexed alternative. The tools share substantial infrastructure-as-code heritage, but governance, licensing, release decisions, and feature evolution are independent and should be evaluated explicitly.

### Kubernetes

`cloud/kubernetes` is a common Terraform integration target. Terraform is frequently used to provision cluster infrastructure and foundational resources, while Kubernetes controllers own continuous in-cluster reconciliation.

### Ansible

`cloud/ansible` is adjacent rather than identical. Terraform usually centers on resource lifecycle and state; Ansible commonly centers on configuration management and orchestration.

## Taxonomy

- Kind: `tool`
- Domains: `cloud`, `devops`
- Deployment: `cli`, `local`
- License: `BUSL-1.1`
- Maturity: `deep-dive`

## Primary references

- Terraform documentation: https://developer.hashicorp.com/terraform
- Terraform repository: https://github.com/hashicorp/terraform
- Terraform license: https://github.com/hashicorp/terraform/blob/main/LICENSE
- State: https://developer.hashicorp.com/terraform/language/state
- Backends: https://developer.hashicorp.com/terraform/language/state/backends
- State locking: https://developer.hashicorp.com/terraform/language/state/locking
- Dependency graph: https://developer.hashicorp.com/terraform/internals/graph
- Plugin architecture: https://developer.hashicorp.com/terraform/plugin/how-terraform-works
- Plugin protocol: https://developer.hashicorp.com/terraform/plugin/terraform-plugin-protocol
- Provider block: https://developer.hashicorp.com/terraform/language/block/provider
- Modules: https://developer.hashicorp.com/terraform/language/modules
- Plan: https://developer.hashicorp.com/terraform/cli/commands/plan
- Apply: https://developer.hashicorp.com/terraform/cli/commands/apply
- Dependency lock file: https://developer.hashicorp.com/terraform/language/files/dependency-lock
- Sensitive data: https://developer.hashicorp.com/terraform/language/manage-sensitive-data
- Import: https://developer.hashicorp.com/terraform/language/import
- Module refactoring: https://developer.hashicorp.com/terraform/language/modules/develop/refactoring
- Tests: https://developer.hashicorp.com/terraform/language/tests

## Verification

This deep-dive was reviewed on **2026-09-06** against current HashiCorp Terraform documentation and the upstream Terraform repository. Fast-moving provider features, registry behavior, Terraform version requirements, licensing interpretation, and HCP-specific capabilities should be rechecked against their current primary documentation before operational decisions.

## Maintenance

Prioritize review when:

- Terraform Core changes the state, plan, import, test, or ephemeral-value model;
- the Terraform Plugin Protocol changes materially;
- provider installation or signature behavior changes;
- the upstream license changes;
- Terraform/OpenTofu compatibility materially diverges;
- backend locking or state-security guidance changes;
- new language constructs alter resource identity or refactoring semantics.
