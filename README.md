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
- **Quality-gated** — modules are included only after structure, metadata, and source checks pass.

## Knowledge modules

Knowledge modules are independently versioned using stable category/slug addresses:

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

Modules must contain real, useful information and pass validation before inclusion in the index.

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

The trusted publication pipeline is **idempotent**: it preserves modules that already exist, renders missing modules from reviewed catalog data, runs validation before publication, and does not grant publication write permission to pull requests.

See [`catalog/README.md`](catalog/README.md) and [`docs/SEEDING.md`](docs/SEEDING.md).

## Search and source health

OpenDevIndex includes reproducible tooling for turning validated catalogs into machine-readable search artifacts:

```bash
python scripts/build_index.py --catalog-dir catalog --output-dir dist/index
python scripts/search_index.py "local ai" --index dist/index/search.json
```

The generated output includes a full JSON catalog, a compact search index, and a human-readable catalog. GitHub Actions builds and smoke-tests these artifacts and publishes them as workflow artifacts for downstream tools.

A separate **Source Health** workflow checks canonical homepages, repositories, and source references on a schedule. Permanent missing-link responses fail the health check, while rate limits, anti-bot responses, and temporary network failures are reported separately to avoid turning transient external outages into false data-quality failures.

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

OpenDevIndex validates curated catalogs and individual knowledge modules in GitHub Actions. Source URLs are restricted to public HTTPS destinations, and third-party Actions used by core workflows are pinned to exact commit SHAs.

A module is included in a milestone only when its required files and metadata pass validation.

## Roadmap

- **v0.1:** 100 verified knowledge modules
- **v0.5:** 1,000 verified knowledge modules + generated search catalog
- **v1.0:** 10,000 verified knowledge modules + public searchable index

Each knowledge module is independently validated for structure, accuracy, and quality before being included in the index.

## License

MIT. Individual linked projects, names, trademarks, documentation, and source materials remain subject to their own licenses and terms.
