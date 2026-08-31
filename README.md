# OpenDevIndex

> **Search the software world.**

OpenDevIndex is an open, structured, source-backed index of software, developer tools, AI, security, open source, infrastructure, standards, and emerging technology.

Instead of keeping thousands of unrelated notes in one giant document, OpenDevIndex treats each subject as an independently versioned **knowledge module**.

## What makes it different?

- **Structured + human-readable** — every module has machine-readable metadata and a concise guide.
- **Source-backed** — important claims should point to primary or reputable sources.
- **Independently versioned** — one subject can evolve without rewriting the entire index.
- **Broad by design** — tools, languages, frameworks, AI, security, cloud, databases, protocols, concepts, and open-source ecosystems belong here.
- **Automation-friendly** — catalogs, schemas, and CI make the index usable by humans, scripts, search engines, and future applications.
- **Quality before branch count** — an empty ref is not a knowledge module.

## Knowledge branches

Each knowledge module lives on a dedicated branch:

```text
tool/git
tool/qemu
language/rust
framework/pytorch
ai/tensorflow
security/sigstore
cloud/kubernetes
database/postgresql
protocol/mcp
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

Branches must contain real, useful information. Empty or artificial branches are explicitly rejected by the project rules.

## v0.1 curated catalog

The first milestone is defined in [`catalog/v0.1.yaml`](catalog/v0.1.yaml):

| Category | Modules |
| --- | ---: |
| Developer tools | 20 |
| Languages | 10 |
| Frameworks | 15 |
| AI / ML | 15 |
| Security | 10 |
| Cloud / DevOps | 10 |
| Databases | 5 |
| Protocols | 5 |
| Concepts | 5 |
| Open-source ecosystems | 5 |
| **Total** | **100** |

Every catalog record has a stable slug, a human-written summary, tags, curated use cases, key points, and authoritative HTTPS sources.

The trusted seeding pipeline is **idempotent**: it skips branches that already exist, renders missing modules from the reviewed catalog, runs the entry validator before every commit, and only then pushes the branch. Pull requests never receive seed write permission.

See [`catalog/README.md`](catalog/README.md) and [`docs/SEEDING.md`](docs/SEEDING.md).

## Categories

| Prefix | Scope |
| --- | --- |
| `tool/` | Developer and software tools |
| `language/` | Programming languages and runtimes |
| `framework/` | Frameworks, SDKs and major libraries |
| `ai/` | AI models, agents, tooling and infrastructure |
| `security/` | Security, privacy and defensive technology |
| `cloud/` | Cloud, DevOps, containers and infrastructure |
| `database/` | Databases, storage and data systems |
| `protocol/` | Protocols, standards and interoperability |
| `concept/` | Technical concepts and practical explainers |
| `opensource/` | Major open-source projects and ecosystems |

## Quality bar

Every module should answer, where applicable:

1. What is it?
2. What problem does it solve?
3. Who should use it?
4. How does it work at a high level?
5. What are its common use cases?
6. What are its important characteristics and trade-offs?
7. Where are the primary sources?
8. When was the information last verified?

See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Validation and supply-chain hygiene

OpenDevIndex validates both the curated catalog and individual knowledge branches in GitHub Actions. Third-party Actions used by the core workflows are pinned to exact commit SHAs.

A branch only counts toward a milestone when its required files and metadata pass validation.

## Roadmap

- **v0.1:** 100 verified knowledge modules
- **v0.5:** 1,000 verified knowledge modules + generated search catalog
- **v1.0:** 10,000 verified knowledge modules + public searchable index

The 10,000-module goal is a **content goal, not a branch-count stunt**.

## License

MIT. Individual linked projects, names, trademarks, documentation, and source materials remain subject to their own licenses and terms.
