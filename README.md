# OpenDevIndex

> **Search the software world.**

OpenDevIndex is an open, structured, source-backed index of software, developer tools, AI, security, open source, infrastructure, standards, and emerging technology.

Instead of keeping thousands of unrelated notes in one giant document, OpenDevIndex treats each subject as an independently versioned **knowledge module**.

## Browse the index

The generated [`INDEX.md`](INDEX.md) is the public directory for discovering every published knowledge module. It groups technologies by what they **are** (`kind`) and shows the domains they belong to, with direct links to the independently versioned module entries.

Search artifacts are also generated for tools and applications:

```bash
python scripts/build_index.py --catalog-dir catalog --output-dir dist/index --public-index INDEX.md
python scripts/search_index.py "local ai" --index dist/index/search.json
```

## What makes it different?

- **Structured + human-readable** — every module has machine-readable metadata and a concise guide.
- **Source-backed** — important claims should point to primary or reputable sources.
- **Independently versioned** — one subject can evolve without rewriting the entire index.
- **Facet-based taxonomy** — stable module addresses are separated from canonical kinds and multi-domain classification.
- **Broad by design** — tools, languages, frameworks, AI, security, cloud, databases, protocols, concepts, and open-source ecosystems belong here.
- **Automation-friendly** — catalogs, schemas, and CI make the index usable by humans, scripts, search engines, and future applications.
- **Quality-gated** — modules are included only after structure, metadata, source, and editorial checks pass.

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

### Stable addresses vs. taxonomy

The address prefix is a stable compatibility identifier, not the only classification of a technology. Taxonomy v2 adds two discovery facets:

- **`kind`** answers *what is it?* — for example `framework`, `runtime`, `library`, `service`, `protocol`, or `platform`.
- **`domains`** answers *where does it belong?* — for example `ai`, `security`, `cloud`, `data`, `observability`, `systems`, or `web`.

For example, the legacy address `ai/tensorflow` remains valid, while the search index classifies TensorFlow as `kind: framework` with `domains: [ai, machine-learning]`. This keeps existing links stable without forcing ambiguous technologies into one-dimensional categories.

See [`docs/TAXONOMY.md`](docs/TAXONOMY.md).

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

OpenDevIndex includes reproducible tooling for turning validated catalogs into machine-readable search artifacts. The generated output includes a full JSON catalog, a compact search index, and the public Markdown index. Search supports taxonomy-aware fields such as kind, domains, tags, license, and deployment type.

A separate **Source Health** workflow checks canonical homepages, repositories, and source references on a schedule. Permanent missing-link responses fail the health check, while rate limits, anti-bot responses, and temporary network failures are reported separately to avoid turning transient external outages into false data-quality failures.

## Editorial quality

Catalog entries are scored against an explicit editorial rubric covering summary quality, discovery tags, source depth, use cases, key points, taxonomy metadata, canonical links, and optional licensing/deployment metadata.

The quality audit is automated in CI, while factual correctness still requires source-backed human review. Link availability alone is never treated as proof that a technical claim is correct.

See [`docs/EDITORIAL_POLICY.md`](docs/EDITORIAL_POLICY.md).

## Address prefixes

| Prefix | Stable address scope |
| --- | --- |
| `tool/` | Developer and software tools |
| `language/` | Programming languages and runtimes |
| `framework/` | Frameworks, SDKs and major libraries |
| `ai/` | Legacy AI-focused module addresses |
| `security/` | Legacy security-focused module addresses |
| `cloud/` | Legacy cloud/DevOps-focused module addresses |
| `database/` | Databases, storage and data systems |
| `protocol/` | Protocols, standards and interoperability |
| `concept/` | Technical concepts and practical explainers |
| `opensource/` | Major open-source projects and ecosystems |

New modules use canonical taxonomy metadata even when a stable address prefix is retained for compatibility.

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
