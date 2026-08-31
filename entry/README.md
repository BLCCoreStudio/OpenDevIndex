# Linkerd

> Lightweight service mesh for Kubernetes that adds mutual TLS, traffic metrics, reliability features, and service-to-service policy through dedicated data-plane proxies.

## What it is

Linkerd is indexed as a **platform**. Its stable OpenDevIndex address is `platform/linkerd`; taxonomy facets are kept separate from that address so classification can improve without breaking links.

## Why it matters

The module focuses on the technology's practical role, high-signal characteristics, common use cases, and authoritative references. Fast-changing details should be verified against the sources below rather than inferred from stale copies.

## Typical use cases

- Encrypt service-to-service traffic with mutual TLS
- Collect service metrics for Kubernetes workloads
- Apply traffic policy and reliability controls without modifying application code

## Key points

- Linkerd injects lightweight proxies into meshed workloads
- The control plane manages identity policy and configuration
- The project emphasizes Kubernetes-native operation and a small data-plane footprint

## Taxonomy

- Kind: `platform`
- Domains: `cloud`, `networking`, `observability`
- Deployment: `self-hosted`, `service`
- License metadata: `not yet curated`

## Primary links

- Homepage: https://linkerd.io/
- Repository: https://github.com/linkerd/linkerd2

## Verified sources

- [Linkerd official site](https://linkerd.io/) — `official`
- [Linkerd source repository](https://github.com/linkerd/linkerd2) — `repository`

## Verification

The catalog metadata and source references for this module were reviewed on **2026-08-31**. Automated checks validate structure and source reachability; factual updates still require source-backed editorial review.

## Maintenance

Update this independently versioned module when material facts, project status, canonical documentation, or important trade-offs change. Preserve the stable module address unless a compatibility migration is explicitly documented.
