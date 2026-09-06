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

The module-search CLI can query the curated-comparison graph directly:

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

- `dist/comparisons/comparisons.json` — complete machine-readable comparison records;
- `dist/comparisons/module-comparisons.json` — reverse module-to-comparison discovery payload;
- `dist/comparisons/index.md` — comparison directory;
- `dist/comparisons/by-module.md` — every compared module mapped to its containing comparison views;
- `dist/comparisons/<comparison-id>.md` — one human-readable view per comparison.

The comparison builder validates every referenced module against the catalog and joins module maturity metadata. Every declared dimension must contain a value for every module in the comparison, preventing asymmetric generated tables.

The reverse index is derived from the same validated records, so contributors do not maintain a second manual module-to-comparison mapping. Modules and their containing comparison lists are emitted in deterministic order.

## Build and search comparison records

Curated comparisons are first-class searchable objects as well as backlinks on modules. Build the compact comparison search artifact after `comparisons.json`:

```bash
python scripts/build_comparison_search.py \
  --input dist/comparisons/comparisons.json \
  --output dist/comparisons/search.json
```

`dist/comparisons/search.json` contains one compact record per curated comparison with:

- comparison id, title, summary, verification date, path, and public URL;
- module refs and names;
- dimension ids and labels;
- module/dimension/decision-rule counts;
- normalized `search_text` derived from the full reviewed comparison content.

The search text includes module summaries, dimension values, decision-rule conditions and reasons, and editorial notes. This means queries can discover comparisons through engineering trade-offs that may not appear in the title.

Examples:

```bash
# Finds Terraform vs OpenTofu through the state-security trade-off
python scripts/search_comparisons.py \
  "state encryption" \
  --index dist/comparisons/search.json

# Finds PostgreSQL vs MySQL vs SQLite through durability internals
python scripts/search_comparisons.py \
  "wal checkpoints" \
  --index dist/comparisons/search.json

# List every curated comparison containing one exact module ref
python scripts/search_comparisons.py \
  --module database/sqlite \
  --index dist/comparisons/search.json

# Combine module membership with a technical query
python scripts/search_comparisons.py \
  "encryption" \
  --module tool/opentofu \
  --index dist/comparisons/search.json
```

The comparison CLI ranks exact comparison ids/titles most strongly, then module identity, dimension identity/labels, summary, and the broader searchable technical content. `--module <ref>` is an exact normalized module-ref filter and can be used without a text query.

Like module search, comparison search is deterministic and dependency-light. `--json` exposes the complete compact search records for downstream interfaces.

## Join comparisons into module discovery

To produce the full discovery surface, build comparisons first and pass the generated reverse index into `build_index.py`:

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

When the reverse index is supplied, every generated module record gains:

- `comparison_count`;
- `comparisons[]` with comparison id, title, summary, verification date, generated path, and public URL.

Comparison ids and titles are also included in module `search_text`, so searching for a comparison can surface its participating modules. The generated Markdown index adds a `Comparisons` column with direct links to the curated views.

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

The compact comparison `search.json` is a CI/downstream discovery artifact rather than a committed public Markdown file. The public comparison pages remain generated from the same validated manifests under `docs/comparisons/`.

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
2. runs unit tests for module search, curated comparisons, reverse indexes, comparison joins/filters, and comparison search;
3. builds complete comparison records plus the compact comparison-search artifact;
4. builds module catalog/search artifacts with comparison backlinks joined in;
5. builds coverage-progress artifacts;
6. audits editorial quality;
7. smoke-tests module discovery and real comparison-search queries, including `state encryption`, `wal checkpoints`, and exact SQLite membership;
8. uploads module, comparison, quality, and coverage discovery output as workflow artifacts.

The **Publish Public Index** workflow rebuilds `INDEX.md` plus generated `docs/comparisons/` views when their validated inputs change. Comparison-search artifacts are built and tested in the discovery workflow for API/UI consumers.

This gives OpenDevIndex two complementary search surfaces:

```text
module search      -> find technologies and their comparison backlinks
comparison search  -> find curated trade-off views and their participating technologies
```

Both are deterministic outputs from the same reviewed catalog/comparison graph rather than independent databases that can drift.