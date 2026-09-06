# OpenTofu

> Community-governed open-source infrastructure-as-code engine that evaluates declarative configuration, coordinates provider plugins, tracks resource identity in state, plans dependency-aware lifecycle changes, and applies them through cloud, SaaS, and infrastructure APIs while maintaining broad Terraform workflow compatibility.

OpenTofu is best understood as a **stateful infrastructure reconciliation and change-planning engine**. Its roots are in Terraform's open-source codebase and language/workflow model, but it is now independently governed, MPL-2.0 licensed, distributed through the OpenTofu project, and able to evolve its own language, security, registry, and compatibility features.

The practical model is:

```text
configuration + variables + provider schemas
                |
                v
        evaluate configuration
                |
                v
       build dependency graph
                |
                v
state <-> read current remote objects
                |
                v
          calculate plan
                |
                v
       review / policy / approval
                |
                v
            tofu apply
                |
                v
        provider API calls
                |
                v
           updated state
```

That model is intentionally similar to Terraform because broad workflow compatibility is part of OpenTofu's design. The important engineering differences are not merely command names. They include project governance, licensing, registry infrastructure, compatibility promises, feature evolution, and OpenTofu-specific capabilities such as built-in state and plan encryption.

## Project identity

OpenTofu is an open-source infrastructure-as-code project governed under the Linux Foundation ecosystem and licensed under **Mozilla Public License 2.0**.

The command-line entry point is:

```bash
tofu
```

Primary workflow commands include:

```bash
tofu init
tofu validate
tofu plan
tofu apply
tofu destroy
```

The project deliberately preserves many familiar Terraform concepts so existing infrastructure code can often migrate with limited changes, but compatibility should be verified for the exact versions and features in use.

## What OpenTofu Core owns

OpenTofu Core provides the generic lifecycle engine. Its responsibilities include:

- parsing and evaluating configuration;
- loading modules;
- resolving provider requirements;
- tracking resource addresses and instances;
- reading and writing state;
- building dependency relationships;
- refreshing remote objects through providers;
- generating execution plans;
- coordinating apply/destroy/import/refactor operations;
- communicating with provider plugins through the provider wire protocol.

Provider-specific API behavior remains outside Core.

## Providers

Providers are executable plugins that let OpenTofu interact with remote systems.

A provider can define:

- managed resource types;
- data sources;
- configuration schemas;
- remote object identity and import behavior;
- create/read/update/delete operations;
- provider-specific validation and diagnostics;
- API retries, timeouts, defaults, and normalization.

Conceptually:

```text
OpenTofu Core
     |
     | provider wire protocol
     v
provider plugin
     |
     | cloud / SaaS / infrastructure API
     v
remote system
```

Provider binaries are independent software dependencies. Their release cadence and behavior are not controlled by OpenTofu Core.

## Public OpenTofu Registry

OpenTofu uses the **Public OpenTofu Registry** for provider and module discovery rather than depending on Terraform's public registry as its primary registry service.

OpenTofu continues to work with the broad Terraform provider ecosystem because providers use a compatible protocol and their licenses are separate from Terraform Core.

This does not imply that every future provider, provider feature, registry behavior, or Terraform-specific integration will remain compatible forever. Production teams should pin and test the exact provider versions they use.

## Provider requirements

Provider dependencies are declared in `required_providers`:

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

The `terraform` block name remains supported for compatibility with Terraform configuration.

Each provider requirement has:

- a local name;
- a source address;
- a version constraint.

Provider configurations then define environment-specific settings such as region, endpoint, authentication, or aliases.

## Provider version strategy

For reusable child modules, broad minimum-compatible constraints are often appropriate so the module does not unnecessarily block consumers.

For root configurations, stronger upper bounds or controlled upgrade policy can reduce surprise from provider releases.

Regardless of constraint strategy, production systems should review provider upgrades as privileged dependency changes.

## Dependency lock file

OpenTofu uses `.terraform.lock.hcl` for provider dependency selections and checksums.

The historical filename is intentionally retained for compatibility.

The lock file:

- belongs to the whole root configuration;
- records selected provider versions;
- records provider package hashes;
- is updated by initialization and provider lock workflows;
- should normally be committed to version control for root configurations.

It currently locks providers, not remote module versions.

## Configuration files

OpenTofu accepts familiar Terraform-style file formats and OpenTofu-specific equivalents.

A module can contain:

```text
*.tf
*.tf.json
*.tofu
*.tofu.json
```

Files in one module directory are evaluated as one configuration. File order does not define execution order.

This is a critical concept: infrastructure ordering is determined by dependency relationships, not by the textual order of `.tf` or `.tofu` files.

## Resource dependency model

References create implicit dependencies.

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

The subnet depends on the VPC because it references the VPC ID.

Use `depends_on` only for behavioral dependencies that are real but not visible through data references.

Excessive explicit dependencies can make plans harder to understand and reduce safe parallelism.

## Resource addresses

OpenTofu identifies managed instances through addresses such as:

```text
aws_instance.web
aws_instance.web[0]
aws_instance.web["blue"]
module.network.aws_subnet.private["az-a"]
```

Addresses matter because state binds those addresses to remote object identities.

Changing an address without a deliberate migration can be interpreted as:

```text
old resource disappeared -> remove or destroy
new resource appeared     -> create
```

Treat address changes as lifecycle migrations, not cosmetic refactors.

## `count` and `for_each`

Instance expansion creates multiple resource or module instances from one block.

Prefer `for_each` when instances have durable semantic keys:

```hcl
resource "example_service" "app" {
  for_each = {
    api = 8080
    web = 80
  }

  name = each.key
  port = each.value
}
```

Stable keys create stable addresses.

Using list indexes as long-lived identity can lead to accidental address churn when list order changes.

## Unknown values

Some values are unavailable until providers create or read remote objects.

Plans can carry unknown values forward and display them as values that will be known after apply.

Unknown values are normal. Problems appear when an unknown value is required to determine configuration structure, instance addressing, backend initialization, or other early-evaluation decisions.

## State

OpenTofu state records the binding between configuration resource instances and real remote objects.

State is required for normal lifecycle management because configuration alone does not encode every provider-assigned identity or historical mapping.

The default local state filename remains:

```text
terraform.tfstate
```

This historical naming is retained for ecosystem compatibility.

## Why state matters

State provides:

- resource-address to remote-object binding;
- provider metadata;
- previously observed attributes;
- dependency information needed during lifecycle operations;
- information used for performance and planning.

Deleting state is therefore not equivalent to clearing a cache. It can sever OpenTofu's knowledge of what it owns.

## Remote backends

A backend defines where OpenTofu stores persistent state.

Production teams commonly use remote storage so multiple operators and automation workers share one authoritative state lineage.

Backends differ in capabilities. Some support locking; some do not.

Do not assume remote storage automatically means safe concurrent writes.

## State locking

If the selected backend supports locking, OpenTofu locks state for operations that can write it.

The lock prevents multiple writers from independently changing the same state.

Avoid disabling locks to bypass another active apply.

`tofu force-unlock` should be reserved for a stale lock whose owning operation is known to be gone.

## State lineage and serial

State contains lineage and serial metadata to help protect against pushing unrelated or older state over newer state.

Force-overriding these protections is an emergency operation.

Before any manual state push:

- back up the destination state;
- verify lineage;
- verify serial direction;
- confirm no active writer exists;
- confirm the remote infrastructure matches the intended recovered state.

## State commands

Useful commands include:

```bash
tofu state list
tofu state show ADDRESS
tofu state pull
tofu state mv OLD NEW
tofu state rm ADDRESS
```

These are production mutation tools, not harmless inspection utilities.

## Failed remote state persistence

A particularly dangerous failure is:

```text
remote API change succeeded
but
updated shared state could not be persisted
```

The next run may then propose duplicate creation or incorrect remediation.

When this occurs:

1. stop automatic retries;
2. inspect which remote operations completed;
3. inspect any local emergency state OpenTofu wrote;
4. determine which state snapshot is authoritative;
5. recover or import deliberately;
6. generate a new plan only after identity is reconciled.

## Plan

`tofu plan` evaluates configuration and compares desired state with managed remote reality.

A plan can propose:

- create;
- update;
- destroy;
- replacement;
- import;
- read;
- refactor/move effects;
- output changes.

A plan is evidence for review, not a proof that the remote system will remain unchanged until apply.

## Apply

`tofu apply` executes the planned lifecycle operations.

In automation, prefer a workflow that ensures the exact approved configuration, variables, providers, and state are the ones that reach apply.

The stronger pattern is:

```text
reviewed commit
 -> final plan
 -> policy/approval
 -> apply exact approved plan
```

rather than:

```text
review one plan
 -> later generate unrelated fresh plan
 -> auto-approve it
```

## Plan freshness

A plan can become stale because:

- state advanced in another run;
- infrastructure drifted;
- provider behavior changed;
- credentials changed;
- environment variables changed;
- remote controllers mutated objects.

Keep the plan-to-apply interval bounded and preserve single-writer semantics for state.

## Drift and ownership

Drift means observed remote reality differs from configuration/state expectations.

Possible causes include:

- console changes;
- another IaC system;
- autoscalers;
- Kubernetes controllers;
- API defaults;
- provider normalization changes;
- policy engines.

The correct question is not only "how do we suppress the diff?" but "which controller owns this field?"

If two systems intentionally write the same field, permanent drift is a predictable consequence.

## Modules

Modules package reusable configuration.

Every OpenTofu configuration has a root module. Child modules can be loaded from local paths or registries.

Good modules expose stable infrastructure contracts rather than hiding every provider detail.

Typical module interfaces contain:

- input variables;
- outputs;
- provider requirements;
- resources;
- documented assumptions.

## Module compatibility

Modules are APIs.

Breaking changes can include:

- renaming resource addresses;
- changing `for_each` keys;
- changing input types;
- changing defaults that trigger infrastructure replacement;
- removing outputs;
- changing provider constraints;
- changing state ownership boundaries.

Version reusable modules and provide migration guidance.

## Provider configurations in modules

Provider configurations are generally defined in the root module and passed to child modules.

This keeps account, region, endpoint, and credential ownership at the composition layer instead of burying environment-specific authentication inside reusable modules.

For multi-account or multi-region systems, aliases should be explicit and reviewed carefully.

## State and plan encryption

One of OpenTofu's major native security features is **state and plan encryption at rest**.

OpenTofu can encrypt:

- state files;
- saved plan files;
- remote-state data-source payload handling under configured encryption rules.

Encryption can protect sensitive state content when an attacker obtains the stored state artifact.

It does **not** replace:

- backend access control;
- state versioning/backup;
- replay protection;
- key recovery;
- transport security;
- credential least privilege.

## Encryption architecture

OpenTofu's encryption configuration separates:

- key providers;
- encryption methods;
- state/plan policy;
- migration fallback behavior.

Conceptually:

```text
KMS / passphrase / key provider
          |
          v
   data encryption key
          |
          v
      AES-GCM method
          |
          v
 encrypted state / plan
```

KMS-backed key providers can generate/wrap per-artifact data encryption keys.

OpenTofu documentation recommends isolating state files with separate KMS keys rather than sharing one key broadly across many independent states.

## Encryption key providers

Supported key-provider families evolve over time. Current documentation includes integrations such as:

- AWS KMS;
- Google Cloud KMS;
- Azure Key Vault / Managed HSM integrations;
- OpenBao;
- PBKDF2-derived keys;
- external key-provider mechanisms.

Treat the current docs as authoritative because crypto integrations and method versions can change across minor releases.

## Encryption methods

Current OpenTofu documentation describes AES-GCM as the primary built-in encryption method and also supports external encryption methods.

Do not hard-code assumptions about method availability across future versions. Encryption components have a narrower compatibility guarantee than the general v1.x language surface.

## Encryption migration

Existing plaintext state is not automatically accepted after strict encryption is enabled.

A safe migration uses an explicit fallback/migration configuration so OpenTofu can read the old format and rewrite using the new method.

The same principle applies to key rotation:

```text
new method = primary
old method = fallback for read
next successful write = new format
```

After migration succeeds, remove obsolete fallback paths as appropriate.

## Encryption disaster recovery

Encryption creates a new failure mode: **state can become permanently unreadable if keys are lost**.

Before enabling encryption:

- test state backup recovery;
- test key recovery;
- document the KMS/key ownership team;
- define key-rotation procedures;
- separate keys by state/failure domain;
- verify break-glass access;
- confirm CI runners can access keys without embedding static secrets.

Encryption without key recovery can convert a confidentiality improvement into an availability disaster.

## Encryption does not stop replay

At-rest encryption alone does not guarantee state freshness.

An attacker or operational mistake could present an older encrypted state artifact. Use backend versioning, locking, audit logs, IAM, and workflow controls to protect state integrity and recency.

## Backends and encryption are separate concerns

Backend encryption and OpenTofu application-level encryption can coexist but protect different boundaries.

For example:

```text
object-storage server-side encryption
```

protects storage at the backend service boundary, while:

```text
OpenTofu state encryption
```

can protect the payload before it is handed to the backend.

Evaluate threat models rather than assuming one layer makes the other redundant.

## Secrets in state

Provider-managed attributes may contain sensitive values.

Even when a CLI masks a value, the underlying state can still contain it unless the feature/provider explicitly avoids persistence.

Therefore:

- restrict state readers;
- use workload identity for provider credentials;
- encrypt state when appropriate;
- minimize secret material returned by resources;
- avoid committing state or plan files;
- audit CI logs and exported JSON.

## Compatibility promises

OpenTofu publishes **v1.x compatibility promises** covering a substantial stable subset of:

- language behavior;
- CLI workflow behavior;
- provider wire protocol compatibility;
- provider/module installation protocols.

The intent is that valid modules written for the stable v1.x base continue to plan/apply across v1.x without required changes within the promised surface.

Important exclusions remain.

Provider behavior is independently versioned and is not guaranteed by OpenTofu Core compatibility promises.

Experimental features and deprecated behavior can also have different stability rules.

## Terraform compatibility

OpenTofu aims for broad Terraform configuration and provider compatibility, but it is not frozen as an identical implementation.

Compatibility should be evaluated at several layers:

```text
configuration syntax
language semantics
provider wire protocol
provider packages
module sources
state format/semantics
backend behavior
registry behavior
CLI automation
new feature usage
```

A successful `tofu plan` with no unexpected changes is much stronger migration evidence than assuming compatibility from project ancestry.

## Migrating from Terraform

OpenTofu's migration guidance emphasizes reversibility and state safety.

A practical migration flow is:

1. back up configuration and state;
2. record current Terraform/provider versions;
3. install the migration-compatible OpenTofu version;
4. initialize with OpenTofu;
5. run `tofu plan`;
6. require zero or fully explained changes;
7. test a small controlled change;
8. migrate CI/CD runners;
9. update documentation and tooling assumptions;
10. only then adopt OpenTofu-specific features.

## Version-specific migration paths

Do not assume that every Terraform version can jump directly to every OpenTofu version.

OpenTofu publishes version-specific migration guidance because state, provider, and language compatibility can differ across release lines.

Follow the documented path for the Terraform version actually in use.

## Interdependent state migration

Migration becomes more complex when multiple configurations exchange data through remote state.

Before migrating one stack independently, verify:

- state format compatibility;
- encryption settings;
- backend access;
- remote-state data source behavior;
- downstream consumer expectations;
- rollback order.

Cross-state dependencies turn migration order into an architecture concern.

## Terraform -> OpenTofu registry behavior

OpenTofu uses its own registry infrastructure and mirrors/indexes the provider ecosystem for OpenTofu workflows.

Automation that hardcodes Terraform registry hosts, credentials, module discovery assumptions, or API endpoints may need adjustment even when the HCL configuration itself is compatible.

Audit tooling around the CLI, not just `.tf` files.

## OpenTofu-specific language evolution

OpenTofu can introduce language features that Terraform does not understand.

For example, newer OpenTofu documentation includes OpenTofu-specific language/compatibility settings while retaining the `terraform` block as a compatibility mechanism.

Once a codebase adopts OpenTofu-only syntax or behavior, bidirectional portability may decrease.

Treat this as a deliberate product choice rather than accidental drift.

## File extension strategy

Because OpenTofu accepts both `.tf` and `.tofu` configuration files, teams can choose a portability strategy.

Using `.tf` plus Terraform-compatible language features can preserve broader interoperability.

Using `.tofu` or OpenTofu-only language features can make project intent explicit but may reduce Terraform compatibility.

Document the intended portability level in repository policy.

## CI/CD workflow

A hardened OpenTofu pipeline commonly looks like:

```text
pull request
 -> tofu fmt / validate
 -> provider lock review
 -> tests / static analysis / policy
 -> speculative plan
 -> human review
 -> protected merge
 -> final plan
 -> approval
 -> apply exact approved plan
 -> state persistence verification
 -> service verification
```

Security invariants:

- untrusted PRs do not receive production credentials;
- state writes are serialized;
- provider upgrades are explicit;
- encrypted-state keys are unavailable to unnecessary jobs;
- plan/state artifacts are treated as sensitive;
- backend identity is verified before planning/applying.

## Pull-request threat model

Infrastructure configuration is executable in effect.

A malicious change may attempt to:

- read data sources;
- invoke privileged provider operations;
- exfiltrate outputs;
- alter state ownership;
- use provisioners/external hooks;
- manipulate backend/encryption settings;
- change provider source addresses.

Never grant production cloud or encryption-key access to untrusted fork/pull-request code without a strong isolation model.

## Provider supply-chain security

Providers are executable binaries with the credentials of the OpenTofu process.

Review:

- source namespace;
- selected version;
- checksums;
- lock-file changes;
- provider ownership/maintenance status;
- release notes;
- private registry/mirror configuration.

A provider compromise can be equivalent to privileged code execution in the infrastructure control plane.

## Modules and supply chain

Remote modules are source code dependencies.

Pin module versions or immutable references according to organizational policy.

Because `.terraform.lock.hcl` does not lock module versions, reproducibility requires explicit module version/ref discipline.

## State partitioning

Split state by operational boundary rather than arbitrary object count.

Good boundaries may follow:

- ownership team;
- cloud account/subscription;
- credentials;
- change cadence;
- blast radius;
- recovery domain.

Example:

```text
network foundation
cluster platform
application infrastructure
```

Benefits include smaller blast radius and less lock contention.

Costs include cross-state interfaces and more orchestration.

## Cross-state interfaces

Remote-state outputs create an API between infrastructure stacks.

Treat output names, types, semantics, and lifecycle as versioned contracts.

For looser coupling, publish integration data through platform-native interfaces such as:

- DNS;
- parameter stores;
- secret stores;
- service registries;
- resource tags;
- configuration APIs.

## OpenTofu and Kubernetes

OpenTofu can provision Kubernetes clusters and manage Kubernetes resources through providers.

However, Kubernetes controllers continuously reconcile desired state inside the cluster, while OpenTofu generally reconciles during explicit runs.

A common ownership model is:

```text
OpenTofu -> cloud network, IAM, cluster, foundational platform
GitOps/controllers -> continuously reconciled application manifests
```

Avoid multiple systems owning the same mutable fields.

## OpenTofu and Terraform

OpenTofu and Terraform solve substantially the same infrastructure-as-code problem using related language, provider, and state concepts.

Key evaluation dimensions include:

- license;
- governance;
- provider/module ecosystem compatibility;
- registry behavior;
- state interoperability;
- feature roadmap;
- automation tooling;
- support/commercial ecosystem;
- OpenTofu-specific features such as state/plan encryption;
- Terraform-specific features introduced after project divergence.

Do not reduce the comparison to "same syntax" or "one is open source."

## Licensing difference

OpenTofu Core is **MPL-2.0**.

Terraform versions 1.6.0 and later in the upstream Terraform repository are distributed under **BUSL-1.1** with an additional-use grant and per-version change date.

This can materially affect decisions for:

- hosted infrastructure platforms;
- embedded products;
- commercial distributions;
- open-source ecosystem strategy;
- long-lived platform standardization.

License questions with business consequences should be reviewed with current upstream license text and appropriate legal counsel.

## Performance

OpenTofu performance depends on:

- provider API latency;
- state size;
- resource graph size;
- provider initialization;
- backend latency;
- module expansion;
- refresh volume;
- API rate limits;
- unnecessary dependency serialization.

Changing graph parallelism is an advanced tuning tool, not a universal rate-limit fix.

Investigate provider retry behavior, API quotas, state boundaries, and data-source costs first.

## Failure modes

### Concurrent applies

Symptoms:

- lock contention;
- stale plans;
- contradictory writes.

Response:

- preserve single-writer state semantics;
- cancel duplicate automation;
- do not bypass a valid lock.

### Remote object changed but state write failed

Response:

- stop retries;
- inspect remote reality;
- inspect emergency local state;
- recover state or import deliberately.

### Lost encryption key

Impact:

- encrypted state/plan may become unrecoverable.

Response:

- restore key from documented recovery path;
- do not rotate/delete KMS keys without state migration;
- exercise key recovery before production encryption rollout.

### Encryption configuration renamed incorrectly

Encrypted metadata can depend on configured key-provider/method identity.

Use documented rollover/fallback mechanisms rather than casually renaming encryption components.

### Terraform migration produces changes

Do not apply merely to "finish migration."

Investigate:

- provider versions;
- state format/version;
- registry source resolution;
- Terraform-version-specific features;
- backend behavior;
- configuration semantics.

A migration plan should be zero-diff or every diff must be explicitly understood.

### Provider upgrade creates large diffs

Provider releases evolve independently from OpenTofu Core.

Pin, review, and test provider upgrades separately.

### Address churn

Resource/module renames or unstable instance keys can cause create/destroy proposals.

Use supported refactoring/state migration mechanisms.

### Permanent controller drift

When another controller continuously changes attributes OpenTofu manages, repeated plans are expected.

Resolve ownership rather than hiding the symptom globally.

## Debugging workflow

When a plan is surprising:

1. verify current workspace/backend;
2. verify cloud account/tenant/region;
3. record `tofu version`;
4. inspect provider selections and lock changes;
5. run `tofu validate`;
6. generate a fresh plan;
7. identify the first unexpected resource;
8. inspect its state address and provider;
9. inspect the real remote object;
10. compare provider release notes;
11. check migration/compatibility docs if crossing Terraform/OpenTofu versions;
12. regenerate the full plan after the fix.

Useful commands:

```bash
tofu providers
tofu state list
tofu state show ADDRESS
tofu state pull
tofu show -json PLAN
tofu console
tofu graph
```

Protect verbose logs because provider diagnostics can contain sensitive operational data.

## Migration validation checklist

Before moving Terraform workloads to OpenTofu:

- back up state and configuration;
- identify every Terraform version in use;
- inventory providers and versions;
- inventory modules and source registries;
- inventory backends/workspaces;
- find remote-state dependencies;
- identify Terraform-only features;
- identify CI tools that invoke `terraform` by name;
- identify registry-host assumptions;
- run the version-specific OpenTofu migration guide;
- require a clean or fully explained plan;
- test rollback.

## Encryption rollout checklist

Before enabling OpenTofu native encryption:

- choose state/plan encryption scope;
- define KMS/key ownership;
- create separate key boundaries per state where appropriate;
- back up plaintext state temporarily for migration safety;
- test fallback migration;
- verify CI key access;
- test key rotation;
- test disaster recovery;
- enable enforcement only after successful migration;
- remove obsolete plaintext fallback once safe.

## Operational checklist

Before merge:

- run format/validate;
- review provider and module dependency changes;
- inspect registry/source-address changes;
- run tests/policy checks;
- review speculative plan;
- inspect all destroy/replacement operations.

Before apply:

- confirm backend/workspace;
- confirm environment identity;
- confirm lock ownership;
- confirm exact reviewed commit and variables;
- confirm encryption keys are available and correct;
- confirm plan freshness.

After apply:

- verify state persisted;
- verify encrypted state remains readable by the intended recovery path;
- verify critical resources;
- run post-apply monitoring/health checks;
- generate a follow-up plan when appropriate to detect residual drift.

## Anti-patterns

Avoid:

- treating OpenTofu as stateless YAML/HCL execution;
- committing state or saved plans;
- bypassing active state locks;
- unreviewed provider upgrades;
- manually editing raw state as routine maintenance;
- enabling encryption without key recovery;
- sharing one high-value encryption key across unrelated state domains without reason;
- assuming encryption prevents stale-state replay;
- assuming Terraform compatibility without a migration plan;
- adopting OpenTofu-only features while claiming full Terraform portability;
- allowing untrusted PRs to use production credentials or state keys;
- using one giant state across unrelated ownership domains;
- letting multiple controllers own the same fields.

## Learning path

### Beginner

Learn:

- `tofu init`, `plan`, `apply`, `destroy`;
- providers;
- resources/data sources;
- variables/outputs;
- state basics;
- direct dependencies.

### Intermediate

Learn:

- modules;
- `for_each`/`count`;
- provider aliases;
- remote backends;
- state locking;
- provider lock files;
- CI planning;
- migration from Terraform.

### Advanced

Learn:

- provider protocol compatibility;
- state recovery;
- state/plan encryption and key rollover;
- cross-state architecture;
- reusable-module compatibility;
- provider supply-chain security;
- Terraform/OpenTofu divergence management;
- disaster recovery;
- large-estate state partitioning.

## Relationships

### Terraform

`cloud/terraform` is the closest indexed alternative. Both systems share substantial language and provider ecosystem heritage, but OpenTofu and Terraform now differ in governance, licensing, registry infrastructure, feature roadmap, and potentially future compatibility behavior.

### Kubernetes

`cloud/kubernetes` is a common OpenTofu integration target. Use explicit ownership boundaries between periodic IaC reconciliation and continuous Kubernetes-controller reconciliation.

## Taxonomy

- Kind: `tool`
- Domains: `cloud`, `developer-tools`, `devops`
- Deployment: `cli`, `local`
- License: `MPL-2.0`
- Maturity: `deep-dive`

## Primary references

- OpenTofu: https://opentofu.org/
- Repository: https://github.com/opentofu/opentofu
- License: https://github.com/opentofu/opentofu/blob/main/LICENSE
- CLI provisioning workflow: https://opentofu.org/docs/cli/run/
- Providers: https://opentofu.org/docs/language/providers/
- Provider requirements: https://opentofu.org/docs/language/providers/requirements/
- Modules: https://opentofu.org/docs/language/modules/
- State: https://opentofu.org/docs/language/state/
- State storage/backends: https://opentofu.org/docs/language/state/backends/
- State locking: https://opentofu.org/docs/language/state/locking/
- State and plan encryption: https://opentofu.org/docs/language/state/encryption/
- Backend configuration: https://opentofu.org/docs/language/settings/backends/configuration/
- Dependency lock file: https://opentofu.org/docs/language/files/dependency-lock/
- v1.x compatibility promises: https://opentofu.org/docs/language/v1-compatibility-promises/
- Terraform migration: https://opentofu.org/docs/intro/migration/
- Language compatibility settings: https://opentofu.org/docs/language/settings/

## Verification

This deep-dive was reviewed on **2026-09-06** against the current OpenTofu documentation, canonical repository, and MPL-2.0 license text. OpenTofu releases, Terraform compatibility, provider ecosystem behavior, registry behavior, encryption methods/key providers, and migration paths are fast-moving areas and should be checked against current primary documentation before production decisions.

## Maintenance

Prioritize review when:

- OpenTofu changes its v1.x compatibility promises;
- provider protocol or registry behavior changes;
- state format or migration guarantees change;
- encryption methods/key providers change;
- Terraform/OpenTofu compatibility materially diverges;
- OpenTofu introduces new language constructs that reduce Terraform portability;
- licensing or governance changes materially.
