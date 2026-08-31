# OpenDevIndex

> **Search the software world.**

OpenDevIndex is an open, structured, source-backed index of software, developer tools, AI, security, open source, infrastructure, standards, and emerging technology.

Instead of keeping thousands of unrelated notes in one giant document, OpenDevIndex treats each subject as an independently versioned **knowledge module**.

## What makes it different?

- **Structured + human-readable** — every module has machine-readable metadata and a concise guide.
- **Source-backed** — important claims should point to primary or reputable sources.
- **Independently versioned** — one subject can evolve without rewriting the entire index.
- **Broad by design** — tools, languages, frameworks, AI, security, cloud, databases, protocols, concepts, and open-source projects belong here.
- **Automation-friendly** — schemas and CI make the index usable by humans, scripts, search engines, and future applications.

## Knowledge branches

Each knowledge module lives on a dedicated branch:

```text
tool/qemu
tool/docker
tool/ffmpeg
language/rust
framework/pytorch
ai/ollama
security/passkeys
protocol/mcp
concept/virtualization
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
5. What platforms or environments does it support?
6. What are the important trade-offs and alternatives?
7. Where are the primary sources?
8. When was the information last verified?

See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Roadmap

- **v0.1:** 100 verified knowledge modules
- **v0.5:** 1,000 verified knowledge modules + generated search catalog
- **v1.0:** 10,000 verified knowledge modules + public searchable index

The 10,000-module goal is a **content goal, not a branch-count stunt**: a module only counts when it passes the schema and quality checks.

## Project status

OpenDevIndex is in its foundation phase. The schema, validation pipeline, first modules, and catalog tooling are being built now.

## License

MIT. Individual linked projects, names, trademarks, documentation, and source materials remain subject to their own licenses and terms.
