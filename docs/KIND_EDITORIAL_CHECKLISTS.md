# Kind-specific editorial checklists

Use these prompts after the general module standard and deepening checklist. They are review aids, not rigid section templates: omit a prompt when it is genuinely irrelevant and explain unusual scope choices in the pull request.

## Tools

- Explain the task boundary: what the tool owns and what it deliberately delegates.
- Show the normal workflow from input/configuration through observable output.
- Document important local, remote, cache, state, and credential boundaries.
- Include failure recovery for interrupted or partially successful operations.
- Distinguish convenience defaults from production-safe practice.
- Cover plugin/extension or supply-chain risk when third-party code is executable.
- Compare at least one credible alternative on workflow and operational trade-offs.

## Languages and runtimes

- Separate language semantics from compiler/interpreter/runtime implementation details.
- Explain execution and memory models at the depth appropriate to module maturity.
- Identify concurrency, error, module/package, and interoperability boundaries.
- Note compatibility/versioning commitments and common migration hazards.
- Include representative build/run/debug/test workflows rather than syntax catalogs.
- Cover package/dependency supply-chain controls where applicable.

## Frameworks and libraries

- State the abstraction the framework provides and what remains application-owned.
- Explain lifecycle, dependency injection/state/data-flow, extension, and configuration models where relevant.
- Distinguish framework behavior from host language/runtime/platform behavior.
- Document performance costs, deployment constraints, upgrade boundaries, and escape hatches.
- Include testing, observability, and failure-debugging workflows.
- Compare alternatives using architectural fit rather than popularity.

## Cloud, infrastructure, and distributed systems

- Draw clear control-plane, data-plane, and trust boundaries.
- Explain reconciliation, scheduling, replication, consistency, or orchestration semantics as applicable.
- Identify durable state, identity, tenancy, region/failure-domain, and network assumptions.
- Cover rollout, rollback, backup/restore, disaster recovery, and degraded-mode behavior.
- Include capacity, latency, cost, security, and availability trade-offs.
- Make managed-service versus self-hosted responsibility boundaries explicit.

## Databases and storage

- Explain logical data model and physical/storage-engine boundaries separately.
- Cover transactions, isolation/concurrency, locking or conflict behavior, and durability.
- Describe indexing/query-planning or access-path behavior where relevant.
- Include backup, restore, replication, failover, corruption/integrity, and migration workflows.
- State consistency and filesystem/network assumptions.
- Connect tuning advice to measurable bottlenecks instead of generic settings lists.

## Security, cryptography, and privacy

- State threat model, protected assets, attacker capabilities, and out-of-scope assumptions.
- Separate preventive, detective, recovery, and operational controls.
- Prefer standards, specifications, vendor advisories, and primary security documentation for consequential claims.
- Avoid presenting configuration snippets as universally safe defaults.
- Cover key/secret lifecycle, trust anchors, identity, logging, update, and compromise-recovery boundaries when applicable.
- Time-scope rapidly changing vulnerability or advisory claims and record verification dates.

## Protocols and standards

- Identify authoritative specification versions and status.
- Explain actors, state machines, message/data model, negotiation, and failure semantics.
- Separate normative requirements from common implementation choices.
- Cover compatibility, extension/versioning, security, privacy, and deployment assumptions.
- Include at least one end-to-end exchange or workflow when it improves understanding.
- Note important interoperability tests or implementation pitfalls.

## AI and machine learning

- Distinguish model architecture, training/inference system, product wrapper, and deployment runtime.
- State data, compute, evaluation, latency, cost, privacy, and safety assumptions.
- Explain inputs/outputs, context/state behavior, failure modes, and observability.
- Avoid benchmark claims without dataset, metric, version, and evaluation context.
- Cover reproducibility and model/dependency provenance where practical.
- Compare alternatives by workload and constraints rather than headline capability.

## Concepts

- Define the concept independently of any single implementation or vendor.
- Explain the mental model, invariants, and boundaries before examples.
- Use multiple implementations when that prevents accidental product-specific framing.
- Include common misconceptions, failure modes, and trade-offs.
- Link naturally to prerequisite and next-step modules without manufacturing graph edges.

## Open-source projects and ecosystems

- Separate project governance, technical architecture, distribution, and hosted/commercial offerings.
- Identify upstream release/support policy and dependency/plugin ecosystem boundaries.
- Explain contribution, extension, upgrade, and compatibility models where relevant.
- Cover supply-chain, maintainer, signing/release, and provenance considerations for critical projects.
- Avoid equating repository activity or popularity with technical quality.

## Final kind-aware review

Before requesting review, verify that:

1. the module's kind-specific architecture and ownership boundaries are clear;
2. practical workflows are present where the subject is operational;
3. consequential security/reliability claims are source-backed and appropriately scoped;
4. trade-offs and alternatives are technically fair;
5. version-sensitive statements identify their scope or verification date;
6. links and relationships help readers navigate rather than inflate graph density;
7. the module still satisfies the general `MODULE_STANDARD.md` and repository validation rules.
