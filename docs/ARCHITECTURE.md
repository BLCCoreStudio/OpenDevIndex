# Architecture

OpenDevIndex separates the **index itself** from the **knowledge modules** it indexes.

## 1. `main` is the control plane

The default branch contains project rules, schemas, validators, contribution documentation, reviewed catalog and comparison manifests, discovery tooling, and CI workflows. It should stay small enough to clone and understand quickly.

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

It also joins independently reviewed maturity metadata from `quality/module-maturity.yaml`, so search and the public index can distinguish overview, guide, and deep-dive modules without changing stable module addresses.

`scripts/search_index.py` provides a dependency-light local search CLI with taxonomy-aware filtering and deterministic ranking. The **Build Search Index** workflow runs unit tests, rebuilds the artifacts, smoke-tests representative searches, and uploads the generated output for downstream consumers.

## 6. Curated comparison views

Comparison manifests under `comparisons/` connect existing modules across decision-relevant dimensions. They are control-plane navigation data, not new knowledge modules and not a replacement for module-level provenance.

`scripts/build_comparisons.py` validates each comparison against the current catalog and requires every dimension to cover every compared module. It joins module identity and maturity metadata, then emits deterministic artifacts:

- `comparisons.json` — machine-readable comparison payload;
- `index.md` — generated comparison directory;
- `<comparison-id>.md` — human-readable comparison view.

The CI build writes these files under `dist/comparisons/`. The public publisher writes the Markdown views under `docs/comparisons/` so they can be browsed directly on GitHub.

Comparison views deliberately avoid universal scores, sponsor rankings, and context-free benchmark claims. Technical depth and authoritative sources remain on the linked module branches. See [`COMPARISONS.md`](COMPARISONS.md).

## 7. Source health

`scripts/check_source_health.py` checks canonical homepages, repositories, and source references using public-HTTPS-only network rules. Redirects are revalidated before following them, private and local destinations are blocked, and results distinguish permanent missing links from restricted or transient responses.

The **Source Health** workflow runs on trusted `main` data and on a schedule. Pull requests perform static URL validation but do not make arbitrary outbound source-health requests.

## 8. Module lifecycle

Knowledge modules may be updated when facts, releases, ownership, support, or references change. Major disputed rewrites should go through normal review before publication.

Core infrastructure uses normal branches such as `feat/*`, `fix/*`, and `docs/*` and is merged into `main` through pull requests.

Curated comparison claims should be updated only after the linked modules are sufficiently current to support them. If a comparison exposes a missing technical distinction, deepen the relevant module first and then refresh the comparison.

## 9. Quality at scale

OpenDevIndex is designed to grow into a broad, searchable software knowledge base while keeping every module useful, source-backed, and maintainable. Empty, duplicate, placeholder, or low-value modules are invalid.

Generated discovery layers should make reviewed knowledge easier to navigate without becoming a second, weaker source of truth.
