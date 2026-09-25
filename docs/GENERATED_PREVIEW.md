# Preview generated index and search changes

OpenDevIndex keeps generated discovery artifacts deterministic so contributors can review the public effect of a catalog or metadata change before opening a pull request.

## Build the preview

From the repository root:

```bash
python -m pip install -r requirements-ci.txt
python scripts/validate_catalog.py catalog/v0.1.yaml
python scripts/build_index.py --catalog-dir catalog --output-dir dist/index
```

The generated preview lives under `dist/index/`:

- `catalog.json` — API-friendly public catalog records and aggregate counts.
- `search.json` — searchable records and normalized search text.
- `catalog.md` — human-readable browse/index rendering.

If your change also affects comparison metadata, first generate the comparison index using the repository's comparison tooling and pass that file to `build_index.py` with `--comparison-index` so backlinks are included in the preview.

## Review the diff

Keep generated review separate from hand-authored source changes. A useful local sequence is:

```bash
git status --short
git diff -- catalog quality comparisons docs
python scripts/build_index.py --catalog-dir catalog --output-dir dist/index
git diff --no-index /dev/null dist/index/catalog.md || true
```

For JSON artifacts, prefer structural inspection over reading minified fragments. Useful checks include:

```bash
python -m json.tool dist/index/catalog.json >/tmp/opendevindex-catalog.pretty.json
python -m json.tool dist/index/search.json >/tmp/opendevindex-search.pretty.json
```

Then inspect the records affected by your module, kind, domain, coverage area, maturity level, or comparison.

## Search the preview

Run representative queries against the generated search index:

```bash
python scripts/search_index.py "your query" --index dist/index/search.json
```

Use at least one query that should find the changed module and, when relevant, one nearby query that should not become noisier or misleading because of the change.

## What to verify

Before opening a pull request, confirm that:

- module counts and facet counts changed only when expected;
- the changed module appears under the intended kind/domain/coverage facets;
- maturity metadata is reflected correctly;
- comparison backlinks appear only for validated curated comparisons;
- search text gains only relevant terms and does not introduce accidental keyword spam;
- generated Markdown links resolve to the intended stable module address;
- rebuilding the same source state produces the same generated artifacts.

Generated output is a review aid, not a replacement for source review. The catalog, schemas, maturity metadata, comparison definitions, and module sources remain the authoritative inputs.
