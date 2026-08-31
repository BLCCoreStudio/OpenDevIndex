# Ninja

> Small build system focused on executing generated build graphs as quickly as possible, commonly used as a backend for higher-level generators such as CMake and Meson.

## What it is

Ninja is indexed as a **tool**. Its stable OpenDevIndex address is `tool/ninja`; taxonomy facets are kept separate from that address so classification can improve without breaking links.

## Why it matters

The module focuses on the technology's practical role, high-signal characteristics, common use cases, and authoritative references. Fast-changing details should be verified against the sources below rather than inferred from stale copies.

## Typical use cases

- Execute large native build graphs with low overhead
- Serve as the generated backend for CMake, Meson, GN, and other build configuration systems
- Run incremental compilation efficiently in projects with many files and generated dependencies

## Key points

- Ninja deliberately keeps its build-file language minimal and expects higher-level tools to generate complex graphs
- Fast startup and dependency checking are central design priorities
- The tool tracks explicit and discovered dependencies to avoid unnecessary rebuilds

## Taxonomy

- Kind: `tool`
- Domains: `build`, `developer-tools`, `systems`
- Deployment: `cli`, `local`
- License metadata: `Apache-2.0`

## Primary links

- Homepage: https://ninja-build.org/
- Repository: https://github.com/ninja-build/ninja

## Verified sources

- [Ninja official site](https://ninja-build.org/) — `official`
- [Ninja source repository](https://github.com/ninja-build/ninja) — `repository`

## Verification

The catalog metadata and source references for this module were reviewed on **2026-08-31**. Automated checks validate structure and source reachability; factual updates still require source-backed editorial review.

## Maintenance

Update this independently versioned module when material facts, project status, canonical documentation, or important trade-offs change. Preserve the stable module address unless a compatibility migration is explicitly documented.
