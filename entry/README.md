# containerd

> Industry-standard container runtime focused on managing the complete container lifecycle, including image transfer, storage, execution, supervision, and low-level runtime integration.

## What it is

containerd is indexed as a **tool**. Its stable OpenDevIndex address is `tool/containerd`; taxonomy facets are kept separate from that address so classification can improve without breaking links.

## Why it matters

The module focuses on the technology's practical role, high-signal characteristics, common use cases, and authoritative references. Fast-changing details should be verified against the sources below rather than inferred from stale copies.

## Typical use cases

- Provide container lifecycle services underneath Kubernetes and other orchestration platforms
- Manage OCI images, snapshots, running containers, and runtime processes
- Embed a stable container runtime API inside higher-level infrastructure platforms

## Key points

- containerd is a daemon and API rather than a full end-user developer platform like Docker
- It integrates with OCI runtimes such as runc for low-level container execution
- The project is a graduated Cloud Native Computing Foundation project and is widely used in Kubernetes environments

## Taxonomy

- Kind: `tool`
- Domains: `cloud`, `containers`, `systems`
- Deployment: `service`, `system`, `self-hosted`
- License metadata: `Apache-2.0`

## Primary links

- Homepage: https://containerd.io/
- Repository: https://github.com/containerd/containerd

## Verified sources

- [containerd official site](https://containerd.io/) — `official`
- [containerd source repository](https://github.com/containerd/containerd) — `repository`

## Verification

The catalog metadata and source references for this module were reviewed on **2026-08-31**. Automated checks validate structure and source reachability; factual updates still require source-backed editorial review.

## Maintenance

Update this independently versioned module when material facts, project status, canonical documentation, or important trade-offs change. Preserve the stable module address unless a compatibility migration is explicitly documented.
