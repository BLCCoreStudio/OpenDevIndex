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

The generator intentionally avoids timestamps in generated artifacts so the same validated inputs produce stable output.

## Search locally

```bash
python scripts/search_index.py "local ai" --index dist/index/search.json
python scripts/search_index.py "container" --category tool --index dist/index/search.json
python scripts/search_index.py "security scanning" --json --index dist/index/search.json
```

Search considers module names, identifiers, categories, tags, summaries, use cases, and key points. Results use deterministic scoring and ordering.

## CI

The **Build Search Index** workflow:

1. validates catalog data through the shared loader;
2. runs unit tests;
3. builds the search artifacts;
4. smoke-tests representative queries;
5. uploads the generated output as a workflow artifact.

This makes the generated catalog suitable for future web search, APIs, editor integrations, and other downstream clients without requiring those consumers to parse YAML directly.
