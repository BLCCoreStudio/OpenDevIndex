# Scaling OpenDevIndex

OpenDevIndex grows through reviewed catalog shards rather than placeholder branches or bulk-generated names.

## Sharded catalogs

Large milestones are divided into small `catalog/v*-*.yaml` files. A shard should remain small enough to review sources, summaries, taxonomy, use cases, and key points without turning a pull request into an unreviewable data dump.

Every shard is checked together with every other catalog. Duplicate module addresses are rejected globally before publication.

## Publication model

Catalog changes are reviewed on an ordinary feature branch with read-only CI. Knowledge-module branches are created only after reviewed catalog data reaches trusted `main`.

The generic catalog publisher:

1. selects only trusted future-milestone catalog files;
2. validates each catalog and the shared taxonomy;
3. renders each missing module in an isolated temporary worktree;
4. runs the normal module validator before creating a commit;
5. pushes the validated commit to the module's stable branch address;
6. skips existing branches by default, making publication idempotent.

Pull-request code never receives the write permission used for module publication.

Legacy v0.1 and v0.2 catalogs retain their existing dedicated publishers. New milestones use `.github/workflows/publish-catalogs.yml`.

## Quality before quantity

A module counts only when it has useful human-readable content, structured metadata, authoritative sources, taxonomy facets, and successful validation. Branch count is a storage/versioning consequence of the architecture, not the quality metric.

The editorial audit continues to score every catalog entry, and source-health checks remain separate from factual verification: a reachable URL does not by itself prove a technical claim.

## Milestone progression

- v0.1 established 100 validated modules.
- v0.2 expanded discovery, taxonomy, and coverage to 135 indexed modules.
- v0.5 grows toward 1,000 modules through repeated reviewed shards, beginning with five 5-module core shards.
- v1.0 targets 10,000 validated modules plus the public software map.

This approach keeps growth reproducible, reviewable, reversible, and useful even at much larger catalog sizes.
