# Curated comparison coverage

OpenDevIndex tracks how many reviewed **deep-dive modules** participate in at least one curated comparison.

This is a discovery-depth metric. It is **not** a target to force every module into a comparison and it must not be used to justify artificial graph edges.

## What is measured

The denominator is every module whose reviewed maturity in `quality/module-maturity.yaml` is `deep-dive`.

A deep-dive counts as comparison-linked when its generated module-search record contains at least one validated curated comparison backlink.

Conceptually:

```text
deep-dive comparison coverage
  = deep dives linked to >= 1 curated comparison
    / all reviewed deep dives
```

Overview and guide modules do not affect this metric.

A module that appears in two or more comparisons still counts once in the numerator. Multi-comparison membership is tracked separately by the comparison discovery validator.

## Generated outputs

`scripts/build_comparison_coverage.py` derives coverage from the generated module search index and writes:

```text
dist/comparisons/coverage.json
dist/comparisons/coverage.md
```

The public publisher also writes:

```text
docs/comparisons/coverage.md
```

and annotates:

- `INDEX.md` with the current deep-dive coverage ratio and unlinked deep-dive refs;
- `docs/comparisons/index.md` with a direct link to the coverage report;
- generated `catalog.json` and `search.json` with a top-level `comparison_coverage` object.

The JSON object contains:

```text
schema_version
deep_dive_total
deep_dive_linked
deep_dive_unlinked
deep_dive_coverage_percent
linked_deep_dive_refs
unlinked_deep_dive_refs
```

Lists are deterministic and sorted by stable module ref.

## Why calculate from generated module search

Comparison membership already flows through a validation chain:

```text
comparison manifests
  -> full comparison records
  -> reverse module/comparison index
  -> comparison-aware module search records
```

Coverage is calculated after that graph has been validated. This avoids maintaining another hand-written list of linked modules.

The coverage builder also verifies that each deep-dive record's `comparison_count` agrees with the actual `comparisons[]` array before using it.

## How to interpret unlinked deep dives

An unlinked deep dive is a **discovery opportunity**, not a content defect.

Good reasons to leave a deep dive unlinked include:

- no sufficiently mature comparison partner exists yet;
- the obvious relationship would be superficial rather than decision-relevant;
- a future comparison needs another module to be deepened first;
- the module is primarily foundational and a comparison would teach less than its existing graph relationships.

A new comparison is justified only when it clarifies a real boundary such as:

- architecture or execution model;
- lifecycle ownership;
- deployment boundary;
- compatibility or migration;
- storage or consistency model;
- security or trust boundary;
- operational failure and recovery;
- complementary versus substitutable roles.

## Local build

After generating comparison-aware module search artifacts:

```bash
python scripts/build_comparison_coverage.py \
  --module-search dist/index/search.json \
  --output-json dist/comparisons/coverage.json \
  --output-markdown dist/comparisons/coverage.md \
  --catalog-json dist/index/catalog.json \
  --search-json dist/index/search.json \
  --catalog-markdown dist/index/catalog.md
```

The public publisher additionally passes `INDEX.md`, `docs/comparisons/coverage.md`, and `docs/comparisons/index.md` so GitHub browsing receives the same metric.

## Editorial rule

Never add a low-value comparison merely to increase the percentage.

The useful signal is not whether coverage reaches 100%. The useful signal is whether important deep-dive modules have meaningful decision-oriented navigation where such a comparison genuinely helps a reader.