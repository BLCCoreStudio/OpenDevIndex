# Module Deepening Checklist

Use this checklist when upgrading an existing OpenDevIndex module from an overview toward guide or deep-dive maturity. It complements [`MODULE_STANDARD.md`](MODULE_STANDARD.md); it does not replace editorial judgment or make every section mandatory.

## 1. Establish the current state

Before editing:

- read the existing `entry/README.md`, `entry/entry.yaml`, `entry/sources.md`, and `entry/history.md`;
- confirm the current maturity and verification date;
- identify which claims are version-sensitive or likely to age quickly;
- inspect existing typed relationships and avoid adding duplicate or artificial graph edges;
- identify the most important reader questions the current module does not answer.

A deepening change should make the module materially more useful, not merely longer.

## 2. Strengthen the mental model

The module should explain, where applicable:

- what problem the technology solves and why it exists;
- its core data/control flow or execution model;
- the main objects, processes, layers, files, protocols, or components;
- which boundaries belong to the technology and which belong to adjacent systems;
- the assumptions a reader must understand before using or operating it.

Prefer diagrams-in-words and concise examples over feature lists.

## 3. Add practical workflows

For important workflows:

- explain the goal before showing commands or APIs;
- include only commands/examples that reinforce the mental model;
- cover normal setup/use plus at least one recovery or diagnostic path when relevant;
- call out destructive, irreversible, privileged, or security-sensitive operations;
- avoid command dumps that are not tied to a clear concept.

## 4. Cover engineering trade-offs

When relevant, document:

- performance characteristics and scaling limits;
- reliability behavior and common failure modes;
- recovery, backup, rollback, or repair boundaries;
- security, permissions, secrets, supply-chain, and trust boundaries;
- privacy or data-retention implications;
- operational complexity and where the technology is a poor fit.

Avoid universal rankings. State the conditions under which a trade-off matters.

## 5. Compare deliberately

For alternatives and adjacent technologies:

- explain the architectural or operational difference that affects a decision;
- distinguish substitutes from complements;
- avoid popularity-only comparisons;
- add a typed relationship only when it helps explain architecture, interoperability, history, or a useful learning path;
- use a curated comparison view when the decision requires multiple reviewed dimensions rather than a one-line link.

## 6. Improve source quality

For every substantial addition:

- prefer official specifications, project documentation, canonical repositories, standards, original research, and security advisories;
- remove or replace weak sources when a stronger primary source exists;
- make version-sensitive claims auditable;
- update verification metadata when the module has actually been rechecked;
- do not treat source reachability alone as factual verification.

## 7. Add learning navigation

A mature module should help the reader continue:

- state useful prerequisites when the subject assumes them;
- provide a small beginner-to-advanced learning sequence;
- link to closely related OpenDevIndex modules where they form a deliberate next step;
- keep “what to learn next” focused rather than turning it into an unbounded link list.

## 8. Apply kind-specific review

Use the subject-specific guidance in [`MODULE_STANDARD.md`](MODULE_STANDARD.md#kind-specific-sections). In particular, check whether the module needs coverage such as:

- language execution/type/memory/package models;
- database storage/transactions/indexes/replication/recovery;
- protocol wire/message/versioning/security/interoperability behavior;
- operating-system process/memory/scheduling/filesystem/driver boundaries;
- AI training/inference/data/evaluation/deployment/safety boundaries;
- hardware execution/memory/interface/performance/power constraints;
- developer-tool project/configuration/automation/extension/failure-mode workflows.

Do not add headings that are meaningless for the technology just to satisfy a template.

## 9. Review for editorial regressions

Before considering the change complete, verify that it did not introduce:

- placeholder sections;
- copied marketing language;
- unsupported superlatives or vague claims;
- large generated code listings;
- artificial graph edges;
- stale or contradictory version claims;
- examples that imply unsafe defaults;
- duplicated material that belongs in another module.

## 10. Run repository checks

For changes that touch catalog/core repository data or tooling, run the checks documented in [`CONTRIBUTING.md`](../CONTRIBUTING.md#local-checks). Module branches should also satisfy their structure/schema validation and keep authoritative sources auditable.

A module should only be promoted in maturity when the content itself meets the corresponding editorial standard. Passing automation is necessary for repository integrity, but it is not a substitute for factual and technical review.
