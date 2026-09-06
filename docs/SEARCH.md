# Search and discovery artifacts

OpenDevIndex generates deterministic discovery artifacts from validated catalog, maturity, coverage, and curated comparison data.

## Build the module index

```bash
python -m pip install -r requirements-ci.txt
python scripts/build_index.py --catalog-dir catalog --output-dir dist/index
```

Generated files:

- `dist/index/catalog.json` — complete public catalog data;
- `dist/index/search.json` — compact search-oriented records;
- `dist/index/catalog.md` — human-readable catalog view.

Schema v3 records also expose `coverage_area` and `coverage_topics`, and the generated payload includes aggregate area/topic counts. Legacy schema v1/v2 modules remain searchable but are reported as coverage-unmapped until they receive explicit schema v3 mappings.

The index builder also joins `quality/module-maturity.yaml`, so generated records expose reviewed `overview`, `guide`, or `deep-dive` maturity independently from catalog schema versions.

The generator intentionally avoids timestamps in generated artifacts so the same validated inputs produce stable output.

## Search locally

```bash
python scripts/search_index.py "local ai" --index dist/index/search.json
python scripts/search_index.py "container" --category tool --index dist/index/search.json
python scripts/search_index.py "security" --coverage-area cybersecurity-privacy --index dist/index/search.json
python scripts/search_index.py "model" --coverage-area ai-ml --coverage-topic model-architectures --index dist/index/search.json
python scripts/search_index.py "security scanning" --json --index dist/index/search.json
```

Search considers module names, identifiers, categories, kinds, maturity, domains, coverage areas/topics, tags, summaries, deployment types, licensing metadata, use cases, and key points. Results use deterministic scoring and ordering.

## Build curated comparisons

Comparison manifests under `comparisons/` can be validated and rendered with:

```bash
python scripts/build_comparisons.py \
  --comparisons-dir comparisons \
  --catalog-dir catalog \
  --output-dir dist/comparisons
```

Generated files include:

- `dist/comparisons/comparisons.json` — machine-readable comparison-first payload;
- `dist/comparisons/module-comparisons.json` — reverse module-to-comparison discovery payload;
- `dist/comparisons/index.md` — comparison directory;
- `dist/comparisons/by-module.md` — every compared module mapped to its containing comparison views;
- `dist/comparisons/<comparison-id>.md` — one human-readable view per comparison.

The comparison builder validates every referenced module against the catalog and joins module maturity metadata. Every declared dimension must contain a value for every module in the comparison, preventing asymmetric generated tables.

The reverse index is derived from the same validated records, so contributors do not maintain a second manual module-to-comparison mapping. Modules and their containing comparison lists are emitted in deterministic order.

The public publisher can additionally render the Markdown set under `docs/comparisons/`:

```bash
python scripts/build_comparisons.py \
  --comparisons-dir comparisons \
  --catalog-dir catalog \
  --output-dir dist/comparisons \
  --public-dir docs/comparisons
```

Comparison artifacts are intentionally curated rather than inferred from tags or generated from arbitrary module prose. See [`COMPARISONS.md`](COMPARISONS.md) for the editorial, validation, and bidirectional-discovery model.

## Coverage progress

Coverage progress is calculated only from explicit schema v3 mappings:

```bash
python scripts/coverage_progress.py \
  --catalog-dir catalog \
  --allocation coverage/topic-allocation-v1.yaml \
  --json-output dist/coverage/coverage.json \
  --markdown-output dist/coverage/coverage.md
```

The report compares real mapped modules with the 10,000-module Technology Universe plan and emits area/topic totals, remaining capacity, and percentages. Planned slots are never counted as published modules.

## CI

The **Build Search Index** workflow:

1. validates catalog data through the shared loader;
2. runs unit tests, including curated-comparison and reverse-index tests;
3. builds module catalog and search artifacts;
4. builds comparison-first and module-first curated comparison artifacts;
5. builds coverage-progress artifacts;
6. audits editorial quality;
7. smoke-tests representative searches;
8. uploads discovery, comparison, quality, and coverage output as workflow artifacts.

The **Publish Public Index** workflow rebuilds `INDEX.md` and the generated `docs/comparisons/` Markdown views—including the module-first reverse index—when their validated inputs change.

This makes the structured discovery layer suitable for GitHub browsing, future web search, APIs, editor integrations, learning tools, comparison interfaces, coverage dashboards, and other downstream clients without requiring those consumers to parse the source YAML directly or reconstruct comparison joins themselves.