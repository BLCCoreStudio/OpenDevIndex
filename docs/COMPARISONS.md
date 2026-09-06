# Curated comparison views

OpenDevIndex comparison views connect mature knowledge modules that solve related problems. They are designed to answer **which architectural and operational boundary fits a requirement**, not to produce popularity rankings, synthetic scores, or universal winners.

The first comparison is `PostgreSQL vs MySQL vs SQLite`, built from the three independently maintained relational-database deep dives.

Generated public views are published under [`docs/comparisons/`](comparisons/index.md).

## Design principles

A comparison should:

- compare technologies only when the relationship is meaningful;
- use dimensions that change an engineering decision;
- prefer architecture, deployment, correctness, reliability, security, and operational trade-offs over marketing claims;
- link back to the independently versioned modules for detailed explanations and source provenance;
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

## Validation invariants

`scripts/build_comparisons.py` validates comparison manifests before rendering them.

The current invariants include:

- `schema_version` must be `1`;
- the filename must match the comparison `id`;
- every referenced module must already exist in the validated catalog;
- a comparison contains 2–6 unique modules;
- every comparison dimension must contain one value for **every** compared module;
- dimension identifiers must be unique;
- decision rules may only recommend modules already present in that comparison;
- verification dates cannot be in the future;
- text fields are bounded to keep generated views reviewable and readable.

These constraints prevent a comparison from silently omitting one technology on an inconvenient dimension or linking to placeholder/nonexistent modules.

## Build locally

Install the normal CI dependencies, then run:

```bash
python scripts/build_comparisons.py \
  --comparisons-dir comparisons \
  --catalog-dir catalog \
  --output-dir dist/comparisons
```

To render the public Markdown views as well:

```bash
python scripts/build_comparisons.py \
  --comparisons-dir comparisons \
  --catalog-dir catalog \
  --output-dir dist/comparisons \
  --public-dir docs/comparisons
```

Generated artifacts include:

```text
dist/comparisons/
├── comparisons.json
├── index.md
└── <comparison-id>.md
```

The public publisher writes the Markdown equivalents under `docs/comparisons/`.

## Machine-readable output

`comparisons.json` contains:

- comparison identity and verification date;
- the compared module references;
- module names, URLs, summaries, and reviewed maturity levels;
- normalized dimensions and per-module values;
- curated decision rules;
- editorial notes.

This gives future web interfaces, APIs, editor integrations, and learning tools a deterministic comparison payload without forcing them to parse Markdown.

## Source discipline

Comparison manifests do not duplicate the full source lists from every module. Instead they depend on the linked modules' source-backed technical claims.

When a comparison introduces a claim not already supported by the compared modules, improve the relevant module first or add the necessary primary-source support there. This keeps provenance attached to stable knowledge nodes instead of scattering evidence across generated navigation pages.

## Contribution workflow

When adding or changing a comparison:

1. confirm all compared modules already exist and are sufficiently mature for the dimensions being discussed;
2. choose decision-relevant dimensions rather than feature-count trivia;
3. update a module first if its current content cannot support the comparison claim;
4. add or update the YAML manifest under `comparisons/`;
5. run the comparison builder and unit tests;
6. review the generated Markdown for symmetry, clarity, and unsupported ranking language;
7. update `verified_at` when the comparison has actually been re-reviewed.

A good comparison should help a reader decide **what to investigate next and why**, while preserving the nuance of the underlying technologies.
