# Curated catalogs

OpenDevIndex catalogs are reviewable source-of-truth manifests used to create independently versioned knowledge branches.

## v0.1

`v0.1.yaml` contains exactly **100 curated technologies and concepts** across ten categories. Each record provides:

- a stable category and slug;
- a concise, human-written summary;
- at least two useful tags;
- authoritative HTTPS sources;
- curated use cases;
- curated key points.

The catalog itself is validated in CI before any seed workflow can create branches. Pull requests never receive write permission for seeding. Branch creation is allowed only after the catalog reaches `main` or through an explicit workflow dispatch.

The generator skips existing branches, so rerunning it is idempotent and safe for incremental milestones.
