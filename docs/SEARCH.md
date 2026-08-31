# Search index

OpenDevIndex can generate deterministic discovery artifacts from all validated catalog manifests under `catalog/`.

## Build

```bash
python -m pip install -r requirements-ci.txt
python scripts/build_index.py --catalog-dir catalog --output-dir dist/index
```

Generated files:

- `dist/index/catalog.json` — complete public catalog data;
- `dist/index/search.json` — compact search-oriented records;
- `dist/index/catalog.md` — human-readable catalog view.

Schema v3 records also expose `coverage_area` and `coverage_topics`, and the generated payload includes aggregate area/topic counts. Legacy schema v1/v2 modules remain searchable but are reported as coverage-unmapped until they receive explicit schema v3 mappings.

The generator intentionally avoids timestamps in generated artifacts so the same validated inputs produce stable output.

## Search locally

```bash
python scripts/search_index.py "local ai" --index dist/index/search.json
python scripts/search_index.py "container" --category tool --index dist/index/search.json
python scripts/search_index.py "security" --coverage-area cybersecurity-privacy --index dist/index/search.json
python scripts/search_index.py "model" --coverage-area ai-ml --coverage-topic model-architectures --index dist/index/search.json
python scripts/search_index.py "security scanning" --json --index dist/index/search.json
```

Search considers module names, identifiers, categories, kinds, domains, coverage areas/topics, tags, summaries, use cases, and key points. Results use deterministic scoring and ordering.

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
2. runs unit tests;
3. builds the search artifacts;
4. builds coverage-progress artifacts;
5. audits editorial quality;
6. smoke-tests representative queries;
7. uploads the generated discovery, quality, and coverage output as workflow artifacts.

This makes the generated catalog suitable for future web search, APIs, editor integrations, coverage dashboards, and other downstream clients without requiring those consumers to parse YAML directly.
