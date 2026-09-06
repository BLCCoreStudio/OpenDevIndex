# OpenDevIndex Roadmap

OpenDevIndex is not being developed as a race to publish the largest number of module branches. The roadmap is organized around **trust, depth, discovery, and useful connections between technologies**.

Coverage still matters, but raw module count is not a quality metric.

## Foundation — complete

The project already has the core infrastructure needed to grow safely:

- stable knowledge-module addresses;
- independently versioned module branches;
- machine-readable entry schemas;
- generated public index and search artifacts;
- source-backed catalogs;
- taxonomy with `kind` and `domains` facets;
- CI validation;
- editorial quality scoring;
- source-health monitoring;
- reproducible trusted publication workflows;
- a Technology Universe coverage map to prevent topic blind spots.

## Current priority — depth

The most important next step is to turn high-value overview modules into genuinely useful technical references.

Priority work:

- establish and enforce the Overview / Guide / Deep dive editorial model;
- deepen foundational technologies before expanding low-value edge coverage;
- explain internal architecture instead of stopping at product descriptions;
- add practical mental models, workflows, commands, APIs, and examples;
- document alternatives and real engineering trade-offs;
- add performance, reliability, security, and privacy sections where relevant;
- build beginner-to-advanced learning paths;
- make authoritative sources easy to audit;
- protect curated deep content from automated publisher regressions.

`tool/git` is the first flagship deep-dive module. `tool/docker` extends that quality bar into container tooling and OCI/runtime boundaries. `concept/containers` establishes the Linux isolation and OCI foundation beneath the tooling, `tool/containerd` covers the node runtime/object-lifecycle layer, and `cloud/kubernetes` carries that chain into API-driven reconciliation, scheduling, networking, storage, security, and distributed cluster operations. `cloud/helm` now adds the Kubernetes package and release-management layer: reusable charts, values/rendering, upgrades and rollbacks, CRD/hook lifecycle, OCI distribution, supply-chain review, and clear ownership boundaries with GitOps and Kubernetes controllers. Future upgrades should match this source discipline and technical usefulness without copying any one module's section layout mechanically.

## Current priority — connected knowledge graph

OpenDevIndex should behave like a navigable technology map rather than a collection of isolated articles.

Priority work:

- validate typed schema-v3 relationships in CI;
- progressively connect foundational modules using meaningful graph edges;
- distinguish architecture, dependency, compatibility, history, and alternative relationships;
- expose graph relationships in human-readable module pages;
- avoid artificial links created only to inflate graph density;
- use relationships to power learning paths and comparison views.

Important relationship types include:

```text
depends-on
uses
implements
integrates-with
part-of
alternative-to
based-on
predecessor-of
successor-of
related-to
```

## Discovery and navigation

The index should make a large body of technical material easy to explore without overwhelming the reader.

Planned improvements:

- clearer public browsing by technology area, kind, and domain;
- fast static search with useful facets;
- related-module navigation;
- "what to learn next" navigation;
- comparison views for technologies that solve similar problems;
- curated learning journeys;
- better discovery of deep-dive modules;
- stronger mobile-friendly GitHub browsing;
- eventually, a public searchable web interface built from the same validated data.

## Module quality model

A module can mature independently:

### Overview

A concise, source-backed node that establishes identity, taxonomy, use cases, key points, and authoritative references.

### Guide

A practical explanation with a useful mental model, workflows, important concepts, tools, alternatives, and examples.

### Deep dive

A standalone technical reference that can additionally cover internals, architecture, object/data models, protocols, performance, reliability, security, ecosystem, failure modes, learning paths, and meaningful graph relationships.

See [`docs/MODULE_STANDARD.md`](docs/MODULE_STANDARD.md).

## Technology coverage

OpenDevIndex is intended to map the wider computing ecosystem, including:

- computer-science foundations;
- programming languages and runtimes;
- software engineering and architecture;
- operating systems and systems software;
- hardware and computer architecture;
- networking and internet infrastructure;
- cybersecurity, cryptography, and privacy;
- web, mobile, and desktop platforms;
- databases, storage, and data engineering;
- cloud, DevOps, infrastructure, and SRE;
- AI and machine learning;
- graphics, games, media, and XR;
- embedded systems, IoT, and robotics;
- open-source ecosystems;
- standards, protocols, and formats;
- developer tools and environments;
- testing, debugging, and performance engineering;
- distributed and large-scale systems;
- important historical and emerging technologies.

The machine-readable coverage plan exists to expose gaps and keep growth balanced. It should not encourage placeholder modules or public count chasing.

See [`docs/COVERAGE.md`](docs/COVERAGE.md).

## Search and application layer

The structured catalog should become useful beyond GitHub Markdown pages.

Planned work:

- API-friendly static catalog artifacts;
- graph-friendly exports;
- searchable web UI;
- topic comparison views;
- generated but editorially constrained learning paths;
- filters for technology kind, domain, deployment model, and coverage area;
- provenance and freshness indicators;
- change feeds for fast-moving technologies;
- translation-ready content structures where they do not weaken source traceability.

## Provenance and maintenance

Long-term usefulness depends on keeping information trustworthy after publication.

Planned work:

- stronger claim-to-source provenance where practical;
- clearer freshness rules by technology type;
- historical snapshots for fast-changing subjects;
- confidence and verification metadata;
- automated stale-source detection without treating network failures as factual invalidation;
- security/advisory-aware maintenance for sensitive modules;
- safeguards against accidental schema or content regression.

## Contribution experience

Contributors should be able to improve one useful piece of the map without understanding every repository automation detail.

Planned improvements:

- clearer templates for deepening existing modules;
- kind-specific editorial checklists;
- relationship suggestions with validation;
- source-quality guidance;
- easier preview of generated index/search changes;
- contribution paths for corrections, sources, examples, architecture explanations, and graph links—not only new modules.

## Non-goals

OpenDevIndex does **not** aim to:

- publish empty or placeholder modules to increase repository size;
- mirror proprietary documentation;
- copy upstream manuals wholesale;
- rank products based on sponsorship;
- treat generated AI text as an authoritative source;
- add relationships only to make the graph look larger;
- sacrifice accuracy, provenance, readability, or usefulness for raw content volume.

## Definition of progress

Progress should be visible when:

- an important module becomes substantially more useful to learn from;
- a reader can navigate naturally to a related technology;
- a source or factual weakness is corrected;
- search and browsing make existing knowledge easier to find;
- automation catches a real quality regression;
- a contributor can improve the project with less friction;
- an uncovered area of the technology map gains trustworthy content.

That is a better measure of OpenDevIndex than a headline branch count.
