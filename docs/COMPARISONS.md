# Curated comparison views

OpenDevIndex comparison views connect mature knowledge modules that solve related problems. They are designed to answer **which architectural and operational boundary fits a requirement**, not to produce popularity rankings, synthetic scores, or universal winners.

The current published set is generated from reviewed manifests under `comparisons/`; use [`docs/comparisons/index.md`](comparisons/index.md) for the live list. A generated [`by-module`](comparisons/by-module.md) reverse index lets readers start from a technology and discover every curated comparison that currently includes it.

## Design principles

A comparison should:

- compare technologies only when the relationship is meaningful;
- use dimensions that change an engineering decision;
- prefer architecture, deployment, correctness, reliability, security, and operational trade-offs over marketing claims;
- link back to independently versioned modules for detailed explanations and source provenance;
- avoid benchmark claims unless the benchmark context is itself reviewed and reproducible;
- avoid a numeric winner, score, or sponsor-driven recommendation;
- make version-sensitive claims explicit and keep a verification date.

Comparison views are navigation artifacts. The module remains the authoritative OpenDevIndex unit for technical depth, source lists, and editorial history.

## Manifest format

Curated manifests live in `comparisons/*.yaml`.

A minimal comparison looks like:

```yaml
schema_version: 1
id: example-comparison
title: Example A vs Example B
summary: A source-aligned comparison of two related technologies and the engineering boundaries that distinguish them.
verified_at: '2026-09-06'
modules:
  - tool/example-a
  - tool/example-b
dimensions:
  - id: deployment-model
    label: Deployment model
    values:
      tool/example-a: Runs as a local command-line tool.
      tool/example-b: Runs as a managed network service.
decision_rules:
  - condition: The workload must remain fully local and offline.
    consider: [tool/example-a]
    reason: The local tool does not require a reachable service boundary.
notes:
  - Recheck version-sensitive capabilities against the linked modules before production decisions.
```

## Manifest validation invariants

`scripts/build_comparisons.py` validates comparison manifests before rendering them.

The current invariants include:

- `schema_version` must be `1`;
- the filename must match the comparison `id`;
- every referenced module must already exist in the validated catalog;
- a comparison contains 2–6 unique modules;
- every comparison dimension contains one value for **every** compared module;
- dimension identifiers are unique;
- decision rules may recommend only modules already present in that comparison;
- verification dates cannot be in the future;
- text fields are bounded to keep generated views reviewable and readable.

These constraints prevent a comparison from silently omitting one technology on an inconvenient dimension or linking to placeholder/nonexistent modules.

## Bidirectional discovery

Comparison manifests are authored comparison-first, but discovery works in both directions.

The builder derives a reverse index automatically:

```text
comparison manifest
  -> compared modules
  -> normalized comparison record
  -> module-to-comparison reverse index
```

A module appears only once in the reverse index, with a deterministic list of every comparison that contains it. The reverse index is derived data; contributors do not maintain a second manual mapping that could drift from the comparison manifests.

This supports both navigation paths:

```text
comparison -> modules
module -> comparisons
```

A module may participate in multiple comparisons. The generated ordering is deterministic, so downstream interfaces can rely on stable output without inventing their own graph reconstruction.

## Discovery consistency validation

Once comparison, reverse-index, comparison-search, and module-search artifacts exist, `scripts/validate_comparison_discovery.py` cross-validates the complete graph.

It checks automatically that:

- `comparisons.json` and comparison `search.json` contain exactly the same comparison ids;
- compact comparison-search records preserve each comparison's title and ordered module refs;
- exact comparison-id and exact-title searches rank that comparison first;
- module search filtered by a comparison returns exactly the modules declared by that comparison;
- the derived reverse index contains exactly the modules that participate in comparisons;
- every module's comparison list has the expected deterministic membership and order;
- module-search backlinks match the reverse index and `comparison_count` exactly;
- comparison search filtered by a module returns exactly that module's containing comparisons in deterministic order;
- the top-level `comparison_linked_module_count` equals the graph-derived count.

These are graph invariants, so they apply automatically to every new comparison. CI no longer needs a hand-written assertion block for each new module/comparison pair.

## Semantic search registry

Structural consistency cannot prove that a human engineering phrase finds the intended comparison. Those expectations live in `comparisons/search-smoke.yaml`.

Example:

```yaml
schema_version: 1
cases:
  - comparison: example-comparison
    query: deployment boundary
```

The discovery validator requires **at least one semantic search case for every comparison** and verifies that the expected comparison ranks first for each query.

This separates two concerns cleanly:

```text
graph correctness
  -> derived automatically from artifacts

human search intent
  -> small reviewed semantic-case registry
```

Adding a comparison therefore requires one meaningful search phrase, not new workflow code.

## Build locally

Install the normal CI dependencies, then build the comparison views and search artifact:

```bash
python scripts/build_comparisons.py \
  --comparisons-dir comparisons \
  --catalog-dir catalog \
  --output-dir dist/comparisons

python scripts/build_comparison_search.py \
  --input dist/comparisons/comparisons.json \
  --output dist/comparisons/search.json
```

Build the comparison-aware module search index:

```bash
python scripts/build_index.py \
  --catalog-dir catalog \
  --output-dir dist/index \
  --comparison-index dist/comparisons/module-comparisons.json
```

Then validate the entire discovery graph:

```bash
python scripts/validate_comparison_discovery.py \
  --comparisons dist/comparisons/comparisons.json \
  --reverse-index dist/comparisons/module-comparisons.json \
  --comparison-search dist/comparisons/search.json \
  --module-search dist/index/search.json \
  --semantic-cases comparisons/search-smoke.yaml \
  --output dist/comparisons/discovery-validation.json
```

To render public Markdown views as well:

```bash
python scripts/build_comparisons.py \
  --comparisons-dir comparisons \
  --catalog-dir catalog \
  --output-dir dist/comparisons \
  --public-dir docs/comparisons
```

Generated comparison artifacts include:

```text
dist/comparisons/
├── comparisons.json
├── module-comparisons.json
├── search.json
├── discovery-validation.json
├── index.md
├── by-module.md
└── <comparison-id>.md
```

The public publisher writes the Markdown equivalents under `docs/comparisons/`; compact search and validation JSON remain discovery artifacts for CI and downstream clients.

## Machine-readable output

`comparisons.json` contains full curated comparison records: identity, verification date, modules, dimensions, decision rules, and notes.

`module-comparisons.json` contains the reverse discovery view: one record per compared module plus every containing comparison.

`search.json` contains compact comparison-search records built from full reviewed content.

`discovery-validation.json` records the validated comparison count, linked-module count, number of modules participating in multiple comparisons, and semantic search-case count.

All are deterministic. Future web interfaces, APIs, editor integrations, and learning tools can traverse comparisons in either direction without parsing Markdown or reconstructing joins themselves.

## Source discipline

Comparison manifests do not duplicate the full source lists from every module. Instead they depend on the linked modules' source-backed technical claims.

When a comparison introduces a claim not already supported by the compared modules, improve the relevant module first or add the necessary primary-source support there. This keeps provenance attached to stable knowledge nodes instead of scattering evidence across generated navigation pages.

## Contribution workflow

When adding or changing a comparison:

1. confirm all compared modules already exist and are sufficiently mature for the dimensions being discussed;
2. choose decision-relevant dimensions rather than feature-count trivia;
3. update a module first if its current content cannot support the comparison claim;
4. add or update the YAML manifest under `comparisons/`;
5. add at least one meaningful rank-1 query to `comparisons/search-smoke.yaml`;
6. run unit tests, comparison builds, and `validate_comparison_discovery.py`;
7. review the generated comparison page and `by-module.md` for useful bidirectional navigation;
8. update `verified_at` when the comparison has actually been re-reviewed.

A good comparison should help a reader decide **what to investigate next and why**, while preserving the nuance of the underlying technologies.