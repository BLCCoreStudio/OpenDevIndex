# Hadolint

> Dockerfile linter that combines Dockerfile best-practice rules with shell-script analysis to catch common image-build mistakes before deployment.

## What it is

Hadolint is indexed as a **tool**. Its stable OpenDevIndex address is `tool/hadolint`; taxonomy facets are kept separate from that address so classification can improve without breaking links.

## Why it matters

The module focuses on the technology's practical role, high-signal characteristics, common use cases, and authoritative references. Fast-changing details should be verified against the sources below rather than inferred from stale copies.

## Typical use cases

- Lint Dockerfiles in CI pipelines
- Catch risky or inefficient image-build patterns
- Enforce container build conventions across repositories

## Key points

- Hadolint parses Dockerfiles into an abstract syntax tree
- Embedded shell commands are checked with ShellCheck-derived rules
- Rules can be configured ignored or enforced by severity

## Taxonomy

- Kind: `tool`
- Domains: `containers`, `developer-tools`
- Deployment: `cli`, `local`
- License metadata: `not yet curated`

## Primary links

- Homepage: https://github.com/hadolint/hadolint
- Repository: https://github.com/hadolint/hadolint

## Verified sources

- [Hadolint source repository](https://github.com/hadolint/hadolint) — `repository`
- [Hadolint documentation](https://github.com/hadolint/hadolint#readme) — `documentation`

## Verification

The catalog metadata and source references for this module were reviewed on **2026-08-31**. Automated checks validate structure and source reachability; factual updates still require source-backed editorial review.

## Maintenance

Update this independently versioned module when material facts, project status, canonical documentation, or important trade-offs change. Preserve the stable module address unless a compatibility migration is explicitly documented.
