# Search and discovery artifacts

OpenDevIndex generates deterministic discovery artifacts from validated catalog, maturity, coverage, and curated comparison data.

## Build the module index

For a standalone catalog build:

```bash
python -m pip install -r requirements-ci.txt
python scripts/build_index.py --catalog-dir catalog --output-dir dist/index
```

Generated files:

- `dist/index/catalog.json` — complete public catalog data;
- `dist/index/search.json` — compact search-oriented records;
- `dist/index/catalog.md` — human-readable catalog view.

Schema v3 records expose `coverage_area` and `coverage_topics`, and the generated payload includes aggregate area/topic counts. Legacy schema v1/v2 modules remain searchable but are reported as coverage-unmapped until they receive explicit schema v3 mappings.

The index builder also joins `quality/module-maturity.yaml`, so generated records expose reviewed `overview`, `guide`, or `deep-dive` maturity independently from catalog schema versions.

The generator intentionally avoids timestamps in generated artifacts so the same validated inputs produce stable output.

## Search locally

```bash
python scripts/search_index.py "local ai" --index dist/index/search.json
python scripts/search_index.py "container" --category tool --index dist/index/search.json
python scripts/search_index.py "security" --coverage-area cybersecurity-privacy --index dist/index/search.json
python scripts/search_index.py "model" --coverage-area ai-ml --coverage-topic model-architectures --index dist/index/search.json
python scripts/search_index.py "Terraform vs OpenTofu" --index dist/index/search.json
```

Search considers module names, identifiers, categories, kinds, maturity, domains, coverage areas/topics, tags, summaries, deployment types, licensing metadata, use cases, key points, and—when the comparison reverse index is joined—curated comparison ids and titles. Results use deterministic scoring and ordering.

### Comparison-aware filters

The search CLI can query the curated-comparison graph directly:

```bash
# Every module that currently participates in at least one curated comparison
python scripts/search_index.py \
  --has-comparison \
  --index dist/index/search.json

# Exact members of one comparison, without needing a text query
python scripts/search_index.py \
  --comparison terraform-opentofu \
  --index dist/index/search.json

# Combine an exact comparison with normal text search
python scripts/search_index.py \
  "state" \
  --comparison terraform-opentofu \
  --index dist/index/search.json

# Combine comparison coverage with ordinary facets
python scripts/search_index.py \
  --has-comparison \
  --maturity deep-dive \
  --domain data \
  --index dist/index/search.json
```

`--has-comparison` returns only modules with at least one validated comparison backlink. `--comparison <id>` matches the exact normalized curated comparison id and implicitly selects only participating modules.

The positional text query remains required for ordinary searches. It becomes optional only when `--has-comparison` or `--comparison` supplies an explicit discovery constraint, which prevents an accidental empty query from dumping the whole catalog.

Comparison filters compose with existing category, kind, maturity, domain, deployment, license, and Technology Universe coverage filters. When no text query is supplied, matching modules are ordered deterministically by name/ref; when a query is supplied, normal relevance scoring still applies.

Human-readable CLI results print linked comparison titles and URLs for matching modules, while `--json` preserves the full `comparisons[]` data for downstream tooling.

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

## Join comparisons into module discovery

To produce the full discovery surface, build comparisons first and pass the generated reverse index into `build_index.py`:

```bash
python scripts/build_comparisons.py \
  --comparisons-dir comparisons \
  --catalog-dir catalog \
  --output-dir dist/comparisons

python scripts/build_index.py \
  --catalog-dir catalog \
  --output-dir dist/index \
  --comparison-index dist/comparisons/module-comparisons.json
```

When the reverse index is supplied, every generated module record gains:

- `comparison_count`;
- `comparisons[]` with comparison id, title, summary, verification date, generated path, and public URL.

Comparison ids and titles are also included in `search_text`, so searching for a comparison can surface its participating modules. The generated Markdown index adds a `Comparisons` column with direct links to the curated views.

The top-level catalog and search payloads expose `comparison_linked_module_count`, making comparison coverage observable without parsing every entry.

The comparison index is validated again at the join boundary: unknown module refs, duplicate module records, duplicate comparison ids, and noncanonical comparison paths are rejected instead of silently entering the search artifacts.

## Public discovery build

The public publisher renders comparison views first, then the comparison-aware module index:

```bash
python scripts/build_comparisons.py \
  --comparisons-dir comparisons \
  --catalog-dir catalog \
  --output-dir dist/comparisons \
  --public-dir docs/comparisons

python scripts/build_index.py \
  --catalog-dir catalog \
  --output-dir dist/index \
  --public-index INDEX.md \
  --comparison-index dist/comparisons/module-comparisons.json
```

This ordering ensures `INDEX.md`, `catalog.json`, `search.json`, and `docs/comparisons/` are derived from the same comparison state.

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
2. runs unit tests, including curated-comparison, reverse-index, comparison-join, and comparison-filter tests;
3. builds comparison-first and module-first comparison artifacts;
4. builds module catalog/search artifacts with comparison backlinks joined in;
5. builds coverage-progress artifacts;
6. audits editorial quality;
7. smoke-tests representative searches, comparison-title discovery, exact comparison membership, and comparison-coverage filtering;
8. uploads discovery, comparison, quality, and coverage output as workflow artifacts.

The **Publish Public Index** workflow uses the same build order and rebuilds `INDEX.md` plus generated `docs/comparisons/` views when their validated inputs change.

This makes the structured discovery layer suitable for GitHub browsing, future web search, APIs, editor integrations, learning tools, comparison interfaces, coverage dashboards, and other downstream clients without requiring those consumers to parse the source YAML directly or reconstruct comparison joins themselves.