# Knowledge branch seeding

OpenDevIndex treats branch count as an implementation detail, not the quality metric. A branch counts as a knowledge module only when its generated entry passes the same repository validator used for manually maintained modules.

## Safety model

1. The curated catalog is reviewed through a normal pull request.
2. CI validates count, category distribution, slugs, summaries, tags, HTTPS sources, use cases, and key points.
3. The seed workflow is never triggered by `pull_request` and requests `contents: write` only on trusted `main` execution.
4. Existing knowledge branches are skipped.
5. Each missing module is rendered into a temporary Git worktree based on `origin/main`.
6. `scripts/validate_entry.py` runs before the commit is pushed.
7. Each branch receives one focused commit containing only its `entry/` module plus the shared core files inherited from `main`.

## Scaling

Milestones should grow through curated catalogs rather than empty refs:

- v0.1 — 100 modules
- v0.5 — 1,000 modules
- v1.0 — 10,000 modules

Future catalogs should preserve deterministic slugs, source quality, and idempotent branch creation.
