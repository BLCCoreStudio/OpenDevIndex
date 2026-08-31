# Contributing to OpenDevIndex

OpenDevIndex is a structured, source-backed index of software, developer tools, AI, security, open source, infrastructure, standards, and emerging technology.

## Core principle

Every knowledge module must be useful on its own, backed by authoritative references, and understandable without relying on hidden context.

## Module identifiers

Use one of these stable category/slug forms:

- `tool/<slug>`
- `language/<slug>`
- `framework/<slug>`
- `ai/<slug>`
- `security/<slug>`
- `cloud/<slug>`
- `database/<slug>`
- `protocol/<slug>`
- `concept/<slug>`
- `opensource/<slug>`

Examples: `tool/qemu`, `language/rust`, `framework/pytorch`, `protocol/mcp`.

## Required module files

Each independently versioned module contains:

- `entry/README.md` — human-readable overview
- `entry/entry.yaml` — machine-readable metadata
- `entry/sources.md` — primary and high-quality references
- `entry/history.md` — notable milestones and changes

## Quality rules

1. Do not publish placeholder or low-value modules.
2. Do not copy marketing text as documentation.
3. Prefer primary sources and official documentation.
4. Use public HTTPS references; local, private-network, or credential-bearing URLs are rejected.
5. Separate facts from opinions.
6. Include alternatives and trade-offs where useful.
7. Mark rapidly changing information with a verification date.
8. Keep entries concise enough to scan but detailed enough to teach.

## Local checks

Before opening a pull request that changes core tooling or catalogs, run:

```bash
python -m pip install -r requirements-ci.txt
python -m unittest discover -s tests -v
python scripts/validate_catalog.py catalog/v0.1.yaml
python scripts/build_index.py --catalog-dir catalog --output-dir dist/index
python scripts/search_index.py "your query" --index dist/index/search.json
```

Network source-health checks run separately in GitHub Actions so pull requests do not make arbitrary outbound requests.

## Pull requests

Changes to the core schema, automation, catalog data, search tooling, or project documentation belong in normal feature branches and pull requests. Independently versioned knowledge modules should remain understandable and maintainable over time.

## Long-term goal

Build a broad, searchable, verified software knowledge index without sacrificing accuracy, source quality, or maintainability.

Each knowledge module is independently validated for structure, accuracy, and quality before being included in the index.
