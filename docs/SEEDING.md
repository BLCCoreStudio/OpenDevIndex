# Knowledge module publication

OpenDevIndex publishes curated records as independently versioned knowledge modules. A module is included only after its generated entry passes the same repository validation rules used for manually maintained content.

## Safety model

1. Curated catalog changes are reviewed through a normal pull request.
2. CI validates category distribution, slugs, summaries, tags, public HTTPS sources, use cases, and key points.
3. The publication workflow is never triggered by `pull_request` and requests `contents: write` only on trusted `main` execution.
4. Existing modules are preserved during incremental publication.
5. Each missing module is rendered into a temporary Git worktree based on `origin/main`.
6. `scripts/validate_entry.py` runs before publication.
7. Each published module receives one focused commit containing its `entry/` content plus the shared core files inherited from `main`.

## Scaling

Milestones grow through reviewed catalogs, deterministic identifiers, source quality checks, and repeatable validation:

- v0.1 — 100 modules
- v0.5 — 1,000 modules
- v1.0 — 10,000 modules

Future catalogs should preserve deterministic slugs, authoritative sources, idempotent publication, and compatibility with the generated search index.
