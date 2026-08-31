# sccache

> Compilation cache that accelerates repeated builds by reusing compiler outputs locally or through remote storage backends across supported toolchains.

## What it is

sccache is indexed as a **tool**. Its stable OpenDevIndex address is `tool/sccache`; taxonomy facets are kept separate from that address so classification can improve without breaking links.

## Why it matters

The module focuses on the technology's practical role, high-signal characteristics, common use cases, and authoritative references. Fast-changing details should be verified against the sources below rather than inferred from stale copies.

## Typical use cases

- Speed up repeated native and Rust compilations
- Share cached compiler outputs across CI workers
- Reduce rebuild time in large codebases

## Key points

- sccache wraps supported compilers and hashes compilation inputs
- Cache storage can be local or backed by remote services
- The tool is commonly used with Rust and C-family build pipelines

## Taxonomy

- Kind: `tool`
- Domains: `build`, `developer-tools`
- Deployment: `cli`, `local`
- License metadata: `not yet curated`

## Primary links

- Homepage: https://github.com/mozilla/sccache
- Repository: https://github.com/mozilla/sccache

## Verified sources

- [sccache source repository](https://github.com/mozilla/sccache) — `repository`
- [sccache documentation](https://github.com/mozilla/sccache/blob/main/docs/README.md) — `documentation`

## Verification

The catalog metadata and source references for this module were reviewed on **2026-08-31**. Automated checks validate structure and source reachability; factual updates still require source-backed editorial review.

## Maintenance

Update this independently versioned module when material facts, project status, canonical documentation, or important trade-offs change. Preserve the stable module address unless a compatibility migration is explicitly documented.
