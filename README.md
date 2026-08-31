# OpenDevIndex

<p align="center">
  <strong>Search the technology world. Understand how it works.</strong>
</p>

<p align="center">
  <a href="INDEX.md">Browse Index</a> ·
  <a href="docs/COVERAGE.md">Technology Universe</a> ·
  <a href="docs/VISION.md">Vision</a> ·
  <a href="docs/TAXONOMY.md">Taxonomy</a> ·
  <a href="CONTRIBUTING.md">Contribute</a> ·
  <a href="ROADMAP.md">Roadmap</a>
</p>

OpenDevIndex is an open, structured, source-backed knowledge map of software, systems, hardware, AI, security, networking, infrastructure, standards, tools, open source, and emerging technology.

It is designed to go beyond a traditional awesome list, cheatsheet collection, glossary, tutorial index, or tool directory. Each subject is represented as an independently validated **knowledge module** that can explain what a technology is, why it exists, how it works, how it is built, what tools belong around it, what alternatives exist, what risks matter, and where to learn more.

## Explore the technology universe

Like a high-quality curated index, OpenDevIndex keeps the front page easy to scan. Unlike a link-only list, each area leads into independently validated knowledge modules and machine-readable relationships.

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

The first technology-universe planning envelope allocates **10,000 validated modules** across these 20 areas. The allocation is machine-readable and CI-validated; it is not a placeholder-content target. See [`coverage/technology-universe-v1.yaml`](coverage/technology-universe-v1.yaml).

## Browse the published index

The generated [`INDEX.md`](INDEX.md) is the public directory for every published knowledge module. It groups technologies by what they **are** (`kind`) and shows the domains they belong to, with direct links to independently versioned module entries.

Search artifacts are also generated for tools and applications:

```bash
python scripts/build_index.py --catalog-dir catalog --output-dir dist/index --public-index INDEX.md
python scripts/search_index.py "local ai" --index dist/index/search.json
```

## What makes it different?

- **Structured + human-readable** — every module has machine-readable metadata and a useful guide.
- **Source-backed** — important claims should point to primary or reputable sources.
- **Independently versioned** — one subject can evolve without rewriting the entire index.
- **Facet-based taxonomy** — stable module addresses are separated from canonical kinds and multi-domain classification.
- **Technology-wide scope** — programming, systems, hardware, networking, AI, security, cloud, databases, protocols, open source, developer tooling and emerging technology belong here.
- **Explain, don't just list** — modules can cover architecture, concepts, tools, examples, alternatives, trade-offs, risks, operations and learning paths.
- **Relationship-aware** — modules can express typed graph edges such as dependencies, implementations, alternatives, compatibility and historical succession.
- **Automation-friendly** — catalogs, schemas, CI and coverage manifests make the index usable by humans, scripts, search engines, educational tools and future applications.
- **Quality-gated** — modules are included only after structure, metadata, source and editorial checks pass.

## Knowledge modules

Knowledge modules are independently versioned using stable category/slug addresses:

```text
tool/git
language/rust
framework/pytorch
protocol/mcp
hardware/example-cpu
architecture/x86-64
algorithm/dijkstra
model/example-model
format/parquet
dataset/example-dataset
concept/virtualization
opensource/linux-kernel
```

A module contains:

```text
entry/
├── README.md
├── entry.yaml
├── sources.md
└── history.md
```

Modules must contain real, useful information and pass validation before inclusion in the index.

### What a mature module should answer

Where applicable, a mature module should cover:

1. What is it?
2. Why does it exist?
3. How does it work?
4. What does its architecture look like?
5. What concepts are important?
6. What technologies, standards or dependencies does it rely on?
7. What tools are commonly used with it?
8. What do practical examples look like?
9. What are its common use cases?
10. What are the important alternatives and trade-offs?
11. What are its performance characteristics and limitations?
12. What are its security and privacy risks?
13. How is it deployed, observed and maintained where relevant?
14. What ecosystem surrounds it?
15. What should someone learn before and after it?
16. What are the primary or authoritative sources?
17. When was the information last verified?
18. How does it relate to the rest of the technology graph?

Not every module needs every section. Requirements can vary by module kind while preserving a consistent experience.

### Stable addresses, taxonomy and graph relationships

Taxonomy v3 separates three concerns:

- **stable address** identifies the module without breaking existing links;
- **`kind` + `domains`** describe what the subject is and where it belongs;
- **`relationships`** connect it to other modules using typed graph edges.

For example, the legacy address `ai/tensorflow` remains valid while discovery can classify TensorFlow as a framework in AI and machine learning. A hardware module can separately point to the architecture it implements, a protocol it uses, compatible tools, alternatives, or predecessor/successor technologies.

Existing schema v1/v2 modules remain supported. New modules should use schema v3 when they need the richer technology-wide taxonomy and relationship graph.

See [`docs/TAXONOMY.md`](docs/TAXONOMY.md).

## Curated publication pipeline

The first milestone is defined in [`catalog/v0.1.yaml`](catalog/v0.1.yaml) and later catalog shards extend it toward the 1,000- and 10,000-module milestones.

Every catalog record has a stable slug, a human-written summary, tags, curated use cases, key points, and authoritative HTTPS sources. The trusted publication pipeline is **idempotent**: it preserves modules that already exist, renders missing modules from reviewed catalog data, runs validation before publication, and does not grant publication write permission to pull requests.

See [`catalog/README.md`](catalog/README.md), [`docs/SEEDING.md`](docs/SEEDING.md), and [`docs/COVERAGE.md`](docs/COVERAGE.md).

## Search and source health

OpenDevIndex includes reproducible tooling for turning validated catalogs into machine-readable search artifacts. The generated output includes a full JSON catalog, a compact search index, and the public Markdown index. Search supports taxonomy-aware fields such as kind, domains, tags, license, and deployment type.

A separate **Source Health** workflow checks canonical homepages, repositories, and source references on a schedule. Permanent missing-link responses fail the health check, while rate limits, anti-bot responses, and temporary network failures are reported separately to avoid turning transient external outages into false data-quality failures.

## Editorial quality

Catalog entries are scored against an explicit editorial rubric covering summary quality, discovery tags, source depth, use cases, key points, taxonomy metadata, canonical links, and optional licensing/deployment metadata.

The quality audit is automated in CI, while factual correctness still requires source-backed human review. Link availability alone is never treated as proof that a technical claim is correct.

See [`docs/EDITORIAL_POLICY.md`](docs/EDITORIAL_POLICY.md).

## Address prefixes

OpenDevIndex keeps legacy prefixes for compatibility and adds canonical technology-wide namespaces for new coverage.

| Prefix | Stable address scope |
| --- | --- |
| `tool/` | Developer, diagnostic and operational tools |
| `language/` | Programming languages |
| `framework/` | Frameworks, SDKs and major libraries |
| `library/` | Reusable software libraries |
| `runtime/` | Language and execution runtimes |
| `platform/` | Software and computing platforms |
| `database/` | Databases, storage and data systems |
| `protocol/` | Protocols and interoperability mechanisms |
| `standard/` | Standards and specifications |
| `system/` | Computing and software systems |
| `toolchain/` | Compilers, build and development toolchains |
| `service/` | Hosted or network-accessible technology services |
| `project/` | Major open-source or technology projects |
| `concept/` | Technical concepts and practical explainers |
| `hardware/` | Processors, accelerators and hardware technologies |
| `architecture/` | Computer, instruction-set and system architectures |
| `algorithm/` | Algorithms and computational methods |
| `model/` | AI/ML models and model families |
| `format/` | Data, media, binary and interchange formats |
| `device/` | Technology devices and device classes |
| `dataset/` | Important datasets and benchmarks |
| `technique/` | Engineering, security and computing techniques |
| `ai/` | Legacy AI-focused module addresses |
| `security/` | Legacy security-focused module addresses |
| `cloud/` | Legacy cloud/DevOps-focused module addresses |
| `opensource/` | Legacy open-source ecosystem addresses |

## Quality bar

Each knowledge module is independently validated for structure, accuracy, provenance, usefulness and quality before being included in the index.

See [CONTRIBUTING.md](CONTRIBUTING.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/VISION.md](docs/VISION.md), and [docs/COVERAGE.md](docs/COVERAGE.md).

## Validation and supply-chain hygiene

OpenDevIndex validates the technology-universe coverage manifest, curated catalogs, and individual knowledge modules in GitHub Actions. Source URLs are restricted to public HTTPS destinations, and third-party Actions used by core workflows are pinned to exact commit SHAs.

A module is included in a milestone only when its required files and metadata pass validation.

## Roadmap

- **v0.1:** 100 verified knowledge modules
- **v0.5:** 1,000 verified knowledge modules + generated search catalog
- **v1.0:** 10,000 verified knowledge modules + public searchable technology map
- **Beyond v1:** a relationship-aware technology knowledge graph spanning the computing ecosystem

See [`ROADMAP.md`](ROADMAP.md) for the detailed plan.

## License

MIT. Individual linked projects, names, trademarks, documentation, and source materials remain subject to their own licenses and terms.
