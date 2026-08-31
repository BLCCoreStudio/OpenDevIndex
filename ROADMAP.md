# OpenDevIndex Roadmap

## v0.1 — Foundation / 100 modules

- Stable entry schema v1
- CI validation for knowledge modules
- Contribution templates
- First 100 source-backed modules
- Category and duplicate checks
- Reproducible search-index generator and local search CLI
- Automated source health workflow

## v0.2 — Discovery and taxonomy / 135 modules

- Generated public `INDEX.md`
- Taxonomy v2 with stable addresses plus `kind` and `domains`
- Editorial quality scoring and source-health reporting
- Expanded language, framework, runtime, library, platform, standard, toolchain, and tool coverage

## v0.5 — Searchable / 1,000 modules

Current growth model: reviewed catalog shards published from trusted `main`. The first v0.5 core shard set contains 25 source-backed modules and establishes the reusable publisher for future batches.

- Scale from the 135-module v0.2 baseline to 1,000 validated modules
- Keep catalog batches small enough for meaningful source and editorial review
- Use the generic trusted catalog publisher for future milestone shards
- Generated global catalog
- Fast static search index
- Cross-links between related technologies
- Staleness detection based on `verified_at`
- Automated source/link health reporting
- Contributor quality dashboard
- Introduce deeper module sections for architecture, concepts, tools, examples, alternatives, risks and learning paths

## v1.0 — Open technology map / 10,000 modules

The 10,000-module destination is now represented by a machine-readable **Technology Universe** coverage plan. Its 20 major areas and allocations are validated in CI so growth stays broad instead of drifting toward whichever topic is easiest to add.

- 10,000 validated knowledge modules
- CI-validated 10,000-module coverage allocation
- Public searchable web index
- API-friendly catalog artifacts
- Topic relationships, dependencies and alternatives graph
- Technology comparison views
- Learning-path generation from prerequisites and relationships
- Security, privacy and operational-risk facets
- Trend/change feeds for fast-moving technologies
- Translation-ready content model
- Broad coverage across software, systems, infrastructure, security, AI, hardware and emerging technology

See [`docs/COVERAGE.md`](docs/COVERAGE.md) and [`coverage/technology-universe-v1.yaml`](coverage/technology-universe-v1.yaml).

## Beyond v1 — Technology knowledge graph

- Expand from a software-centric catalog into a comprehensive map of computing and technology
- Connect concepts, implementations, tools, standards, protocols, ecosystems and historical lineage
- Support graph navigation such as `built-with`, `depends-on`, `alternative-to`, `implements`, `successor-of`, `used-by` and `related-to`
- Add generated comparison matrices without vendor-sponsored ranking
- Add curated beginner-to-advanced learning journeys
- Add structured architecture and data-flow representations where appropriate
- Add stronger provenance, freshness and confidence metadata
- Add historical snapshots for fast-changing technologies
- Make the reviewed catalog reusable by websites, CLIs, educational tools and other open-source applications

## Coverage domains

OpenDevIndex is designed to include programming languages, computer-science foundations, operating systems, hardware and computer architecture, networking and internet infrastructure, cybersecurity and privacy, web and mobile development, databases and data engineering, cloud and DevOps, observability and reliability, AI and machine learning, graphics and games, embedded systems and IoT, robotics, open-source ecosystems, standards and protocols, developer tooling, software architecture, testing and debugging, supply-chain engineering, and emerging technology.

See [`docs/VISION.md`](docs/VISION.md) for the full long-term scope.

## Non-goals

- Publishing placeholder or unverified modules
- Mirroring proprietary documentation
- Ranking products based on sponsorship
- Treating generated AI text as a source
- Sacrificing accuracy, provenance or usefulness merely to increase raw content volume

Each knowledge module is independently validated for structure, accuracy, and quality before being included in the index.
