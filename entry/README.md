# HashiCorp Vault

> Secrets-management and cryptographic platform for securely storing credentials, issuing dynamic secrets, managing encryption keys, and brokering machine identities.

## What it is

HashiCorp Vault is indexed as a **platform**. Its stable OpenDevIndex address is `platform/vault`; taxonomy facets are kept separate from that address so classification can improve without breaking links.

## Why it matters

The module focuses on the technology's practical role, high-signal characteristics, common use cases, and authoritative references. Fast-changing details should be verified against the sources below rather than inferred from stale copies.

## Typical use cases

- Store and control access to application secrets
- Generate dynamic database or cloud credentials
- Provide encryption and signing operations through centralized policy

## Key points

- Vault uses policy-controlled authenticated access to secret engines
- Dynamic secrets can be generated with limited lifetimes
- The transit engine can perform cryptographic operations without exposing raw keys

## Taxonomy

- Kind: `platform`
- Domains: `cloud`, `security`
- Deployment: `self-hosted`, `service`
- License metadata: `not yet curated`

## Primary links

- Homepage: https://developer.hashicorp.com/vault
- Repository: https://github.com/hashicorp/vault

## Verified sources

- [Vault documentation](https://developer.hashicorp.com/vault) — `documentation`
- [Vault source repository](https://github.com/hashicorp/vault) — `repository`

## Verification

The catalog metadata and source references for this module were reviewed on **2026-08-31**. Automated checks validate structure and source reachability; factual updates still require source-backed editorial review.

## Maintenance

Update this independently versioned module when material facts, project status, canonical documentation, or important trade-offs change. Preserve the stable module address unless a compatibility migration is explicitly documented.
