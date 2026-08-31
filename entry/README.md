# ccache

> Compiler cache for C and C++ toolchains that detects equivalent compilations and reuses previous outputs to reduce incremental build times.

## What it is

ccache is indexed as a **tool**. Its stable OpenDevIndex address is `tool/ccache`; taxonomy facets are kept separate from that address so classification can improve without breaking links.

## Why it matters

The module focuses on the technology's practical role, high-signal characteristics, common use cases, and authoritative references. Fast-changing details should be verified against the sources below rather than inferred from stale copies.

## Typical use cases

- Accelerate repeated C and C++ builds
- Reduce CI compile time when inputs are unchanged
- Use local or supported remote caches in native build workflows

## Key points

- ccache sits in front of supported compilers
- It hashes relevant compiler inputs to find reusable results
- The tool supports statistics and multiple cache configuration options

## Taxonomy

- Kind: `tool`
- Domains: `build`, `developer-tools`
- Deployment: `cli`, `local`
- License metadata: `not yet curated`

## Primary links

- Homepage: https://ccache.dev/
- Repository: https://github.com/ccache/ccache

## Verified sources

- [ccache official site](https://ccache.dev/) — `official`
- [ccache source repository](https://github.com/ccache/ccache) — `repository`

## Verification

The catalog metadata and source references for this module were reviewed on **2026-08-31**. Automated checks validate structure and source reachability; factual updates still require source-backed editorial review.

## Maintenance

Update this independently versioned module when material facts, project status, canonical documentation, or important trade-offs change. Preserve the stable module address unless a compatibility migration is explicitly documented.
