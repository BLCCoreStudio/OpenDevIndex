# Verification freshness

OpenDevIndex records a `verified_at` value for each catalog module so maintenance work can be prioritized from explicit provenance rather than guesswork.

The generated search index already carries that field. `scripts/freshness_report.py` turns it into a deterministic maintenance report without changing module content or treating age alone as factual invalidation.

```bash
python scripts/build_index.py --catalog-dir catalog --output-dir dist/index --public-index INDEX.md
python scripts/freshness_report.py --index dist/index/search.json --max-age-days 365
```

For reproducible CI, reviews, or historical audits, pass an explicit reference date:

```bash
python scripts/freshness_report.py \
  --index dist/index/search.json \
  --max-age-days 180 \
  --as-of 2026-09-06 \
  --json
```

The cutoff is strict: a module verified exactly `max-age-days` before the reference date is still considered within the selected freshness window. Older entries are sorted oldest first.

A stale report is a maintenance signal, not a correctness verdict. The module still needs editorial review against authoritative sources before its verification date is updated. Future-dated or malformed `verified_at` values fail closed instead of being silently accepted.
