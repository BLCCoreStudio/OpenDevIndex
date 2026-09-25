# Relationship Suggestions and Validation

OpenDevIndex relationships are editorial claims, not graph-decoration metadata. A useful edge should help a reader understand architecture, dependency, compatibility, history, alternatives, or a sensible next topic.

This guide provides a lightweight workflow for proposing relationship changes without creating artificial graph density.

## Start from a reader question

Before adding an edge, state the question it answers. Good examples include:

- What does this technology depend on at runtime or build time?
- Which protocol or standard does it implement?
- Which component is this part of?
- Which technology is a realistic alternative under similar requirements?
- Which predecessor or successor explains an important historical transition?
- What adjacent module should a reader learn next to understand this subject?

If the edge does not answer a useful question, do not add it.

## Choose the narrowest relationship type

Prefer the most specific relationship that accurately describes the connection:

- `depends-on` — the source requires the target as a dependency or operational prerequisite.
- `uses` — the source deliberately uses the target, but the target is not necessarily a hard dependency.
- `implements` — the source implements a protocol, standard, interface, or specification represented by the target.
- `integrates-with` — the technologies interoperate through a supported integration without implying dependency.
- `part-of` — the source is a component or sub-system of the target.
- `alternative-to` — the modules address sufficiently similar needs that a real engineering choice may exist between them.
- `based-on` — the source is materially derived from, built on, or architecturally founded on the target.
- `predecessor-of` / `successor-of` — use only for a meaningful historical or product-line succession relationship.
- `related-to` — reserve for useful adjacency that cannot be expressed more precisely.

Do not use `related-to` as a fallback merely because a precise relationship requires more research.

## Evidence expectations

Relationship edges should be supportable by the same source discipline as module content.

Prefer:

1. official architecture or product documentation;
2. standards/specifications for implementation relationships;
3. canonical repositories or release/migration documentation for lineage;
4. authoritative compatibility or integration documentation;
5. high-quality secondary sources only when primary material does not establish the claim clearly.

For `alternative-to`, avoid relying on marketing comparison pages from either vendor alone. The relationship should reflect overlapping engineering use cases, not popularity or branding.

## Direction matters

Read the proposed edge as a sentence before committing it.

Examples:

- `tool/docker` **uses** `tool/containerd`
- `tool/containerd` **implements** `standard/oci-runtime-spec`
- `cloud/helm` **integrates-with** `cloud/kubernetes`

Do not assume every relationship is symmetric. Add a reverse edge only when the reverse statement is independently meaningful and allowed by the model.

## Avoid graph inflation

Do not add edges solely because two technologies:

- appear in the same stack;
- are often mentioned in the same article;
- share a broad domain;
- are maintained by the same organization;
- can technically be used together;
- would make a module appear better connected.

A small number of specific, teachable edges is better than a dense graph of weak associations.

## Suggested review workflow

For each proposed edge:

1. confirm both module references exist in the catalog;
2. write the relationship as a plain-language sentence;
3. choose the narrowest accurate type;
4. confirm the direction is correct;
5. identify evidence that supports the exact claim;
6. check whether an existing edge already expresses the same relationship;
7. consider whether the edge improves discovery, comparison, architecture understanding, or learning navigation;
8. reject the edge if its main benefit is graph-count growth.

## Validate locally

Run the repository relationship validator after editing catalog relationship metadata:

```bash
python scripts/validate_relationships.py catalog/*.yaml
```

For catalog changes, also run the normal repository checks:

```bash
python -m unittest discover -s tests -v
python scripts/validate_catalog.py catalog/v0.1.yaml
python scripts/build_index.py --catalog-dir catalog --output-dir dist/index
```

Validation confirms structural correctness, known targets, and supported relationship types. It does not prove that the relationship is factually or editorially justified.

## Review checklist

Before opening a pull request, verify that:

- the target module exists;
- the edge type is supported and as specific as practical;
- the direction reads correctly;
- the relationship is useful to a reader;
- authoritative evidence exists for consequential claims;
- the edge does not duplicate an existing connection;
- the edge was not added merely to increase graph density;
- `scripts/validate_relationships.py` passes;
- generated discovery changes are reviewed when the catalog change affects navigation.

Relationship suggestions should make the map easier to reason about, not merely larger.
