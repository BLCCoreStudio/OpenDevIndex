# OpenDevIndex Knowledge Module Standard

OpenDevIndex modules are not meant to be dictionary entries or link cards. A mature module should help a reader understand a technology well enough to place it in the wider computing ecosystem, use it safely, compare it with alternatives, and know what to learn next.

This document defines the editorial depth target for knowledge modules.

## Depth levels

### Overview

An overview is the minimum publishable module. It provides a source-backed identity, taxonomy, use cases, key points, canonical links, and verification metadata.

Overview modules are useful for coverage and discovery, but they are not considered finished learning resources.

### Guide

A guide explains the subject beyond its identity. It should cover the important mental model, major components, normal workflows, common tools, trade-offs, and practical examples.

### Deep dive

A deep dive is the target state for important technologies. It should be useful as a standalone technical reference while remaining readable enough to serve as an entry point for learners.

Not every subject needs every section below, but omitted sections should be irrelevant to the subject rather than merely unfinished.

## Deep-dive structure

Where applicable, a mature module should answer the following questions.

1. **What is it?** — a precise explanation without marketing language.
2. **Why does it exist?** — the problem, historical context, and design motivation.
3. **How does it work?** — the core mental model and data/control flow.
4. **Internal architecture** — important subsystems, layers, processes, files, objects, or components.
5. **Important concepts** — the vocabulary needed to reason about the subject.
6. **Data or object model** — important internal data structures and relationships when applicable.
7. **Common workflows** — how the technology is normally used in real projects.
8. **Commands, APIs, or examples** — small practical examples that reinforce the mental model.
9. **Tools used with it** — editors, debuggers, build systems, libraries, services, extensions, or companion tools.
10. **Integrations** — systems and standards it commonly connects to.
11. **Alternatives** — meaningful competing or adjacent technologies.
12. **Trade-offs** — where the technology is strong, weak, or inappropriate.
13. **Performance characteristics** — scaling behavior, bottlenecks, latency, throughput, memory, storage, or complexity where relevant.
14. **Reliability and failure modes** — common ways it breaks and how operators or developers recover.
15. **Security and privacy** — trust boundaries, dangerous defaults, attack surface, secrets, permissions, and supply-chain concerns where relevant.
16. **Common mistakes** — recurring conceptual and operational errors.
17. **Ecosystem** — important projects, standards, communities, and extensions around the subject.
18. **Learning path** — prerequisites, beginner progression, and advanced topics.
19. **Authoritative sources** — official documentation, standards, canonical repositories, research, or advisories.
20. **Related OpenDevIndex modules** — typed graph relationships and useful next hops.
21. **What to learn next** — a small set of deliberate follow-on topics rather than an unbounded link dump.
22. **Verification and maintenance** — when the content was checked and what facts are most likely to age.

## Kind-specific sections

The structure should adapt to the kind of technology instead of forcing meaningless headings.

- **Languages:** execution model, type system, memory model, package ecosystem, tooling, interoperability, common idioms.
- **Databases:** storage engine, indexes, transactions, consistency, replication, query model, recovery, operational trade-offs.
- **Protocols and standards:** wire model, message flow, negotiation, versioning, security properties, interoperability, extensions.
- **Operating systems and kernels:** process model, memory, scheduling, filesystems, drivers, security boundaries, boot and observability.
- **AI models and frameworks:** model architecture, training/inference model, hardware requirements, data flow, evaluation, deployment, safety limitations.
- **Hardware and architectures:** instruction or execution model, memory hierarchy, interfaces, implementations, performance constraints, power and compatibility.
- **Developer tools:** internal model, project integration, configuration, automation, extensions, failure modes, alternatives, and workflow examples.

## Source requirements

Deep modules should prefer primary sources whenever possible.

Use, in descending preference:

1. official specifications and project documentation;
2. canonical source repositories and maintainer documentation;
3. standards bodies and original research;
4. vendor security advisories and authoritative engineering documentation;
5. reputable secondary sources only when primary material does not explain the topic sufficiently.

A source link alone is not evidence that a claim was reviewed. The module should make clear which claims depend on version-sensitive facts.

## Internal linking

A deep module should behave like a node in a knowledge graph, not a dead-end article.

Use typed relationships for machine-readable graph edges and add human-readable links where they help navigation. Prefer deliberate links such as:

- `depends-on`
- `uses`
- `implements`
- `integrates-with`
- `alternative-to`
- `based-on`
- `part-of`
- `predecessor-of`
- `successor-of`
- `related-to`

Do not create relationships only to inflate graph density. Every edge should help explain architecture, history, interoperability, or a sensible learning path.

## Examples

Examples should be small enough to understand quickly and realistic enough to teach the actual model. Avoid long generated code listings, contrived examples, and copy-paste-heavy tutorials that hide the concept being explained.

Commands should be accompanied by the idea they demonstrate. A command list without explanation is not a deep module.

## Anti-patterns

A module is not considered mature when it mainly contains:

- a one-paragraph definition;
- generic statements such as "widely used" or "powerful" without explaining why;
- an undifferentiated list of links;
- headings with placeholder text;
- copied marketing descriptions;
- dozens of commands without a mental model;
- artificial relationships created only to increase graph counts;
- claims that cannot be traced to credible sources.

## Migration strategy

OpenDevIndex can grow coverage and depth independently. Existing overview modules remain valid, but important subjects should be upgraded progressively.

Priority for deepening modules:

1. foundational technologies with many graph connections;
2. high-usage developer tools and platforms;
3. technologies that unlock understanding of many other modules;
4. security-sensitive or operationally complex subjects;
5. areas where the current index is broad but shallow.

The first flagship deep module is `tool/git`. The second is `tool/docker`. Together they demonstrate that deep modules should adapt to the subject: Git emphasizes object/commit/ref models and history manipulation, while Docker emphasizes layered architecture, OCI/runtime boundaries, build systems, isolation, storage, networking, and operational security. Future deep modules should match their source discipline and explanatory depth without mechanically copying either structure.
