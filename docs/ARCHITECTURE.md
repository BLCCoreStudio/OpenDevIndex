# Architecture

OpenDevIndex separates the **index itself** from the **knowledge modules** it indexes.

## 1. `main` is the control plane

The default branch contains the project rules, schema, validators, contribution documentation, catalog tooling, and generated index artifacts. It should stay small enough to clone and understand quickly.

## 2. Knowledge branches are modules

A knowledge branch represents one canonical subject. Its name is its address:

```text
<category>/<slug>
```

Examples:

```text
tool/qemu
language/rust
framework/pytorch
protocol/mcp
```

A valid module contains `entry/README.md`, `entry/entry.yaml`, `entry/sources.md`, and `entry/history.md`.

This model gives each topic an independent history while avoiding a single enormous content tree on `main`.

## 3. Machine-readable metadata

`entry/entry.yaml` is the canonical metadata record. It includes identity, category, summary, links, tags, verification date, status, and sources.

The schema lives at `schema/entry.schema.json`. CI performs additional semantic checks such as matching the branch prefix to the declared category.

## 4. Generated catalog

The long-term catalog process will enumerate available knowledge modules, validate each one, normalize metadata, and publish searchable JSON/index artifacts back to `main`.

Only modules whose required content, metadata, and source references pass validation are published into the searchable index.

## 5. Branch lifecycle

Knowledge modules may be updated in place when facts, releases, ownership, support, or sources change. Major disputed rewrites should go through a review branch and pull request before moving the module ref.

Core infrastructure uses normal branches such as `feat/*`, `fix/*`, and `docs/*` and is merged into `main` through pull requests.

## 6. Quality at scale

OpenDevIndex is designed to grow into a broad, searchable software knowledge base while keeping every module useful, source-backed, and maintainable. Empty, duplicate, placeholder, or low-value modules are invalid.
