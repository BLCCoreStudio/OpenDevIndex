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
- `dist/index/search.json` — compact module-search records;
- `dist/index/catalog.md` — human-readable catalog view.

Schema v3 records expose `coverage_area` and `coverage_topics`, and the generated payload includes aggregate area/topic counts. Legacy schema v1/v2 modules remain searchable but are reported as coverage-unmapped until they receive explicit schema v3 mappings.

The index builder also joins `quality/module-maturity.yaml`, so generated records expose reviewed `overview`, `guide`, or `deep-dive` maturity independently from catalog schema versions.

The generator intentionally avoids timestamps in generated artifacts so the same validated inputs produce stable output.

## Search modules locally

```bash
python scripts/search_index.py "local ai" --index dist/index/search.json
python scripts/search_index.py "container" --category tool --index dist/index/search.json
python scripts/search_index.py "security" --coverage-area cybersecurity-privacy --index dist/index/search.json
python scripts/search_index.py "model" --coverage-area ai-ml --coverage-topic model-architectures --index dist/index/search.json
python scripts/search_index.py "Terraform vs OpenTofu" --index dist/index/search.json
```

Module search considers names, identifiers, categories, kinds, maturity, domains, coverage areas/topics, tags, summaries, deployment types, licensing metadata, use cases, key points, and—when the comparison reverse index is joined—curated comparison ids and titles. Results use deterministic scoring and ordering.

### Comparison-aware module filters

```bash
# Every module that participates in at least one curated comparison
python scripts/search_index.py \
  --has-comparison \
  --index dist/index/search.json

# Exact members of one comparison
python scripts/search_index.py \
  --comparison terraform-opentofu \
  --index dist/index/search.json

# Combine comparison membership with text search
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

`--has-comparison` returns only modules with at least one validated comparison backlink. `--comparison <id>` matches an exact normalized curated comparison id.

The positional text query remains required for ordinary searches. It becomes optional only when `--has-comparison` or `--comparison` supplies an explicit discovery constraint, preventing an accidental empty query from dumping the whole catalog.

Comparison filters compose with category, kind, maturity, domain, deployment, license, and Technology Universe coverage filters. Human-readable results print linked comparison titles/URLs; JSON mode preserves the full `comparisons[]` records.

## Build curated comparisons

```bash
python scripts/build_comparisons.py \
  --comparisons-dir comparisons \
  --catalog-dir catalog \
  --output-dir dist/comparisons
```

Generated files include:

- `dist/comparisons/comparisons.json` — complete machine-readable comparison records;
- `dist/comparisons/module-comparisons.json` — reverse module-to-comparison discovery payload;
- `dist/comparisons/index.md` — comparison directory;
- `dist/comparisons/by-module.md` — compared modules mapped to containing comparisons;
- `dist/comparisons/<comparison-id>.md` — one human-readable view per comparison.

Only top-level `comparisons/*.yaml` files are comparison manifests. Supporting discovery metadata, including semantic-search cases, lives under `comparisons/_meta/` so it cannot be mistaken for a comparison record by the builder.

The comparison builder validates every referenced module against the catalog and joins module maturity metadata. Every declared dimension must contain a value for every module in the comparison.

The reverse index is derived from the same validated records, so contributors do not maintain a second manual module-to-comparison mapping.

## Build and search comparison records

Curated comparisons are first-class searchable objects as well as backlinks on modules:

```bash
python scripts/build_comparison_search.py \
  --input dist/comparisons/comparisons.json \
  --output dist/comparisons/search.json
```

`dist/comparisons/search.json` contains one compact record per comparison with id, title, summary, verification date, path/URL, module refs/names, dimension ids/labels, counts, and normalized `search_text` derived from reviewed comparison content.

The search text includes module summaries, dimension values, decision-rule conditions/reasons, and notes, so engineering phrases can discover a comparison even when they are absent from its title.

Examples:

```bash
python scripts/search_comparisons.py \
  "state encryption" \
  --index dist/comparisons/search.json

python scripts/search_comparisons.py \
  "wal checkpoints" \
  --index dist/comparisons/search.json

python scripts/search_comparisons.py \
  --module database/sqlite \
  --index dist/comparisons/search.json

python scripts/search_comparisons.py \
  "encryption" \
  --module tool/opentofu \
  --index dist/comparisons/search.json
```

The comparison CLI ranks exact ids/titles most strongly, then module identity, dimension identity/labels, summary, and broader reviewed technical content. `--module <ref>` is an exact normalized module-ref filter and may be used without a text query.

## Join comparisons into module discovery

Build comparisons and their compact search artifact before the module index:

```bash
python scripts/build_comparisons.py \
  --comparisons-dir comparisons \
  --catalog-dir catalog \
  --output-dir dist/comparisons

python scripts/build_comparison_search.py \
  --input dist/comparisons/comparisons.json \
  --output dist/comparisons/search.json

python scripts/build_index.py \
  --catalog-dir catalog \
  --output-dir dist/index \
  --comparison-index dist/comparisons/module-comparisons.json
```

When the reverse index is supplied, every generated module record gains `comparison_count` plus `comparisons[]` with comparison id, title, summary, verification date, generated path, and public URL.

Comparison ids and titles also enter module `search_text`, and the generated Markdown index adds a direct `Comparisons` column. The top-level catalog/search payloads expose `comparison_linked_module_count`.

The comparison index is revalidated at the join boundary: unknown module refs, duplicate records/ids, and noncanonical paths are rejected instead of silently entering discovery artifacts.

## Validate the complete comparison discovery graph

After all comparison and module search artifacts are built, run:

```bash
python scripts/validate_comparison_discovery.py \
  --comparisons dist/comparisons/comparisons.json \
  --reverse-index dist/comparisons/module-comparisons.json \
  --comparison-search dist/comparisons/search.json \
  --module-search dist/index/search.json \
  --semantic-cases comparisons/_meta/search-smoke.yaml \
  --output dist/comparisons/discovery-validation.json
```

The validator derives expected membership directly from `comparisons.json` and cross-checks it against every discovery surface. It verifies:

- comparison/search id parity;
- compact search record module identity;
- exact id/title ranking;
- comparison -> module membership through module search;
- module -> comparison membership through the reverse index and comparison search;
- deterministic ordering for modules that appear in multiple comparisons;
- `comparison_count` backlinks in module search;
- the top-level comparison-linked module count.

Human search intent is kept separately in `comparisons/_meta/search-smoke.yaml`. Every comparison must have at least one reviewed query whose expected comparison ranks first. This avoids hard-coding comparison-specific shell/Python assertions into the GitHub Actions workflow.

Successful validation writes `dist/comparisons/discovery-validation.json` with comparison, linked-module, multi-comparison-module, and semantic-case counts.

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

Compact comparison search and discovery-validation JSON are CI/downstream artifacts rather than committed public Markdown. Public comparison pages remain generated under `docs/comparisons/` from the same reviewed manifests.

See [`COMPARISONS.md`](COMPARISONS.md) for the editorial, bidirectional-discovery, semantic-search, and validation model.

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

1. runs unit tests for module search, curated comparisons, reverse indexes, joins/filters, comparison search, and discovery validation;
2. builds full comparison records and the compact comparison-search artifact;
3. builds module catalog/search artifacts with comparison backlinks joined in;
4. runs the generic comparison discovery validator against all generated graph surfaces;
5. executes every semantic rank-1 query registered in `comparisons/_meta/search-smoke.yaml`;
6. builds coverage-progress artifacts and audits editorial quality;
7. smoke-tests representative non-comparison module facets;
8. uploads module, comparison, validation, quality, and coverage discovery output as workflow artifacts.

The **Publish Public Index** workflow rebuilds `INDEX.md` plus generated `docs/comparisons/` views when their validated inputs change.

OpenDevIndex therefore exposes two complementary deterministic search surfaces:

```text
module search      -> technologies + comparison backlinks
comparison search  -> curated trade-off views + participating technologies
```

A separate end-to-end validator ensures those surfaces remain one consistent graph rather than drifting independent indexes.