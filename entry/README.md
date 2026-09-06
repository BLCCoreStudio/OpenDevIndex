# Ansible

> Agentless automation system whose control node resolves inventory, variables, playbooks, plugins, and collections into ordered tasks executed across managed nodes for configuration management, deployment, orchestration, and repeatable operations.

Ansible is easiest to reason about as a **control-node execution engine plus a large plugin/content ecosystem**. A run starts on the control node, resolves target hosts from inventory, combines variables from multiple scopes, expands plays and roles into tasks, selects plugins and modules, schedules work across hosts, connects to each managed node, executes the required operation, and gathers structured results.

The word “agentless” is useful but incomplete. Ansible normally does not require a persistent Ansible daemon on managed machines. It still needs a usable connection mechanism and whatever runtime or platform facilities the selected module requires. On Unix-like systems, SSH and a compatible remote Python environment are common; network devices, Windows systems, local execution, containers, and APIs can use other connection or execution paths.

## Mental model

A typical run can be modeled as:

```text
playbook / ad-hoc command
          |
          v
inventory sources -> hosts + groups
          |
          v
variables + facts + configuration
          |
          v
roles / collections / plugins
          |
          v
play -> ordered tasks
          |
          v
strategy plugin + forks + batches
          |
          v
action plugin on control node
          |
          +---- control-node-only work
          |
          v
connection / shell / become plugins
          |
          v
module or command on managed node
          |
          v
structured result: changed / failed / data
          |
          v
handlers / next task / error policy
```

This model explains several production behaviors:

- YAML order defines task order within a play, but host concurrency is controlled separately.
- A task can perform work entirely on the control node, entirely through a remote API, or on a managed node depending on its action/module/plugin implementation.
- “Idempotent Ansible” is not a property of YAML itself; it depends on module semantics, task inputs, external systems, and how `changed` is determined.
- Inventory is not merely a host list. It also contributes grouping, connection information, and variables.
- Variable precedence is part of the runtime semantics and can materially change what a task does.
- Collections and plugins are executable dependencies and therefore part of the automation supply chain.

## `ansible-core` versus the `ansible` package

Ansible is distributed in two important forms:

### `ansible-core`

The minimal language/runtime package. It includes:

- the CLI tools;
- the playbook engine;
- inventory/runtime machinery;
- builtin modules and plugins under `ansible.builtin`;
- the plugin and collection loading system.

The canonical `ansible/ansible` repository is the source repository for `ansible-core`.

### `ansible`

The larger community package. It combines `ansible-core` with a curated set of community Collections that provide many additional modules and plugins.

The two have separate versioning and maintenance models. A playbook that depends on a collection shipped by the broad `ansible` package may not work on a minimal `ansible-core` installation unless that collection is installed explicitly.

For reproducible automation, document which distribution and collection versions are required instead of treating “Ansible version” as a single sufficient dependency identifier.

## Control node

The control node is where Ansible itself runs.

It owns activities such as:

- parsing configuration and playbooks;
- loading inventory;
- resolving variables;
- Jinja templating;
- loading collections and plugins;
- scheduling hosts/tasks;
- invoking connection plugins;
- running action plugins;
- evaluating lookups;
- collecting and formatting results.

This makes the control node a high-trust component. It commonly has:

- SSH keys or other remote credentials;
- privilege-escalation credentials;
- cloud/API credentials;
- access to vault passwords or secret managers;
- access to inventory and sensitive host metadata.

A compromised control node or malicious collection can therefore have broad infrastructure impact.

## Managed nodes

Managed nodes are the systems or endpoints targeted by a run.

Depending on the module and connection type, a target may be:

- a Linux/Unix host over SSH;
- a Windows host through a Windows-capable connection plugin;
- a network appliance;
- localhost;
- a cloud or SaaS API represented through provider-specific modules;
- another system reached indirectly through delegation.

Do not assume every module executes on the inventory host. Action plugins, delegated tasks, lookups, and API-oriented modules can shift the execution boundary.

## Inventory

Inventory maps logical host identities into groups, variables, and connection information.

A small YAML inventory may look like:

```yaml
all:
  children:
    web:
      hosts:
        web-01:
          ansible_host: 10.10.0.11
        web-02:
          ansible_host: 10.10.0.12
    database:
      hosts:
        db-01:
          ansible_host: 10.10.0.21
```

Inventory hostnames are logical Ansible identities. `ansible_host` can point to a different network address.

### Groups

A host can belong to multiple groups. Groups support:

- targeting;
- variable assignment;
- functional organization;
- environment organization;
- dynamic grouping from provider metadata.

Useful group dimensions include function, environment, region, operating system, or service role. Avoid inventing one giant hierarchy when hosts naturally belong to several independent dimensions.

## Static and dynamic inventory

Static inventory works well for small or stable estates.

Dynamic inventory is better when host membership comes from systems such as:

- cloud APIs;
- virtualization platforms;
- CMDBs;
- directory services;
- Kubernetes or infrastructure APIs;
- other authoritative discovery sources.

Modern Ansible documentation recommends **inventory plugins** over legacy executable inventory scripts where suitable.

A dynamic inventory source can create hosts and groups from provider metadata, often with keyed groups or composed variables.

### Inventory is a trust boundary

Inventory data can influence:

- connection destination;
- remote user;
- interpreter selection;
- privilege escalation;
- plugin options;
- variables consumed by templates and commands.

Treat write access to production inventory as privileged automation access.

## Separate environment inventories

Keeping production and non-production in separate inventories or inventory roots can reduce accidental targeting and secret exposure.

A command such as:

```bash
ansible-playbook -i inventories/prod site.yml
```

makes environment selection visible.

Do not rely only on naming conventions like `prod-*` inside one enormous inventory if the resulting blast radius is unacceptable.

## Host patterns and targeting

A play selects hosts using `hosts:` patterns, and CLI commands can further constrain execution with options such as `--limit`.

Example:

```yaml
- name: Configure web tier
  hosts: web
  tasks:
    - name: Ensure Nginx is present
      ansible.builtin.package:
        name: nginx
        state: present
```

Operational safety depends on verifying what a pattern expands to **before** making a destructive change.

Useful inventory inspection commands include:

```bash
ansible-inventory -i inventory.yml --graph
ansible-inventory -i inventory.yml --list
ansible all -i inventory.yml --list-hosts
```

## Variables

Variables can come from many layers, including:

- role defaults;
- inventory group variables;
- inventory host variables;
- `group_vars` and `host_vars`;
- play variables;
- role variables;
- facts;
- registered task results;
- `set_fact`;
- included variable files;
- command-line extra variables.

Ansible applies precedence rules when the same variable name appears in several places.

The most important practical rule is: **do not guess which value wins**. When a value matters to production behavior, know its source and precedence.

## Variable precedence and debugging

High-precedence overrides are convenient but can hide architecture problems.

For example, repeatedly fixing a bad role default through `-e` extra variables can make local runs succeed while automation behaves differently.

When a variable is surprising:

1. identify the host actually executing the task;
2. inspect inventory membership;
3. inspect `host_vars` and `group_vars`;
4. inspect role defaults and vars;
5. inspect play/task vars;
6. inspect extra vars and CI inputs;
7. inspect facts and registered values;
8. account for delegation context.

Keep important configuration ownership clear rather than relying on a long precedence chain as an implicit override system.

## Facts

Facts are host information gathered or provided to Ansible.

They can include information such as:

- operating system;
- network interfaces;
- addresses;
- architecture;
- Python/interpreter information;
- hardware details.

Facts are exposed through host variables after they are gathered or loaded from a fact cache.

Fact gathering is useful but can be expensive across very large fleets. Disable or narrow it where playbooks do not need it, or use an appropriate cache when repeated discovery dominates runtime.

## Magic variables

Ansible exposes runtime context through reserved variables such as:

- `hostvars`;
- `groups`;
- `group_names`;
- `inventory_hostname`;
- `ansible_play_hosts`;
- `ansible_play_batch`;
- `playbook_dir`;
- `ansible_check_mode`.

Do not redefine reserved magic-variable names.

`hostvars` can read information for another host, but facts for that host must already be available through gathering or caching when referenced.

## Playbooks

A playbook is a YAML list of plays.

A play maps a host pattern to an ordered task sequence and can define variables, roles, execution controls, handlers, and other behavior.

Conceptually:

```text
playbook
  -> play
      -> hosts
      -> vars
      -> pre_tasks
      -> roles
      -> tasks
      -> post_tasks
      -> handlers
```

A task normally references a module or action using a Fully Qualified Collection Name.

Example:

```yaml
- name: Configure application hosts
  hosts: app
  become: true
  tasks:
    - name: Install application package
      ansible.builtin.package:
        name: example-app
        state: present
```

## Modules

Modules implement operations such as:

- package management;
- file ownership and content;
- users/groups;
- service management;
- cloud API resources;
- database operations;
- network device configuration;
- Kubernetes resources;
- commands and scripts.

Well-designed modules return structured results including fields such as whether the task changed something or failed.

Prefer a purpose-built module over shell commands when the module models the desired state correctly.

## Module execution architecture

A task that looks like a module invocation may involve both control-node and managed-node work.

Ansible's module execution path commonly includes:

1. task execution on the control node;
2. an action plugin;
3. connection/shell/become plugins;
4. transfer or assembly of module code/arguments when required;
5. module execution on the target;
6. structured result returned to the control node;
7. callback/output processing.

Some action plugins perform all work on the control node. Others prepare data locally and then call a remote module.

This distinction matters for security reviews because templating, lookups, local files, and credentials may be accessed before anything reaches the managed node.

## Action plugins

Action plugins run on the control node and can augment or replace normal module execution.

They can:

- preprocess arguments;
- render templates;
- transfer files;
- manage temporary files;
- choose remote execution behavior;
- implement operations that need no remote module.

A collection adding an action plugin is adding executable control-node code. Review it accordingly.

## Connection plugins

Connection plugins determine how Ansible communicates with a target.

Common examples include:

- native SSH;
- Paramiko SSH;
- local execution;
- platform-specific remote protocols.

A host uses one connection plugin at a time for a task context.

Connection variables such as:

```text
ansible_host
ansible_port
ansible_user
```

can come from inventory and other variable sources.

## Agentless does not mean dependency-free

Many Unix modules rely on Python or other tools on the target. Some modules are implemented differently or bootstrap capabilities, and other platform types have different requirements.

Before automating a minimal host image, network appliance, container, or unusual operating system, verify the selected module's actual target requirements rather than assuming SSH alone is sufficient.

## Idempotency

Ansible is commonly used to express convergent configuration, but not every task is idempotent.

Compare:

```yaml
- name: Ensure package is installed
  ansible.builtin.package:
    name: nginx
    state: present
```

with:

```yaml
- name: Run arbitrary installer
  ansible.builtin.shell: ./install.sh
```

The first module has a declared state model. The shell command's idempotency depends entirely on the script.

Good automation aims for:

```text
first run  -> changes system toward desired state
second run -> reports no change when state already matches
```

Repeated `changed` results with no intended drift are a signal to investigate.

## `changed_when` and `failed_when`

Ansible lets task authors override change and failure interpretation.

Example:

```yaml
- name: Check application status
  ansible.builtin.command: /usr/local/bin/app-status
  register: status
  changed_when: false
  failed_when: status.rc not in [0, 3]
```

These controls are powerful because they affect handlers, failure flow, reporting, and automation gates.

Do not use `changed_when: false` or `failed_when: false` merely to hide noisy or broken behavior.

## Handlers

Handlers run in response to notifications from changed tasks.

Example:

```yaml
tasks:
  - name: Install service configuration
    ansible.builtin.template:
      src: app.conf.j2
      dest: /etc/example/app.conf
      mode: '0644'
    notify: Restart example service

handlers:
  - name: Restart example service
    ansible.builtin.service:
      name: example
      state: restarted
```

This separates **configuration change** from **expensive side effect**.

Multiple tasks can notify the same handler, and the handler normally runs once when flushed for that host.

## Handler failure semantics

By default, a later task failure can prevent a previously notified handler from running on that host.

That can create a half-applied configuration: a file changed but the service was not restarted.

For workflows where completing notified handlers is safer, evaluate `force_handlers` and the surrounding failure model deliberately.

## Roles

Roles package reusable automation using a conventional directory structure such as:

```text
roles/web/
  defaults/
  vars/
  tasks/
  handlers/
  templates/
  files/
  meta/
```

Roles can encapsulate:

- task sequences;
- handlers;
- defaults;
- stronger role-specific vars;
- templates/files;
- dependencies and metadata.

Good roles expose stable inputs and outputs rather than depending on hidden global variables.

## Role variable design

Prefer:

- low-precedence defaults for user-overridable values;
- namespaced variable names;
- explicit required inputs;
- documented supported operating systems and versions;
- validation of critical arguments where possible.

Avoid putting ordinary user-tunable settings in high-precedence role vars because callers then have fewer safe ways to override them.

## Collections

Collections are the distribution format for Ansible content.

A collection can contain:

- modules;
- action plugins;
- roles;
- inventory plugins;
- connection plugins;
- lookup/filter/test plugins;
- playbooks;
- other plugin types and supporting code.

Collection content uses a Fully Qualified Collection Name (FQCN):

```text
namespace.collection.plugin
```

For example:

```yaml
ansible.builtin.copy:
```

Using FQCNs makes content origin explicit and reduces ambiguity when several collections expose the same short plugin name.

## Collection supply chain

Collections can execute privileged automation logic on the control node and managed nodes.

Pin and review collection versions according to risk.

Important controls include:

- explicit source servers;
- version constraints;
- artifact verification/signatures where supported;
- dependency review;
- reproducible installation;
- restricted write access to internal collections;
- separation of development and production credentials.

Do not treat `requirements.yml` as harmless data. It can select executable automation dependencies.

## Plugins

Ansible is plugin-oriented.

Major plugin classes include:

- action;
- connection;
- inventory;
- strategy;
- vars;
- lookup;
- filter;
- test;
- callback;
- cache;
- become;
- shell;
- network-specific plugins.

Plugin loading paths can come from collections, adjacent directories, configuration, and built-in sources depending on plugin type.

This flexibility is a feature and a supply-chain concern. A local plugin with a conflicting name can change behavior without any visible change in the task body if short names are used carelessly.

## Lookup plugins

Lookups fetch data from external sources such as files, APIs, databases, or secret stores.

Crucially, lookups run on the **control node** as part of templating.

Example:

```yaml
vars:
  token: "{{ lookup('community.hashi_vault.hashi_vault', 'secret=...') }}"
```

A lookup may therefore have access to control-node files, credentials, environment variables, and networks.

Treat untrusted lookup inputs carefully. Some lookup implementations may invoke shell-like behavior or external processes; use documented escaping and trust rules.

## Filters and tests

Filters transform values inside Jinja expressions. Tests evaluate conditions.

They can come from collections and therefore execute plugin code on the control node.

Prefer FQCNs where the plugin type and documentation support them, especially in shared automation where ambiguous names are risky.

## Jinja templating

Jinja expressions are used throughout Ansible for variables, conditions, templates, and plugin inputs.

Templating happens primarily on the control node.

Examples:

```yaml
name: "{{ app_name }}"
when: ansible_facts['os_family'] == 'Debian'
```

The danger is treating arbitrary external strings as safe code or shell fragments.

Never assume YAML quoting is equivalent to shell escaping. When a variable crosses into a shell command, SQL query, URL, or another interpreter, use the target-specific safe module or escaping mechanism.

## Configuration precedence

Ansible behavior can be configured through several channels, including:

- configuration files;
- environment variables;
- command-line options;
- playbook keywords;
- Ansible variables.

Different categories have their own precedence rules.

Use:

```bash
ansible-config dump --only-changed
ansible-config view
```

when debugging an unexpected runtime setting.

A hidden user-level `ansible.cfg` or CI environment variable can explain why the same playbook behaves differently on two control nodes.

## Keep configuration with automation

For team automation, prefer a reviewed project configuration over relying on undocumented per-user defaults.

Be careful with configuration-file discovery in writable directories. An automation runner should not accidentally consume attacker-controlled configuration or plugin paths.

## Execution strategy

The strategy plugin controls host/task scheduling.

The default `linear` strategy conceptually does:

```text
task 1 -> current batch of hosts
task 2 -> current batch of hosts
task 3 -> current batch of hosts
```

The `free` strategy allows hosts to advance through the play independently as fast as each host can complete tasks.

Strategy choice can affect ordering assumptions, shared dependencies, debugging, and rollout safety.

## Forks

Forks control how many hosts Ansible works on concurrently.

The community documentation describes a default of five forks for standard playbook execution, though project or controller configuration can override it.

Increasing forks can improve throughput but can also overload:

- the control node;
- SSH bastions;
- package mirrors;
- APIs;
- identity services;
- shared storage;
- databases or load balancers touched by delegated tasks.

Tune concurrency based on the slowest shared dependency, not only CPU availability on the Ansible runner.

## Rolling updates with `serial`

`serial` limits the active host batch.

Example:

```yaml
- hosts: web
  serial: 2
  tasks:
    - name: Deploy application
      ...
```

This supports rolling changes where only part of a fleet is modified at once.

Design batch size against service redundancy. `serial: 50%` can still be too aggressive if the service cannot tolerate half its capacity being unhealthy.

## `throttle`

`throttle` can limit concurrency for an individual task or block below the wider fork/batch limit.

Use it when a particular dependency can handle less concurrency than the rest of the play.

Example uses:

- database schema operations;
- rate-limited APIs;
- firmware updates;
- shared storage mutations.

## `run_once`

`run_once` executes a task for one host in the current batch context and applies result/variable semantics accordingly.

It is often misunderstood as a global exactly-once distributed lock.

When batching with `serial`, reason carefully about whether the task can run once per batch rather than once for the entire play.

For truly global external operations, design explicit coordination rather than relying on vague assumptions about `run_once`.

## Delegation

`delegate_to` runs a task in the context of another host.

Common uses include:

- removing a server from a load balancer before maintenance;
- updating DNS;
- calling a monitoring system;
- performing a control action from localhost.

Delegation changes variable and connection context. Most templated connection/become/shell options are resolved for the delegated host, not the original inventory host.

## Delegation concurrency hazard

Delegating many hosts to update one shared resource does not automatically serialize the operation.

For example, ten hosts can all delegate a file update to one load-balancer node concurrently.

Mitigate with an appropriate combination of:

- `run_once`;
- `serial`;
- `throttle`;
- a loop over host data;
- an external transactional API;
- a separate coordination play.

## Asynchronous tasks

By default, tasks are synchronous.

`async` can allow long-running operations to outlive an individual connection wait, and `poll` controls whether Ansible waits/polls or starts the job and moves on.

Example:

```yaml
- name: Start long operation
  ansible.builtin.command: /usr/local/bin/long-job
  async: 3600
  poll: 0
  register: job
```

Async support depends on the action/module and execution mode. It is not a universal concurrency abstraction.

## Check mode

Check mode asks supported modules to predict what they would change without performing the change.

```bash
ansible-playbook site.yml --check
```

This is useful but **not equivalent to a transactionally accurate dry run**.

Limitations include:

- modules that do not support check mode;
- commands/shell scripts with no predictive model;
- later tasks depending on data that would have been created by earlier tasks;
- APIs whose real validation occurs only during write;
- runtime side effects outside the module's model.

Use check mode as evidence, not proof of safety.

## Diff mode

Diff mode can show before/after content for supported modules:

```bash
ansible-playbook site.yml --check --diff
```

Diff output can expose secrets, certificates, configuration files, tokens, or sensitive application data.

Restrict and sanitize CI artifacts where diff output is retained.

## Privilege escalation

`become` allows a task to execute through a privilege-escalation method such as sudo where supported.

Example:

```yaml
- hosts: web
  become: true
  tasks:
    - name: Manage system package
      ansible.builtin.package:
        name: nginx
        state: present
```

Do not run an entire play as privileged merely because one task needs it. Scope privilege to the smallest practical boundary.

The privilege-escalation credential and resulting target privileges are part of the automation threat model.

## Vault

Ansible Vault encrypts variables or files at rest.

Useful commands include:

```bash
ansible-vault encrypt secrets.yml
ansible-vault encrypt_string 'secret-value' --name api_token
ansible-vault rekey secrets.yml
```

Vault protects encrypted content **while stored**. Once decrypted for a run, plaintext can still leak through:

- task output;
- debug statements;
- module errors;
- temporary files;
- callback plugins;
- process environment;
- downstream commands.

## `no_log`

Use `no_log: true` for tasks whose arguments or results contain secrets and whose module behavior does not already suppress them adequately.

Example:

```yaml
- name: Authenticate to private API
  some.collection.login:
    token: "{{ api_token }}"
  no_log: true
```

`no_log` reduces normal Ansible output exposure. It is not a complete secret-isolation mechanism and should not replace proper secret storage, least privilege, and runner isolation.

## Vault password handling

Avoid storing a vault password beside the encrypted vault content with equivalent access controls.

Better approaches include:

- interactive prompts for operator runs;
- protected CI secrets;
- secret-manager lookup/password scripts;
- workload identity that retrieves a vault credential at runtime.

Separate vault IDs can limit which secret domains a run must unlock.

## SSH host-key verification

SSH host-key checking helps detect connections to unexpected hosts.

Disabling verification globally may make ephemeral automation convenient but weakens protection against misrouting and man-in-the-middle conditions.

For dynamic fleets, solve host identity operationally rather than silently accepting every presented key without understanding the threat model.

## Secrets and inventory

Avoid embedding plaintext passwords directly in inventory.

Inventory is frequently copied, rendered, debugged, or queried through tools such as `ansible-inventory`.

Prefer protected secret sources and keep ordinary inventory focused on identity, topology, and non-secret connection metadata.

## Commands and shell

`ansible.builtin.command` executes a command without a shell by default and should generally be preferred over `ansible.builtin.shell` when shell features are not required.

Shell introduces another interpreter and therefore additional quoting/injection complexity.

If a purpose-built module exists, prefer the module because it can often provide:

- idempotency;
- check mode;
- structured errors;
- platform-aware behavior;
- better change reporting.

## Error handling

By default, a task failure stops further tasks on that host while other hosts may continue.

Controls include:

- `failed_when`;
- `ignore_errors`;
- `ignore_unreachable`;
- `any_errors_fatal`;
- maximum failure percentage;
- blocks with `rescue` and `always`;
- handler forcing.

Failure behavior is part of rollout architecture.

A service rollout that can tolerate one host failure may need very different policy from a database migration where partial execution is dangerous.

## Blocks, `rescue`, and `always`

Blocks group tasks under shared conditions or privilege settings and support error-handling structure.

Conceptually:

```yaml
- block:
    - name: Apply risky change
      ...
  rescue:
    - name: Attempt recovery
      ...
  always:
    - name: Record completion state
      ...
```

`rescue` is not automatic rollback. It runs whatever recovery logic you explicitly write.

## Tags

Tags select subsets of tasks:

```bash
ansible-playbook site.yml --tags config
```

Tags are useful for debugging and optional workflows but can become an architectural hazard when normal correctness depends on operators remembering a complicated tag combination.

A complete standard playbook run should generally remain the easiest safe path.

## Includes versus imports

Reusable task/play/role content can be included dynamically or imported statically depending on construct.

The distinction affects when content is expanded and how conditions/tags behave.

When a playbook becomes difficult to reason about, reduce deep layers of dynamic inclusion and make execution paths more explicit.

## Configuration management versus orchestration

Ansible handles both.

### Configuration management

The desired end state matters:

```yaml
ansible.builtin.service:
  name: nginx
  state: started
  enabled: true
```

### Orchestration

The ordered procedure matters:

```text
remove host from load balancer
stop service
upgrade package
migrate local config
start service
health check
return host to load balancer
```

A production automation design usually contains both convergent resource tasks and procedural rollout steps.

## Terraform boundary

Terraform and Ansible overlap but have different centers of gravity.

A common ownership model is:

```text
Terraform/OpenTofu
  -> provision VM, VPC, IAM, DNS, load balancer

Ansible
  -> configure operating system and application on VM
```

The exact boundary can differ, but the two systems should not independently own the same mutable property.

If Terraform continually restores one value while Ansible continually changes it, the automation architecture has an ownership conflict.

## Kubernetes boundary

Ansible collections can create or modify Kubernetes API objects and can orchestrate cluster-adjacent operations.

Kubernetes controllers, however, continuously reconcile desired state.

For application resources, a common model is:

```text
Ansible -> bootstrap / migration / one-time orchestration
GitOps or Kubernetes controllers -> continuous desired-state ownership
```

Avoid periodic Ansible runs fighting continuous controllers over the same fields.

## Control platforms: AWX and Automation Platform

AWX and Red Hat Ansible Automation Platform provide controller-oriented capabilities around Ansible execution such as inventories, credentials, scheduling, APIs, RBAC, workflow orchestration, and execution environments.

They are not the same thing as `ansible-core`.

When debugging behavior, separate:

```text
playbook / ansible-core issue
```

from:

```text
controller inventory / credential / execution-environment / scheduling issue
```

That boundary prevents “works on my laptop” assumptions when the production runner has different collections, Python versions, credentials, or configuration.

## Reproducible execution environments

Production automation should pin more than playbook Git commits.

Relevant dependencies include:

- ansible-core version;
- Python runtime;
- collections and versions;
- Python packages required by modules/plugins;
- system packages and command-line tools;
- SSH/client libraries;
- environment/configuration;
- custom plugins.

Containerized execution environments can make these dependencies more reproducible, but only if their image build and collection/package inputs are pinned and reviewed.

## Collection requirements

A project can declare collection dependencies in a requirements file for `ansible-galaxy collection install`.

Treat the file like a dependency manifest.

Production controls should answer:

- Which registry/servers are trusted?
- Are versions pinned sufficiently?
- Are transitive collection dependencies reviewed?
- Can the artifact be reconstructed if a remote source disappears?
- Are signatures verified where available?

## Performance model

Run time can be dominated by:

- SSH/connection setup;
- fact gathering;
- control-node CPU for templating;
- module transfer/startup;
- slow package repositories;
- remote API latency;
- low fork count;
- overly strict serialization;
- huge inventories;
- dynamic inventory API calls;
- expensive vars/lookups;
- callback/output volume.

Measure before tuning.

## Persistent connection considerations

For some platforms and plugins, persistent connection mechanisms reduce repeated setup cost.

Benefits can include lower latency and less authentication overhead.

Risks include stale sessions, credential lifetime, resource usage, and debugging complexity.

Use the connection plugin's documented behavior rather than assuming all transports persist connections identically.

## Large-fleet strategy

For large estates:

- use authoritative dynamic inventory;
- cache expensive inventory/facts when appropriate;
- tune forks against infrastructure limits;
- batch risky changes with `serial`;
- isolate environments;
- reduce unnecessary fact gathering;
- avoid global shared delegated writes;
- make retries safe and idempotent;
- collect structured run evidence;
- partition automation by operational blast radius.

Do not solve every scale problem by only increasing forks.

## Rolling deployment pattern

A safe service rollout can look like:

```text
batch N hosts
 -> remove batch from traffic
 -> verify drain
 -> deploy/configure
 -> restart if changed
 -> health check
 -> return to traffic
 -> verify service
 -> continue next batch
```

Ansible primitives supporting this include:

- `serial`;
- handlers;
- delegation;
- `until`/retries;
- failure thresholds;
- blocks/rescue;
- explicit health-check tasks.

The external load balancer and health system still define the real safety boundary.

## Retry and `until`

Tasks can retry until a condition succeeds.

Use retries for transient eventual-consistency or readiness conditions, not to hide deterministic configuration errors.

Good retry logic includes:

- bounded attempts;
- meaningful delay;
- explicit success condition;
- diagnostics on exhaustion.

Unbounded or very long retries can pin forks and hide outages.

## Common failure modes

### Wrong inventory selected

Symptoms:

- correct playbook targets the wrong environment;
- many unexpected hosts appear in the run.

Response:

- stop before writes;
- inspect `--list-hosts` and inventory graph;
- separate environment inventory and credentials.

### Variable unexpectedly overridden

Symptoms:

- task renders an unexplained value;
- local and CI runs differ.

Response:

- trace variable precedence;
- inspect extra vars and controller inputs;
- simplify ownership.

### Non-idempotent shell task

Symptoms:

- every run reports changed;
- repeated execution duplicates data or causes restarts.

Response:

- replace with an idempotent module;
- add guarded conditions only when the side effect is well understood;
- explicitly define change/failure semantics.

### Handler not executed after later failure

Symptoms:

- configuration changed;
- service restart/reload did not occur.

Response:

- understand handler/failure policy;
- evaluate `force_handlers` or restructure the transaction boundary.

### Dynamic inventory outage

Symptoms:

- expected hosts disappear;
- inventory plugin errors;
- empty target set.

Response:

- fail closed for critical production workflows;
- validate inventory population before mutation;
- use caching only with explicit freshness rules.

### Too much concurrency

Symptoms:

- SSH connection failures;
- API throttling;
- package mirror overload;
- shared service saturation.

Response:

- reduce forks or task-specific concurrency;
- batch with `serial`;
- use `throttle` for bottleneck operations;
- fix rate-limit/retry architecture.

### Delegated shared-write race

Symptoms:

- several target hosts corrupt or overwrite one delegated file/resource.

Response:

- serialize the shared mutation;
- aggregate data first;
- use a transactional external API.

### Check mode looked safe but apply failed

Cause:

- module lacked full check support;
- remote API validation differed;
- later tasks depended on values not created in check mode.

Response:

- treat check mode as advisory;
- test in representative non-production environments;
- verify module support attributes.

### Secret leaked in output

Response:

- revoke/rotate the secret;
- scrub retained artifacts where possible;
- add `no_log` and safer callback/log policy;
- inspect whether the secret also leaked to command history, temp files, diffs, or controller events.

### Collection upgrade changes behavior

Possible causes:

- module default changes;
- renamed plugin/module;
- return schema change;
- dependency change;
- remote API compatibility update.

Response:

- pin versions;
- review collection changelogs;
- test upgrades separately from playbook feature changes.

## Debugging workflow

When a run behaves unexpectedly:

1. record `ansible --version`;
2. inspect `ansible-config dump --only-changed`;
3. verify inventory source and selected hosts;
4. inspect host/group variables;
5. verify collection versions;
6. use FQCNs to remove plugin ambiguity;
7. reproduce on one non-critical host with `--limit`;
8. use `--check` only where meaningful;
9. increase verbosity cautiously (`-v` through `-vvvv`) while protecting secrets;
10. inspect registered module result fields;
11. distinguish `FAILED` from `UNREACHABLE`;
12. confirm which host actually executed delegated/local tasks;
13. review connection, become, and interpreter settings;
14. rerun only after deciding whether the failed operation is safe to repeat.

Useful commands:

```bash
ansible --version
ansible-config dump --only-changed
ansible-inventory --graph
ansible-inventory --host HOST
ansible-doc FQCN
ansible-galaxy collection list
ansible-playbook site.yml --syntax-check
ansible-playbook site.yml --list-hosts
ansible-playbook site.yml --list-tasks
```

## Unreachable versus failed

An unreachable host generally means Ansible could not establish the required execution path. A failed task means Ansible reached the task context but the operation reported failure.

Treat them differently operationally:

```text
UNREACHABLE -> routing / DNS / SSH / auth / connection / host availability
FAILED      -> module / command / permission / application / input semantics
```

Error-policy controls also distinguish these categories.

## Upgrade discipline

Ansible Core and Collections evolve on independent schedules.

Before upgrading Core:

- read the relevant porting guide;
- test playbooks and custom plugins;
- validate Python support on control and managed nodes;
- test templating behavior;
- verify collection compatibility.

Before upgrading Collections:

- isolate the dependency change;
- review changelog/release notes;
- run module/role tests;
- inspect check-mode and real-run diffs in a safe environment.

Do not combine a Core major/minor migration, collection refresh, inventory redesign, and production rollout into one opaque change.

## Security model

A useful trust map is:

```text
Git repository
   |
   +-- playbooks / roles / config
   +-- collection requirements
   +-- custom plugins
   |
control-node runtime
   |
   +-- inventory / variables
   +-- secret manager / vault keys
   +-- SSH / API credentials
   +-- installed collections
   |
managed systems / remote APIs
```

Compromise at the Git or control-node layer can propagate broadly because automation is intentionally privileged.

Use:

- protected branches/reviews;
- dependency pinning;
- isolated runners;
- least-privilege credentials;
- environment-separated inventory;
- secret redaction;
- host-key and TLS verification;
- audit logging;
- short-lived credentials where possible.

## Anti-patterns

Avoid:

- one inventory containing every environment and every credential domain;
- pervasive use of `shell` when state-aware modules exist;
- disabling host-key checking globally without a threat-model decision;
- plaintext passwords in inventory;
- unpinned collection dependencies in production;
- using short plugin names when source ambiguity matters;
- blanket `ignore_errors: true`;
- blanket `changed_when: false` to make reports look green;
- broad `become: true` when only one task needs privilege;
- relying on check mode as proof that apply is safe;
- increasing forks without understanding shared bottlenecks;
- using `run_once` as if it were a distributed global lock;
- concurrent delegated writes to one shared resource;
- letting Ansible and another controller continuously fight over the same field;
- storing vault passwords beside vault-encrypted content with equivalent access;
- treating third-party collections as passive configuration instead of executable dependencies.

## Operational checklist

Before merge:

- run syntax checks;
- lint/test according to project policy;
- verify collection dependency changes;
- use FQCNs for important modules/plugins;
- review inventory and variable ownership;
- verify secrets are not embedded in Git;
- inspect shell/command tasks for injection and idempotency;
- validate handlers and failure semantics.

Before production execution:

- confirm inventory and `--limit` scope;
- confirm selected hosts with `--list-hosts` when risk warrants it;
- confirm control-node/core/collection versions;
- confirm credentials and privilege scope;
- confirm batch/concurrency settings;
- confirm maintenance window and service capacity;
- confirm rollback/recovery procedure;
- protect diff/verbose output.

After execution:

- review failed and unreachable hosts separately;
- verify handlers completed;
- verify service health externally;
- rerun idempotent convergence where appropriate and investigate unexplained changes;
- archive useful non-secret run evidence;
- rotate any credential accidentally exposed in logs.

## Learning path

### Beginner

Learn:

- inventory;
- ad-hoc commands;
- playbooks and plays;
- tasks and modules;
- variables;
- facts;
- handlers;
- `ansible-playbook`, `ansible-inventory`, and `ansible-doc`.

### Intermediate

Learn:

- roles;
- Collections and FQCNs;
- dynamic inventory;
- variable precedence;
- templates and filters;
- privilege escalation;
- Vault;
- check/diff mode;
- tags;
- error handling;
- delegation;
- `serial`, forks, and strategy plugins.

### Advanced

Learn:

- action/module execution internals;
- plugin loading and supply-chain controls;
- large-fleet inventory/fact caching;
- controller/execution-environment reproducibility;
- custom inventory and connection plugins;
- rollout/failure-domain design;
- delegated concurrency hazards;
- secrets and control-node trust boundaries;
- collection/Core upgrade compatibility;
- integration boundaries with Terraform, OpenTofu, Kubernetes, and GitOps systems.

## Relationships

### Terraform

`cloud/terraform` is adjacent rather than identical. Terraform centers on persistent resource identity, provider-driven plan/apply lifecycle, and infrastructure state. Ansible centers on task execution, configuration management, and orchestration. They are often complementary when ownership is explicit.

### Kubernetes

`cloud/kubernetes` is a common integration target. Ansible can bootstrap and orchestrate Kubernetes-related operations, but Kubernetes controllers usually own continuous reconciliation of cluster resources.

## Taxonomy

- Kind: `tool`
- Domains: `cloud`, `devops`
- Deployment: `cli`, `local`
- License: `GPL-3.0-or-later`
- Maturity: `deep-dive`

## Primary references

- Ansible Community Documentation: https://docs.ansible.com/projects/ansible/latest/
- ansible-core repository: https://github.com/ansible/ansible
- ansible-core project metadata: https://github.com/ansible/ansible/blob/devel/pyproject.toml
- ansible-core license: https://github.com/ansible/ansible/blob/devel/COPYING
- Installation/package distinction: https://docs.ansible.com/projects/ansible-core/devel/installation_guide/intro_installation.html
- Core concepts: https://docs.ansible.com/projects/ansible-core/devel/getting_started/basic_concepts.html
- Playbooks: https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks.html
- Dynamic inventory: https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_dynamic_inventory.html
- Connection plugins: https://docs.ansible.com/projects/ansible/latest/plugins/connection.html
- Module architecture: https://docs.ansible.com/projects/ansible/latest/dev_guide/developing_program_flow_modules.html
- Strategy plugins: https://docs.ansible.com/projects/ansible/latest/plugins/strategy.html
- Execution strategies: https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_strategies.html
- Variables: https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_variables.html
- Roles: https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_reuse_roles.html
- Collections: https://docs.ansible.com/projects/ansible/latest/collections_guide/index.html
- Error handling: https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_error_handling.html
- Executing playbooks: https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_execution.html
- Vault: https://docs.ansible.com/projects/ansible/latest/vault_guide/vault.html
- Lookups: https://docs.ansible.com/projects/ansible/latest/plugins/lookup.html
- Releases and maintenance: https://docs.ansible.com/projects/ansible/latest/reference_appendices/release_and_maintenance.html

## Verification

This deep-dive was reviewed on **2026-09-06** against current Ansible Community and ansible-core documentation plus the canonical `ansible/ansible` repository. Core/runtime support, collection compatibility, plugin behavior, controller/execution-environment features, and package contents change independently and should be rechecked against the version-specific upstream documentation before production upgrades.

## Maintenance

Prioritize review when:

- ansible-core changes execution, templating, plugin, or variable semantics;
- the `ansible` community package changes its collection composition materially;
- inventory or connection plugin behavior changes;
- collection verification/distribution behavior changes;
- control/managed-node Python support changes;
- Vault or secret-handling guidance changes;
- a major porting guide identifies behavior that can silently alter existing playbooks.
