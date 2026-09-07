# Source quality guidance

OpenDevIndex prefers evidence that is close to the technology, claim, or event being documented. Source quality is not a popularity score: a useful source is one that is authoritative for the specific claim, current enough for the claim's volatility, and precise enough to audit.

## Evidence hierarchy

Use the strongest practical source for each claim.

### Tier 1 — primary and canonical

Prefer these whenever they directly support the claim:

- official project documentation and release notes;
- standards bodies and published specifications;
- canonical source repositories and maintained design documents;
- original security advisories and vendor bulletins;
- original research papers, protocol drafts, and architecture documents;
- official licensing, governance, compatibility, and support-policy pages.

Tier 1 is the default for architecture, protocol behavior, lifecycle guarantees, compatibility promises, security boundaries, licensing, and version-specific claims.

### Tier 2 — high-quality secondary

Use reputable secondary material when primary sources are incomplete, inaccessible, or insufficiently explanatory. Examples include established technical publications, conference material from identified practitioners, and well-maintained independent documentation that links back to primary evidence.

Secondary sources should add context, synthesis, operational experience, or comparison—not silently replace a primary source that already exists.

### Tier 3 — discovery only

Search results, forum posts, social posts, generated summaries, marketing pages, aggregator sites, and unsourced tutorials may help discover terminology or locate better evidence. They should not be the sole support for consequential factual claims.

## Match the source to the claim

A source can be authoritative for one claim and weak for another. For example:

- a protocol specification is strong evidence for wire semantics but may not describe one implementation's operational behavior;
- a project's own benchmark is evidence that the project published those numbers, not proof of universal performance superiority;
- a security advisory is strong evidence for the affected versions and remediation it names, but not for unrelated architectural claims;
- a repository README can establish project intent while implementation details may require code, design docs, or maintained technical documentation.

Avoid citing a generic homepage when a specific specification, release note, or design document supports the exact statement.

## Freshness and version scope

Before using a source for a fast-moving claim, verify that its version and date match the module text.

Review especially carefully when documenting:

- supported versions or platforms;
- APIs, flags, defaults, and configuration behavior;
- licensing or governance changes;
- security posture and advisories;
- cloud-service features;
- compatibility guarantees;
- performance characteristics;
- rapidly evolving AI, browser, mobile, and infrastructure tooling.

If the source is historically correct but no longer current, scope the prose explicitly to the relevant version or period rather than presenting it as timeless behavior.

## Claim discipline

For each non-trivial technical claim, ask:

1. What exactly is being asserted?
2. Which source directly supports that assertion?
3. Does the source describe the same version, mode, platform, and deployment boundary?
4. Is the wording more confident than the evidence permits?
5. Would a reader be able to audit the claim without guessing which paragraph or document was intended?

When evidence is ambiguous, narrow the claim or state the uncertainty. Do not combine several weak sources into a stronger-sounding conclusion than any of them support.

## Comparisons and trade-offs

Comparison content needs evidence on both sides. Avoid using one project's documentation to characterize a competing technology unless the statement is independently supported.

Prefer architecture and requirement language over universal rankings:

- describe the deployment boundary, failure model, consistency model, authorization model, lifecycle, or operational trade-off;
- distinguish measured facts from contextual judgment;
- avoid context-free "faster", "better", "more secure", or "enterprise-grade" claims;
- state when two technologies solve overlapping but non-equivalent problems.

## Security-sensitive material

For vulnerabilities, cryptography, authentication, sandboxing, privilege boundaries, supply-chain controls, and destructive recovery procedures:

- prefer original advisories, specifications, canonical security documentation, or primary research;
- record affected versions and prerequisites precisely;
- do not generalize a single vulnerability into a claim that an entire technology is insecure;
- separate mitigation guidance from factual vulnerability description;
- avoid reproducing exploit detail that is unnecessary to explain the engineering boundary.

## Source-list review checklist

Before considering a module or substantial revision ready for editorial review, check that:

- important architecture and behavior claims have direct authoritative support;
- version-sensitive claims use current or explicitly version-scoped evidence;
- source links are specific enough to audit;
- secondary sources add value instead of replacing available primary documentation;
- marketing copy, generated text, snippets, and community discussion are not acting as sole authority;
- alternatives and comparisons are sourced fairly;
- licensing, security, compatibility, and support claims use first-party or canonical evidence where available;
- the module's `verified_at` date reflects an actual review of the cited evidence.

Automated source-health checks only establish that a URL can be reached. They do not establish that the source proves the claim. Editorial review remains responsible for that judgment.
