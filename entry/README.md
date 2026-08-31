# mold

> High-speed linker for Unix-like systems designed as a drop-in alternative for common ELF linkers, reducing the final link stage of large native builds.

## What it is

mold is indexed as a **tool**. Its stable OpenDevIndex address is `tool/mold`; taxonomy facets are kept separate from that address so classification can improve without breaking links.

## Why it matters

The module focuses on the technology's practical role, high-signal characteristics, common use cases, and authoritative references. Fast-changing details should be verified against the sources below rather than inferred from stale copies.

## Typical use cases

- Reduce link times for large native applications
- Use a faster linker in C and C++ build pipelines
- Experiment with parallelized linking for large binaries

## Key points

- mold is designed for high parallelism during linking
- It targets compatibility with common Unix linker command conventions
- The project focuses on native ELF-oriented toolchains

## Taxonomy

- Kind: `tool`
- Domains: `build`, `systems`
- Deployment: `cli`, `system`
- License metadata: `not yet curated`

## Primary links

- Homepage: https://github.com/rui314/mold
- Repository: https://github.com/rui314/mold

## Verified sources

- [mold source repository](https://github.com/rui314/mold) — `repository`
- [mold documentation](https://github.com/rui314/mold/blob/main/docs/mold.md) — `documentation`

## Verification

The catalog metadata and source references for this module were reviewed on **2026-08-31**. Automated checks validate structure and source reachability; factual updates still require source-backed editorial review.

## Maintenance

Update this independently versioned module when material facts, project status, canonical documentation, or important trade-offs change. Preserve the stable module address unless a compatibility migration is explicitly documented.
