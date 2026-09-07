# Reviewed depth discovery

OpenDevIndex keeps module coverage separate from editorial depth. The reviewed-depth discovery view exposes only modules that have been explicitly classified as `guide` or `deep-dive` in `quality/module-maturity.yaml`; overview modules remain valid catalog entries and are not treated as lower quality.

## Source of truth

The generator does not infer maturity from page length, schema version, branch history, or catalog wording. It joins validated catalog records with the existing maturity manifest and uses that reviewed metadata as the only maturity source of truth.

This keeps discovery output derived and reproducible instead of introducing a second hand-maintained list of mature modules.

## Build locally

```bash
python scripts/build_depth_discovery.py \
  --catalog-dir catalog \
  --maturity-manifest quality/module-maturity.yaml \
  --output-dir dist/depth
```

The command writes:

- `dist/depth/depth.json` — machine-readable reviewed-depth records and maturity/kind/domain counts;
- `dist/depth/depth.md` — deterministic human-readable discovery view.

To render the same Markdown to a public path, pass `--public-file`:

```bash
python scripts/build_depth_discovery.py \
  --catalog-dir catalog \
  --maturity-manifest quality/module-maturity.yaml \
  --output-dir dist/depth \
  --public-file docs/depth.md
```

## Discovery fields

Each reviewed record includes the stable module ref, display name, kind, domains, maturity, review date, summary, and canonical module URL. The Markdown view groups modules by maturity and also exposes kind/domain facets with direct module links.

Output ordering is deterministic so identical validated inputs produce identical files.

## CI and publication

The **Build Search Index** workflow builds the reviewed-depth artifacts, reports guide/deep-dive counts in the Actions summary, and includes `dist/depth` in the discovery artifact bundle.

The trusted **Publish Public Index** workflow renders `docs/depth.md` from the same generator and only commits public discovery output when validated generated views actually change.

Generated public Markdown is therefore a projection of reviewed catalog and maturity data. It must not become an independent editorial source of truth.

## Editorial boundary

A module enters this view only after its maturity metadata is deliberately reviewed. Adding a module to the catalog, increasing its word count, or changing generated discovery files must never promote maturity by itself.
