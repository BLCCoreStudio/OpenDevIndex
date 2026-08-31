# Curated catalogs

OpenDevIndex catalogs are reviewable source-of-truth manifests used to publish independently versioned knowledge modules and build searchable index artifacts.

## v0.1

`v0.1.yaml` contains exactly **100 curated technologies and concepts** across ten categories. Each record provides:

- a stable category and slug;
- a concise, human-written summary;
- at least two useful tags;
- authoritative public HTTPS sources;
- curated use cases;
- curated key points.

The catalog is validated in CI before publication tooling can act on it. Pull requests never receive publication write permission; publication is allowed only after reviewed catalog data reaches `main` or through an explicit trusted workflow dispatch.

The publication process is idempotent, so rerunning it is safe for incremental milestones. The same catalog data also feeds the reproducible search-index builder and scheduled source-health checks.
