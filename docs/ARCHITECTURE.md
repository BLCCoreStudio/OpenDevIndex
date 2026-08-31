# Architecture

OpenDevIndex separates the **index itself** from the **knowledge modules** it indexes.

## 1. `main` is the control plane

The default branch contains project rules, schemas, validators, contribution documentation, reviewed catalog manifests, search tooling, and CI workflows. It should stay small enough to clone and understand quickly.

## 2. Knowledge modules are independently versioned

A knowledge module uses a stable category/slug address:

```text
<category>/<slug>
```

Examples:

```text
tool/qemu
language/rust
framework/pytorch
protocol/mcp
```

A valid module contains `entry/README.md`, `entry/entry.yaml`, `entry/sources.md`, and `entry/history.md`.

This model gives each topic an independent history while keeping the control plane focused on schemas, catalogs, validation, and discovery tooling.

## 3. Machine-readable metadata

`entry/entry.yaml` is the canonical module metadata record. It includes identity, category, summary, links, tags, verification date, status, and sources.

The schema lives at `schema/entry.schema.json`. CI performs additional semantic checks such as matching the module identifier to its declared category and rejecting unsafe source URL forms.

## 4. Curated catalogs

Reviewed milestone catalogs under `catalog/` provide structured manifests for module publication and discovery. Catalog validation checks identifiers, category distribution, summaries, tags, public HTTPS references, use cases, and key points before downstream tooling can consume the data.

Cross-catalog duplicate module identifiers are rejected by the shared catalog loader.

## 5. Search artifacts

`scripts/build_index.py` converts validated catalogs into deterministic artifacts:

- `catalog.json` — full machine-readable catalog;
- `search.json` — compact records with normalized search text;
- `catalog.md` — human-readable generated catalog.

`scripts/search_index.py` provides a dependency-light local search CLI with category filtering and deterministic ranking. The **Build Search Index** workflow runs unit tests, rebuilds the artifacts, smoke-tests representative searches, and uploads the generated output for downstream consumers.

## 6. Source health

`scripts/check_source_health.py` checks canonical homepages, repositories, and source references using public-HTTPS-only network rules. Redirects are revalidated before following them, private and local destinations are blocked, and results distinguish permanent missing links from restricted or transient responses.

The **Source Health** workflow runs on trusted `main` data and on a schedule. Pull requests perform static URL validation but do not make arbitrary outbound source-health requests.

## 7. Module lifecycle

Knowledge modules may be updated when facts, releases, ownership, support, or references change. Major disputed rewrites should go through normal review before publication.

Core infrastructure uses normal branches such as `feat/*`, `fix/*`, and `docs/*` and is merged into `main` through pull requests.

## 8. Quality at scale

OpenDevIndex is designed to grow into a broad, searchable software knowledge base while keeping every module useful, source-backed, and maintainable. Empty, duplicate, placeholder, or low-value modules are invalid.
