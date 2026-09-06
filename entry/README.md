# GitHub Actions

> GitHub-native workflow automation platform that turns repository events, reusable YAML workflows, permissions, runners, environments, actions, artifacts, caches, and identity tokens into CI/CD and repository automation jobs.

GitHub Actions is best understood as a **hosted workflow-control plane plus job runners that execute repository-selected code**. The control plane receives GitHub events, resolves a workflow revision, evaluates workflow/job metadata, applies permissions and environment gates, queues jobs, selects runners, and records logs/artifacts. The runner then executes steps that may include shell commands, JavaScript actions, container actions, or composite actions.

That split is the foundation for understanding both reliability and security:

```text
GitHub event
    |
    v
workflow selection + YAML evaluation
    |
    v
job graph / permissions / environment gates
    |
    v
runner queue + runner selection
    |
    v
runner process
    |
    +-- checkout repository code
    +-- execute actions
    +-- execute shell/process commands
    +-- access job token / allowed secrets / OIDC
    +-- create cache or artifacts
    |
    v
results / checks / deployments / artifacts
```

A workflow file is therefore not passive CI configuration. It is privileged code that chooses **when automation runs, which revision is trusted, what credentials are available, what third-party code executes, and where that code runs**.

## Product boundary

GitHub Actions includes several different things that should not be conflated:

- the GitHub-hosted workflow service;
- workflow YAML and expression semantics;
- GitHub-hosted runners;
- self-hosted runners;
- the open-source `actions/runner` application;
- first-party and third-party actions;
- reusable workflows;
- caches and artifacts;
- environments/deployment protection;
- `GITHUB_TOKEN` permissions;
- GitHub's OIDC identity provider.

The `actions/runner` repository is MIT-licensed. That license applies to the open-source runner software, **not to the entire GitHub Actions hosted service or GitHub platform**. OpenDevIndex keeps the existing `MIT` module license metadata because the canonical code repository indexed for this module is the runner repository; service terms remain a separate product boundary.

## Workflow files

Repository workflows normally live under:

```text
.github/workflows/*.yml
.github/workflows/*.yaml
```

A minimal workflow:

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<pinned-ref>
      - run: ./gradlew test
```

A workflow describes triggers and a graph of jobs. A job describes runner selection, permissions, optional environment/concurrency controls, and a sequence of steps.

## Workflow revision matters

A workflow event does not always execute the YAML from the same Git revision you intuitively expect.

Different triggers use different `GITHUB_REF`/`GITHUB_SHA` semantics. Security-sensitive events such as `pull_request_target` deliberately execute in the context of the base/default branch rather than the untrusted pull-request head.

Before granting credentials, know all three of these:

```text
which event triggered the run?
which workflow revision is executing?
which repository code revision is being checked out?
```

They are not necessarily the same revision.

## Events

Workflows can be triggered by many event classes, including:

- `push`;
- `pull_request`;
- `pull_request_target`;
- `merge_group`;
- `release`;
- `schedule`;
- `workflow_dispatch`;
- `repository_dispatch`;
- `workflow_call`;
- `workflow_run`;
- issue/discussion/review events;
- deployment and package events.

The event choice is a trust decision, not just scheduling syntax.

## `pull_request`

For normal pull-request CI, `pull_request` is usually the safer starting point because untrusted forked code is intentionally constrained.

Fork-originated pull-request workflows normally receive reduced token privileges and do not receive repository secrets by default.

This means a workflow may need two separate stages:

```text
untrusted PR validation
  -> no privileged secrets/write token

trusted post-merge or approved deployment
  -> narrowly scoped credentials
```

Trying to make one workflow do both often creates unnecessary privilege.

## `pull_request_target`

`pull_request_target` runs in the security context of the target/base repository and is useful for trusted metadata operations such as labeling or commenting on pull requests.

It is dangerous when combined with checkout or execution of untrusted pull-request code.

Unsafe mental model:

```text
pull_request_target
  + write token/secrets
  + checkout attacker PR head
  + execute build script
  = repository compromise path
```

GitHub's secure-use documentation explicitly warns that privileged events such as `pull_request_target` can expose write access, secrets, or privileged caches if they execute untrusted code.

If the workflow needs to build/test pull-request code, prefer `pull_request`. If it needs privileged metadata actions, keep those actions separated from untrusted execution.

## `workflow_run`

`workflow_run` can intentionally create a privilege boundary:

```text
unprivileged workflow
  -> build/test attacker-controlled code

workflow_run workflow
  -> privileged publishing/commenting/deployment step
```

But the second workflow must treat artifacts, caches, outputs, or other data created by the first workflow as **untrusted input**.

A privileged workflow that blindly executes an artifact produced by an untrusted workflow recreates the same trust-boundary failure through a different channel.

## Event payload is untrusted data

Fields under contexts such as `github.event` can contain attacker-controlled content:

- pull-request titles;
- branch names;
- issue bodies;
- commit messages;
- usernames;
- labels;
- external dispatch inputs.

Do not interpolate untrusted context directly into a shell program.

Risky:

```yaml
- run: echo "${{ github.event.pull_request.title }}"
```

The expression is substituted before the shell parses the script. A malicious title can become shell syntax.

Safer pattern:

```yaml
- name: Print PR title
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: printf '%s\n' "$PR_TITLE"
```

This moves the untrusted string into process data rather than source code. The exact escaping rules still depend on the interpreter.

## Expressions and contexts

GitHub Actions expressions use `${{ ... }}` and can read contexts such as:

- `github`;
- `env`;
- `vars`;
- `inputs`;
- `secrets`;
- `runner`;
- `job`;
- `steps`;
- `needs`;
- `strategy`;
- `matrix`.

Context availability differs by YAML field and evaluation phase. A value available inside a step may not be allowed in a top-level job key.

When a workflow expression unexpectedly resolves to empty or errors, check the **allowed contexts for that exact syntax field** rather than assuming every context exists everywhere.

## Job graph

Jobs run in parallel by default unless dependencies are declared with `needs`.

Example:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: ./test.sh

  build:
    runs-on: ubuntu-latest
    steps:
      - run: ./build.sh

  deploy:
    needs: [test, build]
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh
```

The graph is:

```text
test  -----\
           -> deploy
build -----/
```

Do not infer job ordering from YAML order.

## Step ordering

Steps inside one job execute sequentially on the same runner workspace unless control flow skips or fails them.

This means later steps can observe:

- files created earlier;
- environment changes persisted through supported mechanisms;
- repository modifications;
- credentials/config files written to disk;
- side effects from previous actions.

Treat a job as one shared execution trust domain.

## Outputs

A step can expose outputs to later steps, and a job can map outputs for downstream jobs through `needs`.

Outputs are useful for structured orchestration but are not an automatic secret transport.

Avoid using output channels to bypass secret-handling semantics or to expose attacker-controlled strings to privileged shells without validation.

## Matrix strategy

Matrices expand one job definition into multiple job variants.

Example:

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest]
    java: [17, 21]
```

Conceptually:

```text
ubuntu + 17
ubuntu + 21
windows + 17
windows + 21
```

Matrix configuration can also use `include`, `exclude`, `fail-fast`, and concurrency controls.

Matrices are useful for compatibility coverage, but Cartesian products can create large cost and queue amplification. Keep the dimensions aligned with actual supported combinations.

## `fail-fast` and experimental variants

For compatibility matrices, a useful design is to distinguish required configurations from allowed-to-fail experiments rather than hiding all failures.

A broken required platform should fail the workflow. An intentionally experimental version can use narrowly scoped `continue-on-error` behavior.

Avoid broad job-level `continue-on-error` because it can turn a real release blocker into a green status.

## Runner selection

`runs-on` determines which runner type can receive a job.

Runner selection can use:

- GitHub-hosted labels;
- self-hosted labels;
- runner groups;
- larger-runner labels/configuration where available.

A job's runner determines its operating system, installed software, network reachability, persistence characteristics, hardware, and trust boundary.

## GitHub-hosted runners

GitHub-hosted runners provide managed environments maintained by GitHub.

Benefits include:

- low operational burden;
- clean hosted environments for jobs;
- automatic capacity management;
- standard images with common developer tooling.

Trade-offs include:

- hosted image changes over time;
- limited control over base image details compared with self-hosting;
- network access requirements for private systems;
- queue/cost constraints depending on plan and runner class.

For reproducible builds, do not depend on a mutable runner label alone for every tool version. Pin critical language/toolchain dependencies in the build itself.

## Self-hosted runners

Self-hosted runners execute jobs on infrastructure you operate.

They can provide:

- custom hardware;
- private-network access;
- special operating systems;
- local caches/toolchains;
- controlled images;
- specialized accelerators.

They also move major security and reliability responsibilities to you.

A self-hosted runner can hold:

- repository checkout data;
- process state;
- Docker state;
- network credentials;
- filesystem credentials;
- cloud metadata access;
- access to internal services;
- previous-job residue if the machine is persistent.

## Public repositories and self-hosted runners

GitHub warns against exposing self-hosted runners to untrusted public-repository pull requests. A fork can potentially submit code that the runner executes.

The threat is broader than stealing a job token. Malicious code can attack:

- the host operating system;
- neighboring workloads;
- cloud instance metadata;
- internal networks;
- persistent credentials;
- runner registration/configuration;
- later jobs on the same machine.

Runner access policy is therefore part of repository security.

## Ephemeral self-hosted runners

For autoscaling, GitHub recommends ephemeral self-hosted runners rather than persistent autoscaled runners.

An ephemeral runner accepts one job and de-registers, allowing the infrastructure automation to destroy or wipe it afterward.

This reduces cross-job persistence and helps contain compromise, but it does not make the current job safe from overly broad network or cloud privileges.

Ephemeral runner design still needs:

- minimal instance identity permissions;
- network segmentation;
- external log retention;
- image patching;
- controlled registration tokens;
- cleanup verification.

## Runner logs and observability

Ephemeral runner fleets need logs forwarded outside the runner because the runner may disappear immediately after the job.

Monitor at least:

- runner registration failures;
- queue time;
- job pickup latency;
- runner image/version;
- job completion/failure;
- scaling events;
- runner update failures;
- orphaned infrastructure.

## Runner groups

Runner groups create access boundaries around self-hosted or larger runner capacity.

Use them to restrict which repositories can schedule jobs onto sensitive infrastructure.

Example segmentation:

```text
public/untrusted CI -> GitHub-hosted runners
internal builds      -> isolated build runner group
production deploy    -> protected deploy runner group
```

Do not expose a production-network runner group to every repository merely for convenience.

## Actions Runner Controller (ARC)

Actions Runner Controller is GitHub's recommended Kubernetes-based implementation for autoscaling self-hosted runner scale sets.

ARC is useful when Kubernetes is already an appropriate execution substrate and you need elastic runner capacity.

Its security model still depends on:

- Kubernetes namespace/cluster isolation;
- service-account permissions;
- pod/container isolation;
- runner group access;
- network policies;
- ephemeral job lifecycle;
- secret/registration-token handling.

Kubernetes scheduling does not automatically make untrusted CI safe.

## Actions

A workflow step can execute an action using `uses:`.

Common action implementation types include:

- JavaScript actions;
- Docker container actions;
- composite actions.

An action can read files, execute processes, use the network, and consume any token/secrets exposed to the job. Treat third-party actions as dependencies with code-execution privilege.

## Pinning actions

For security-sensitive workflows, pin third-party actions to a full commit SHA.

Example:

```yaml
- uses: owner/action@0123456789abcdef0123456789abcdef01234567
```

A tag such as `@v4` can be convenient but is a mutable repository reference. A full commit SHA binds execution to reviewed source content.

Dependency-update automation can still propose SHA upgrades while preserving reviewability.

## Action ownership and takeover risk

Before adding a third-party action, evaluate:

- repository owner;
- maintainer activity;
- release provenance;
- permissions requested;
- network behavior;
- dependencies;
- whether the repository or tag could be transferred/retargeted;
- whether the action is needed at all.

An action running in a deploy job can be as privileged as the deployment script itself.

## Composite actions versus reusable workflows

Composite actions package **steps** and run inside a caller job.

Reusable workflows package **jobs** and can choose runners, permissions, matrices, environments, and multiple stages.

Use a composite action for a reusable step-level operation:

```text
setup tool -> authenticate helper -> run command
```

Use a reusable workflow for an organization-level pipeline contract:

```text
build job -> scan job -> attest job -> deploy job
```

## Reusable workflows

Reusable workflows are called with `workflow_call`.

They support defined inputs, outputs, and secrets and can centralize organization policy.

Example caller:

```yaml
jobs:
  build:
    uses: org/ci/.github/workflows/android.yml@<pinned-sha>
    with:
      java-version: 21
```

For cross-repository reusable workflows, a commit SHA is the safest reference for stability and security.

## Reusable workflow permissions

A called workflow does not provide a magic privilege-escalation route. Nested reusable workflows can keep or reduce the caller's `GITHUB_TOKEN` permissions, not elevate beyond the caller's permission ceiling.

This encourages a useful design:

```text
caller grants minimum permissions
    |
    v
reusable workflow operates within that ceiling
```

Do not grant broad caller permissions merely because one nested step might need them. Split privileged work into an isolated job/workflow when practical.

## `GITHUB_TOKEN`

GitHub provides a repository-scoped automation token to workflow jobs.

Its effective permissions depend on:

- repository/organization/enterprise defaults;
- the event that triggered the workflow;
- top-level `permissions`;
- job-level `permissions`;
- fork/Dependabot restrictions;
- reusable-workflow permission propagation.

The safe rule is to declare explicit minimum permissions.

Example read-only CI:

```yaml
permissions:
  contents: read
```

Example release job:

```yaml
permissions:
  contents: write
```

Do not use `write-all` as a default convenience setting.

## Job-level least privilege

If only one job needs elevated permission, grant it only there.

```yaml
permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: ./test.sh

  release:
    needs: test
    permissions:
      contents: write
    runs-on: ubuntu-latest
    steps:
      - run: ./release.sh
```

This keeps untrusted build tooling away from the write token whenever the workflow architecture permits.

## Secrets

Secrets can exist at repository, organization, or environment scope depending on configuration and plan.

Do not assume every secret is automatically available to every run.

Availability depends on event trust, repository settings, environment gates, and reusable-workflow secret passing.

Secrets should be:

- narrowly scoped;
- rotated;
- non-printable by default;
- unavailable to untrusted fork execution;
- avoided entirely for cloud authentication when OIDC can replace them.

## Secret masking is not a security boundary

GitHub masks recognized secret values in logs, but masking is a defense-in-depth feature, not authorization.

A malicious process that receives a secret can transform, split, encode, upload, or otherwise exfiltrate it.

The primary control is **do not expose the secret to code that does not need it**.

## OpenID Connect

GitHub's OIDC provider lets a workflow exchange a GitHub-signed identity token for a short-lived credential at an external cloud or service provider.

Flow:

```text
workflow job
   |
   | request OIDC token
   v
GitHub OIDC issuer
   |
   | signed claims: repository/ref/environment/workflow/etc.
   v
cloud identity provider
   |
   | validate trust policy
   v
short-lived cloud credential
```

This can eliminate long-lived cloud credentials stored as GitHub secrets.

## `id-token: write`

A job needs:

```yaml
permissions:
  id-token: write
  contents: read
```

to request an OIDC token.

`id-token: write` does **not** itself grant write permission to cloud infrastructure. It allows the workflow to request an identity token. The external provider's trust policy and role permissions decide what that identity can obtain.

## OIDC trust conditions

Do not trust every token issued for an entire GitHub organization unless that is truly intended.

Constrain cloud trust using claims such as the relevant:

- repository;
- owner;
- branch/ref;
- environment;
- workflow identity;
- audience;
- organization/repository policy metadata where supported.

The cloud trust policy is the real authorization boundary.

A workflow-level condition alone is not enough if a malicious workflow in the same repository can request the same cloud role.

## Environments

GitHub Actions environments represent deployment targets such as:

- `development`;
- `staging`;
- `production`.

An environment can provide:

- deployment history;
- approval/reviewer gates;
- branch/tag deployment restrictions;
- custom protection rules;
- environment-scoped secrets and variables.

Protection rules are evaluated before the protected job is sent to a runner, and environment secrets become available only after the protection requirements pass.

## Environment gate as privilege boundary

A useful production design is:

```text
build/test job
  -> no production credentials

production deploy job
  -> environment: production
  -> approval/protection rules
  -> OIDC role limited to production deployment
```

Do not place production credentials in an earlier build job and rely on a later manual approval to make the workflow safe. The privilege should appear only after the gate.

## Concurrency

`concurrency` prevents conflicting runs or jobs from executing simultaneously within a concurrency group.

Deployment example:

```yaml
concurrency:
  group: production
  cancel-in-progress: false
```

For branch CI:

```yaml
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
```

Use concurrency to protect resources that cannot tolerate overlapping automation.

Do not mistake concurrency for a globally ordered queue. GitHub documents that ordering within a concurrency group is not guaranteed in the general case.

## Canceling stale CI

For pull-request CI, canceling an obsolete run after a new commit arrives can save time and compute.

For deployments or migrations, automatic cancellation can be dangerous if the running job has already mutated external state.

Choose `cancel-in-progress` based on whether the operation is safely interruptible.

## Caches

Caches are intended to speed up dependency/build reuse across jobs and workflow runs.

They are **not trusted artifact storage**.

Cache keys should reflect inputs that affect cache correctness, such as dependency lockfiles.

Example concept:

```text
OS + toolchain + hash(lockfile)
```

Do not place secrets in caches.

## Cache poisoning

A workflow with access to a privileged cache can be attacked if untrusted code can populate or influence that cache and a later privileged job consumes it unsafely.

This is particularly important when combining untrusted pull-request workflows with privileged `workflow_run` or `pull_request_target` logic.

Privileged workflows should not blindly execute code retrieved from attacker-influenced caches.

## Artifacts

Artifacts persist files produced by workflow runs for later download or consumption.

Typical uses:

- test reports;
- binaries;
- coverage reports;
- build logs;
- packaged releases;
- provenance/attestation inputs.

Artifacts have a different lifecycle and trust purpose from caches.

A file being a GitHub Actions artifact does not make it trusted. The producing workflow's trust level determines how downstream consumers should treat it.

## Untrusted artifact boundary

If an unprivileged PR job uploads a binary and a privileged workflow downloads it, the privileged workflow must assume the binary is attacker-controlled.

Safe privileged patterns include:

- verify metadata/digests/provenance before privileged use;
- rebuild from a trusted commit after approval;
- treat artifact contents as data, not executable code;
- isolate processing with no secrets/write token.

## Service containers

Jobs can define service containers for integration-test dependencies such as databases or caches on supported runner environments.

They are useful for test isolation but expand the local attack surface and startup complexity.

Pin service image versions/digests where reproducibility and supply-chain integrity matter.

## Container jobs

A job can run steps inside a specified container on a compatible runner.

A container boundary can improve dependency consistency but is not automatically a security sandbox against a hostile runner host. The runner controls the container runtime and mounts required for job execution.

## Shell behavior

The shell used by `run:` depends on runner OS and workflow configuration.

Cross-platform workflows should explicitly account for:

- Bash/sh differences;
- PowerShell semantics;
- path separators;
- quoting;
- executable bits;
- line endings;
- environment-variable syntax.

Avoid giant shell programs embedded in YAML. Put complex logic into versioned, testable scripts where practical.

## Working directory and checkout

The runner starts the job workspace, but repository content is not automatically available until a checkout action or equivalent fetch step provides it.

Be explicit about:

- which repository;
- which ref;
- fetch depth;
- submodules;
- credentials persisted by checkout;
- whether untrusted code is being checked out in a privileged job.

Checkout configuration is a security decision in privileged workflows.

## Credentials persisted by checkout

Repository checkout tooling can configure credentials so later Git commands can authenticate.

If a job does not need authenticated Git writes after checkout, avoid leaving unnecessary credentials available to later untrusted build steps.

This is another reason to separate build and release jobs.

## Branch protection and required checks

GitHub Actions often provides required status checks for protected branches or rulesets.

A robust required check should be:

- deterministic enough to reproduce;
- named/stable enough for branch policy;
- not silently skipped by path/event mistakes;
- not allowed to pass because of broad `continue-on-error`;
- protected from untrusted workflows spoofing an equivalent status context where repository rules permit distinctions.

When restructuring workflows, verify branch/ruleset requirements still reference the intended checks.

## Merge queue

Repositories using merge queue can use the `merge_group` event so required checks run against the merge-group revision.

If a required workflow listens only to `pull_request`, merge-queue behavior may not match expectations.

CI event architecture should account for how code actually reaches the protected branch.

## Scheduled workflows

`schedule` is useful for:

- nightly tests;
- dependency/source checks;
- periodic maintenance;
- stale-resource cleanup.

Scheduled execution has no human commit actively initiating the run, so operations should still use least privilege and idempotent safety controls.

Do not use scheduled cleanup code with broad credentials and weak resource selectors.

## Manual dispatch

`workflow_dispatch` can expose typed inputs and supports operator-triggered automation.

Inputs are user-controlled data. Validate them before using them as:

- shell fragments;
- cloud resource names;
- repository refs;
- environment selectors;
- deployment parameters.

Use environment gates for high-risk manual production operations instead of assuming only trusted humans can click the button.

## Repository dispatch

`repository_dispatch` supports external event-driven automation.

Treat client payload fields as untrusted input unless the calling integration and payload are authenticated and validated.

The workflow's repository token/secret/OIDC privileges can be much stronger than the system sending the event.

## Timeouts

Jobs and individual steps can define timeouts.

Timeouts protect against:

- hung test processes;
- stalled network calls;
- deadlocked deployment scripts;
- runaway compute cost;
- jobs occupying scarce self-hosted capacity indefinitely.

A timeout is not rollback. External mutations completed before cancellation remain completed.

## Retry design

GitHub Actions does not make arbitrary shell steps transactional.

If a deployment workflow is manually rerun, every step should have known retry behavior:

```text
safe to repeat
safe only after inspection
or
must not be repeated automatically
```

Idempotency belongs to the external operation/tool as much as to the workflow engine.

## Deployment pattern

A hardened deployment flow can look like:

```text
pull_request
  -> unprivileged build/test
  -> no deploy secrets

merge to protected main
  -> build trusted commit
  -> scan/test
  -> produce immutable artifact
  -> production environment gate
  -> OIDC short-lived credential
  -> deploy exact artifact
  -> verify health
  -> record deployment evidence
```

This keeps untrusted PR code and production credentials in different jobs/events.

## Build once, deploy exact artifact

If your release model requires strong provenance, avoid rebuilding materially different binaries independently in every environment.

A common model is:

```text
trusted build -> digest/artifact
staging       -> deploy digest X
production    -> deploy same digest X
```

The workflow then promotes identity rather than reconstructing output from a mutable dependency graph.

## Supply-chain integrity

CI/CD controls the software supply chain, so consider:

- pinned actions;
- pinned package/dependency lockfiles;
- trusted runner images;
- immutable build inputs;
- artifact digests;
- attestations/provenance;
- protected release environments;
- OIDC federation;
- least-privilege package/repository permissions.

The workflow itself should be treated as release infrastructure code.

## Artifact attestations

GitHub Actions supports generating artifact attestations through workflow permissions and supported tooling.

Attestations can bind an artifact to provenance information, but their value depends on protecting the workflow/runner identity that is allowed to produce the attestation.

A compromised privileged runner that can build and attest malicious output has not been made safe merely because an attestation exists.

## Dependency update automation

Actions pinned to commit SHAs can become stale.

Use dependency automation to propose reviewed updates rather than falling back to mutable tags solely for convenience.

A good update PR should make visible:

- old SHA;
- new SHA;
- upstream release/tag association;
- permission/behavior changes;
- release notes when relevant.

## Secrets versus OIDC

Prefer OIDC for supported cloud/service authentication because it can remove long-lived cloud credentials from GitHub secret storage.

Keep GitHub secrets for credentials that cannot yet use federated identity, and limit their scope and lifetime.

Do not put a permanent cloud administrator key into a repository secret simply because it makes deployment YAML shorter.

## Self-hosted runner cloud identity

A self-hosted cloud VM may have ambient instance identity even when the workflow does not receive a GitHub secret.

Untrusted code can potentially call the cloud metadata/identity endpoint and inherit that privilege.

Therefore self-hosted runner least privilege must cover **host identity** as well as workflow-provided credentials.

## Network trust

A runner with private network access may be able to reach systems far beyond the resources needed by the current job.

Segment runner networks by trust level and purpose.

Example:

```text
CI runner -> source/package/test services
release runner -> artifact registry only
production deploy runner -> narrowly scoped deployment endpoints
```

Do not make “runner is inside VPN” equivalent to unrestricted production network trust.

## Persistent runner contamination

Persistent self-hosted runners can retain:

- malicious binaries in PATH;
- altered Git config;
- poisoned build caches;
- Docker images/volumes;
- modified SDKs;
- background processes;
- credentials/files;
- filesystem permissions.

If persistence is required, implement rigorous cleanup and isolation. For untrusted builds, ephemeral runners are generally the safer architecture.

## Workflow logs

Logs can leak:

- environment data;
- paths/usernames;
- URLs;
- partial secrets;
- cloud account identifiers;
- deployment topology;
- debug output from third-party actions.

Avoid enabling shell tracing or verbose credential-provider logs in production workflows unless the resulting logs are protected and reviewed.

## Debug logging

Runner/workflow debug options can dramatically increase output detail.

Use them temporarily and assume they may reveal values that normal output omits. Rotate credentials if a debug run exposed them.

## Performance model

Workflow duration includes more than command runtime:

```text
trigger latency
+ queue time
+ runner provisioning
+ checkout/download
+ dependency restore/install
+ build/test
+ artifact upload
+ environment approval wait
+ deployment
```

Optimize the dominant term rather than blindly adding caching.

## Cache effectiveness

A cache is useful when:

```text
restore + validation cost < recomputation/download cost
```

Caches can make workflows slower when keys churn constantly, payloads are huge, or compression/network overhead exceeds the saved work.

Measure hit rate and restore/save duration.

## Job granularity

Splitting everything into separate jobs can increase parallelism and isolation but adds:

- runner startup cost;
- artifact handoff cost;
- repeated checkout/setup;
- more permission boundaries to maintain.

One giant job reduces setup overhead but combines privileges and reduces parallelism.

Choose job boundaries around:

- trust/permissions;
- runner type;
- parallelizable work;
- reusable outputs;
- failure domains.

## CI concurrency economics

A large matrix plus multiple pushes can create hundreds of redundant jobs.

Use:

- branch-scoped concurrency cancellation for stale CI;
- matrix `max-parallel` where downstream systems have limits;
- path filters carefully;
- targeted smoke/full test tiers;
- caching where safe and effective.

Avoid optimizing cost by silently removing meaningful coverage.

## Failure modes

### Workflow never triggers

Check:

- workflow exists on the required branch for that event;
- event/activity type;
- branch/tag/path filters;
- YAML syntax;
- default-branch requirements for events such as `workflow_run`;
- organization/repository Actions policy.

### Job remains queued

Check:

- `runs-on` label/group match;
- self-hosted runner online status;
- runner group repository access;
- runner capacity;
- concurrency group;
- environment gate status.

### Works on GitHub-hosted, fails self-hosted

Possible causes:

- stale workspace;
- missing tool;
- permissions;
- shell/path difference;
- network/DNS/proxy;
- Docker availability;
- runner version;
- persistent contamination.

### Works on self-hosted, fails GitHub-hosted

Possible causes:

- undeclared local dependency;
- private-network assumption;
- credentials from ambient host state;
- cached global toolchain;
- filesystem/path assumption.

A clean hosted runner failure often reveals an undeclared dependency.

### Secret unexpectedly unavailable

Check:

- fork/Dependabot event restrictions;
- repository/organization secret policy;
- environment gate and environment scope;
- reusable-workflow secret passing;
- secret name and case;
- whether the workflow is intentionally unprivileged.

Do not “fix” an untrusted PR by granting secrets without redesigning the trust boundary.

### Permission denied from GitHub API

Check effective `GITHUB_TOKEN` permissions at the job level.

Adding a write permission is not automatically correct; first verify whether the job should be allowed to perform that operation.

### Deployment runs twice

Check:

- overlapping `push` and `workflow_run` triggers;
- retries/reruns;
- missing concurrency group;
- external deployment tool idempotency;
- duplicate reusable workflow invocation.

### Deployment cancelled mid-change

`cancel-in-progress` or manual cancellation can stop the runner while the external platform is partially updated.

Recovery depends on the deployment system. Design interruptible CI differently from stateful production changes.

### Action update breaks workflow

If using mutable tags, the underlying action code can change without a workflow-file diff.

Pin by SHA and review dependency updates.

### Cache causes strange privileged behavior

Treat possible cache poisoning as a security incident when the cache crossed an untrusted-to-privileged boundary. Invalidate the cache and inspect privileged credentials/artifacts.

### Runner compromise

Response should include:

- stop accepting jobs;
- revoke runner registration/access;
- rotate credentials exposed to the host;
- revoke cloud/session credentials where applicable;
- rebuild from a clean image;
- inspect adjacent network/resource access;
- invalidate caches/artifacts if integrity is uncertain;
- preserve logs/forensics.

## Debugging workflow

When a workflow behaves unexpectedly:

1. identify event and activity type;
2. identify workflow commit/revision;
3. identify checked-out code SHA;
4. inspect top-level and job-level permissions;
5. inspect environment gate/secret scope;
6. inspect runner type, labels, group, and image/version;
7. expand matrix values;
8. inspect `needs` graph and job conditions;
9. inspect expression/context values without printing secrets;
10. verify action/reusable-workflow refs;
11. distinguish queue time from execution time;
12. inspect artifact/cache boundaries;
13. reproduce the failing command locally/containerized where meaningful;
14. enable debug logging only when necessary.

## Workflow review checklist

For every new or materially changed workflow, review:

- trigger trust level;
- checked-out ref;
- token permissions;
- secrets exposed;
- OIDC claims/trust policy;
- runner trust level;
- third-party action SHAs;
- shell interpolation of untrusted contexts;
- reusable workflow permissions;
- environment protections;
- concurrency/cancellation semantics;
- cache/artifact trust direction;
- deployment idempotency and recovery.

## Security anti-patterns

Avoid:

- `pull_request_target` plus checkout/execution of PR head code;
- privileged `workflow_run` that blindly executes untrusted artifacts;
- `permissions: write-all` as a default;
- long-lived cloud administrator secrets when OIDC is available;
- third-party actions referenced only by mutable branches/tags in privileged jobs;
- public fork code on persistent self-hosted runners;
- production-network access on general-purpose CI runners;
- untrusted event fields interpolated directly into shell source;
- cache content treated as trusted executable input;
- production secrets available before an environment approval gate;
- one job combining untrusted build steps and privileged release steps;
- silent `continue-on-error` on security/release checks;
- auto-canceling non-interruptible production deployments;
- relying on secret masking as authorization.

## Reliability anti-patterns

Avoid:

- workflows depending on undocumented hosted-runner global tools;
- self-hosted runners with manual snowflake configuration;
- matrices that grow combinatorially without value;
- ambiguous mutable action refs;
- duplicate workflows that implement release policy differently;
- deployments without concurrency/idempotency controls;
- privileged workflows coupled to attacker-controlled caches/artifacts;
- no timeout on network-dependent or external deployment steps.

## Organization-scale design

At organization scale, centralize the parts that should be policy:

- reusable build/test workflows;
- approved deployment workflows;
- OIDC trust conventions;
- runner groups;
- action allow/deny policy;
- SHA-pinning/dependency update policy;
- environment naming/protection;
- artifact/attestation policy.

Keep application-specific build logic close to the application repository while making privilege/security rules hard to accidentally bypass.

## Reusable workflow as platform API

A reusable workflow is effectively an internal platform API.

Treat its inputs and outputs as a versioned contract:

```text
inputs:
  artifact-name
  environment
  java-version
outputs:
  digest
  deployment-url
```

Breaking a reusable workflow can affect many repositories at once. Pin callers to reviewed revisions and publish migration guidance for contract changes.

## Relationship to Git

`tool/git` provides the distributed version-control object/history model underneath repository revisions. GitHub Actions consumes repository refs, commits, diffs, tags, and collaboration events to decide what automation to run.

Understanding Git SHAs is particularly useful when pinning actions, debugging checkout depth/ref behavior, and tying releases to immutable commits.

## Relationship to Kubernetes

`cloud/kubernetes` is both a deployment target and a runner substrate. Workflows can deploy Kubernetes resources, while Actions Runner Controller can manage autoscaling self-hosted runner scale sets on Kubernetes.

The two roles have different trust boundaries: a cluster used to **run CI** should not automatically inherit production-cluster privileges simply because the same organization uses Kubernetes for both.

## Taxonomy

- Kind: `tool`
- Domains: `ci-cd`, `devops`
- Deployment: `saas`, `self-hosted`
- License metadata: `MIT` for the indexed open-source runner repository; the hosted GitHub Actions service is a separate product boundary
- Maturity: `deep-dive`

## Primary references

- GitHub Actions documentation: https://docs.github.com/actions
- Workflow syntax: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- Events: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- Contexts: https://docs.github.com/en/actions/reference/workflows-and-actions/contexts
- Expressions: https://docs.github.com/en/actions/reference/workflows-and-actions/expressions
- Secure use: https://docs.github.com/en/actions/reference/security/secure-use
- `GITHUB_TOKEN`: https://docs.github.com/en/actions/how-tos/security-for-github-actions/security-guides/automatic-token-authentication
- OIDC concept: https://docs.github.com/en/actions/concepts/security/openid-connect
- OIDC reference: https://docs.github.com/en/actions/reference/security/oidc
- Deployment environments: https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments
- Reusable workflow concepts: https://docs.github.com/en/actions/concepts/workflows-and-actions/reusing-workflow-configurations
- Self-hosted runners: https://docs.github.com/en/actions/concepts/runners/self-hosted-runners
- Self-hosted runner reference: https://docs.github.com/en/actions/reference/runners/self-hosted-runners
- Runner groups: https://docs.github.com/en/actions/concepts/runners/runner-groups
- Runner source: https://github.com/actions/runner
- Runner MIT license: https://github.com/actions/runner/blob/main/LICENSE

## Verification

This deep-dive was reviewed on **2026-09-06** against current GitHub Actions documentation and the canonical `actions/runner` repository. GitHub Actions evolves continuously; event semantics, workflow syntax, permissions, runner images, concurrency behavior, reusable-workflow limits, security guidance, OIDC claims, and plan-specific features should be rechecked against current GitHub documentation before security-sensitive architecture decisions.

## Maintenance

Prioritize review when:

- GitHub changes token permission defaults;
- `pull_request_target` or `workflow_run` security guidance changes;
- action/reusable-workflow reference or pinning guidance changes;
- hosted runner lifecycle/images materially change;
- self-hosted runner or ARC autoscaling guidance changes;
- OIDC claims/trust customization changes;
- environment protection or concurrency semantics change;
- artifact/cache trust or retention behavior changes;
- the `actions/runner` license or architecture changes.
