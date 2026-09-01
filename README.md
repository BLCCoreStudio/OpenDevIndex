# OpenDevIndex

<p align="center">
  <strong>Search the technology world. Understand how it works.</strong>
</p>

<p align="center">
  An open, source-backed knowledge map for software, systems, hardware, AI, security, networking, infrastructure, standards, tools, open source, and emerging technology.
</p>

<p align="center">
  <a href="INDEX.md">Browse the Index</a> ·
  <a href="docs/COVERAGE.md">Explore Technology Areas</a> ·
  <a href="docs/MODULE_STANDARD.md">Module Standard</a> ·
  <a href="CONTRIBUTING.md">Contribute</a> ·
  <a href="ROADMAP.md">Roadmap</a>
</p>

---

## More than a list of links

OpenDevIndex is built to answer the question that ordinary directories usually stop before:

> **What is this technology, how does it actually work, what belongs around it, what are the trade-offs, and what should I learn next?**

Each subject is an independently maintained **knowledge module** with structured metadata, authoritative sources, taxonomy, verification history, and—where useful—typed relationships to other technologies.

A module can grow from a concise source-backed overview into a full technical deep dive without changing its stable address.

## Start exploring

The generated [`INDEX.md`](INDEX.md) is the main directory. It groups modules by what they are and shows the domains they belong to.

A few examples:

- **[Git](https://github.com/BLCCoreStudio/OpenDevIndex/tree/tool/git/entry)** — flagship deep dive into Git's object model, index, refs, branching, merging, rebasing, packfiles, protocols, performance, recovery, and security boundaries.
- **[Git LFS](https://github.com/BLCCoreStudio/OpenDevIndex/tree/tool/git-lfs/entry)** — large-file workflows around Git.
- **[Docker](https://github.com/BLCCoreStudio/OpenDevIndex/tree/tool/docker/entry)** — container development and packaging workflows.
- **[PyTorch](https://github.com/BLCCoreStudio/OpenDevIndex/tree/framework/pytorch/entry)** — machine-learning framework coverage.
- **[x86-64](https://github.com/BLCCoreStudio/OpenDevIndex/tree/architecture/x86-64/entry)** — computer-architecture coverage using the richer schema-v3 model.
- **[JSON](https://github.com/BLCCoreStudio/OpenDevIndex/tree/format/json/entry)** and **[Apache Parquet](https://github.com/BLCCoreStudio/OpenDevIndex/tree/format/parquet/entry)** — data-format modules mapped into the technology universe.

The goal is not to produce the longest possible list. The goal is to make every useful click lead somewhere worth reading.

## What a mature module teaches

Depending on the subject, a mature OpenDevIndex module can cover:

- what the technology is and why it exists;
- how it works and what its internal architecture looks like;
- the important concepts, objects, protocols, components, or data structures;
- common workflows, commands, APIs, and practical examples;
- tools and integrations commonly used with it;
- alternatives and meaningful trade-offs;
- performance characteristics and scaling limits;
- reliability concerns and common failure modes;
- security and privacy boundaries;
- common mistakes and operational pitfalls;
- ecosystem and interoperability;
- beginner-to-advanced learning paths;
- authoritative sources and verification date;
- related OpenDevIndex modules and sensible next topics.

See [`docs/MODULE_STANDARD.md`](docs/MODULE_STANDARD.md) for the full editorial standard.

## Depth without placeholder content

OpenDevIndex separates **coverage** from **depth**.

An overview module can establish a trustworthy node in the map. Important technologies are then progressively upgraded into guides and deep dives. This lets the project broaden its technology coverage without pretending that a one-paragraph entry is a finished learning resource.

The project deliberately avoids:

- empty pages created only to increase counts;
- copied marketing descriptions;
- giant command dumps without explanation;
- AI-generated text treated as a source;
- fake rankings or sponsor-driven recommendations;
- graph edges created only to make the graph look denser.

## A connected technology map

Technology is easier to understand when subjects are connected rather than isolated.

Taxonomy v3 separates three ideas:

1. a **stable module address**, such as `tool/git`;
2. semantic facets such as **kind** and **domains**;
3. typed **relationships** between modules.

Relationships can express ideas such as:

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

This makes it possible to move naturally from a tool to the protocol it implements, the libraries it depends on, alternatives worth comparing, related standards, or the next concept in a learning path.

## Explore by technology area

The Technology Universe coverage map keeps growth broad across computing rather than clustering around whatever happens to be easiest to add.

- [Computer Science Foundations](docs/COVERAGE.md#computer-science-foundations)
- [Programming Languages and Runtimes](docs/COVERAGE.md#programming-languages-and-runtimes)
- [Software Engineering and Architecture](docs/COVERAGE.md#software-engineering-and-architecture)
- [Operating Systems and Systems Software](docs/COVERAGE.md#operating-systems-and-systems-software)
- [Hardware and Computer Architecture](docs/COVERAGE.md#hardware-and-computer-architecture)
- [Networking and Internet Infrastructure](docs/COVERAGE.md#networking-and-internet-infrastructure)
- [Cybersecurity, Cryptography and Privacy](docs/COVERAGE.md#cybersecurity-cryptography-and-privacy)
- [Web Platforms and Development](docs/COVERAGE.md#web-platforms-and-development)
- [Mobile and Desktop Computing](docs/COVERAGE.md#mobile-and-desktop-computing)
- [Databases, Storage and Data Engineering](docs/COVERAGE.md#databases-storage-and-data-engineering)
- [Cloud, DevOps, Infrastructure and SRE](docs/COVERAGE.md#cloud-devops-infrastructure-and-sre)
- [Artificial Intelligence and Machine Learning](docs/COVERAGE.md#artificial-intelligence-and-machine-learning)
- [Graphics, Games, Media and XR](docs/COVERAGE.md#graphics-games-media-and-xr)
- [Embedded Systems, IoT and Robotics](docs/COVERAGE.md#embedded-systems-iot-and-robotics)
- [Open Source Ecosystems](docs/COVERAGE.md#open-source-ecosystems)
- [Standards, Protocols and Formats](docs/COVERAGE.md#standards-protocols-and-formats)
- [Developer Tools and Environments](docs/COVERAGE.md#developer-tools-and-environments)
- [Testing, Debugging and Performance Engineering](docs/COVERAGE.md#testing-debugging-and-performance-engineering)
- [Distributed and Large-Scale Systems](docs/COVERAGE.md#distributed-and-large-scale-systems)
- [Emerging and Historical Technology](docs/COVERAGE.md#emerging-and-historical-technology)

The coverage model is a planning and quality-control tool—not a public race to inflate repository size.

## How modules are organized

Knowledge modules use stable category/slug addresses and live on independently versioned branches:

```text
tool/git
language/rust
framework/pytorch
protocol/mcp
architecture/x86-64
format/parquet
concept/virtualization
```

A module contains:

```text
entry/
├── README.md      # human-readable knowledge page
├── entry.yaml     # machine-readable metadata
├── sources.md     # provenance and authoritative references
└── history.md     # verification and editorial history
```

Independent module branches let one subject evolve without rewriting the entire index while preserving stable links.

## Searchable by humans and tools

OpenDevIndex generates machine-readable search artifacts alongside the public Markdown directory.

```bash
python scripts/build_index.py --catalog-dir catalog --output-dir dist/index --public-index INDEX.md
python scripts/search_index.py "local ai" --index dist/index/search.json
```

Search can use taxonomy-aware fields including kind, domains, tags, deployment type, licensing metadata, and Technology Universe coverage facets.

The structured model is intended to work for:

- people browsing on GitHub;
- local search and CLI tools;
- future web interfaces;
- educational and learning-path tools;
- technology comparison views;
- graph exploration;
- other open-source applications that need a reviewed technology catalog.

## Quality and provenance

Every published module is expected to be source-backed and independently validatable.

Core quality controls include:

- schema validation;
- taxonomy validation;
- source URL safety checks;
- source-health monitoring;
- editorial quality scoring;
- duplicate and category checks;
- Technology Universe coverage validation;
- relationship validation for schema-v3 graph edges;
- pinned third-party GitHub Actions in core workflows.

Automated checks can validate structure and source reachability. They do **not** replace factual editorial review.

Primary and authoritative sources are preferred: official documentation, standards, canonical repositories, original research, and security advisories.

## Publication model

Reviewed catalogs on trusted `main` drive reproducible module publication. The publisher is idempotent and validation-gated.

Curated deep-dive modules are protected from accidental automatic replacement, and an older catalog cannot silently downgrade a newer module schema. Intentional replacement requires an explicit override.

This is important because OpenDevIndex treats hand-curated depth as durable project content rather than disposable generated output.

## Contributing

Useful contributions include much more than adding a new technology name.

You can help by:

- deepening an existing overview;
- correcting an inaccurate explanation;
- adding authoritative sources;
- documenting architecture or internal concepts;
- improving examples and workflows;
- connecting related technologies with meaningful graph edges;
- documenting alternatives and trade-offs;
- improving security, reliability, or performance coverage;
- proposing a missing technology that fills a real coverage gap.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`docs/EDITORIAL_POLICY.md`](docs/EDITORIAL_POLICY.md).

## Project principles

- **Explain, don't just list.**
- **Prefer primary sources.**
- **Stable links matter.**
- **Depth and coverage are separate quality dimensions.**
- **Relationships should teach something.**
- **Automation should protect curated work, not overwrite it.**
- **No placeholder-content races.**
- **No sponsored rankings.**

## Documentation

- [`docs/MODULE_STANDARD.md`](docs/MODULE_STANDARD.md) — module depth and editorial expectations
- [`docs/COVERAGE.md`](docs/COVERAGE.md) — technology-area coverage model
- [`docs/TAXONOMY.md`](docs/TAXONOMY.md) — stable addresses, kinds, domains, and relationships
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — repository and publication architecture
- [`docs/EDITORIAL_POLICY.md`](docs/EDITORIAL_POLICY.md) — quality rules
- [`docs/SEARCH.md`](docs/SEARCH.md) — generated search artifacts
- [`docs/SOURCE_HEALTH.md`](docs/SOURCE_HEALTH.md) — source monitoring
- [`docs/VISION.md`](docs/VISION.md) — long-term scope
- [`ROADMAP.md`](ROADMAP.md) — development direction

## License

MIT. Individual linked projects, names, trademarks, documentation, specifications, and source materials remain subject to their own licenses and terms.
