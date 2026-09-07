# Contribution paths

OpenDevIndex contributions do not need to add a new technology module. Small, well-scoped improvements to existing knowledge are often more valuable because they strengthen trust, depth, discovery, or navigation without expanding the catalog unnecessarily.

Use the narrowest contribution path that matches the change you can support with evidence.

## Correct a factual weakness

Use this path when an existing statement is inaccurate, misleading, obsolete, or too absolute.

Expected change:

- identify the exact claim that needs correction;
- replace it with the narrowest accurate wording;
- add or update an authoritative source that supports the corrected claim;
- update verification metadata when the corrected fact is time-sensitive;
- avoid unrelated editorial rewrites in the same pull request.

A correction should improve factual reliability without silently changing unrelated architecture, taxonomy, maturity, or graph data.

## Improve sources or provenance

Use this path when the module is directionally correct but its evidence is weak, stale, secondary when a primary source exists, or broader than the claim it supports.

Expected change:

- prefer official specifications, documentation, release notes, design documents, or project-maintained references;
- match each replacement source to the claim it actually proves;
- preserve useful secondary sources when they add independent context rather than merely duplicating a primary source;
- do not increase confidence or maturity only because more URLs were added.

See `docs/SOURCE_QUALITY.md` for the detailed source-quality workflow.

## Add a practical example or workflow

Use this path when a module explains what a technology is but does not yet help a reader perform a representative task.

Good additions include:

- a minimal command sequence;
- a small API or configuration example;
- a troubleshooting or recovery workflow;
- a concrete lifecycle walkthrough;
- an example that exposes an important boundary or failure mode.

Examples should teach the concept without becoming a substitute for upstream documentation. Prefer small, stable examples over large copied configurations.

## Add or clarify architecture

Use this path when the module names components but does not explain ownership, data flow, control flow, process boundaries, protocol boundaries, or where state actually lives.

Expected change:

- identify the reader question the architecture explanation answers;
- distinguish components that own state from components that only observe or transform it;
- separate control-plane and data-plane behavior where relevant;
- call out important external dependencies and failure boundaries;
- support non-obvious architecture claims with authoritative evidence.

Avoid decorative diagrams or terminology lists that do not improve the mental model.

## Add a graph relationship

Use this path when an existing module is missing a meaningful connection that helps readers navigate architecture, dependencies, compatibility, history, or alternatives.

Before editing graph data:

1. start from a concrete reader or architecture question;
2. choose the narrowest supported relationship type;
3. verify directionality;
4. ensure the target module actually exists;
5. add evidence for non-obvious claims;
6. run the relationship validator and generated-index checks.

Do not add links only to increase graph density. See `docs/RELATIONSHIP_SUGGESTIONS.md` for the complete workflow.

## Deepen an existing module

Use this path when an overview is correct but not yet useful enough as a guide or deep dive.

Prefer depth that adds one or more of the following:

- a stronger mental model;
- architecture or internals;
- realistic workflows;
- recovery and failure diagnosis;
- performance or reliability trade-offs;
- security or privacy boundaries;
- meaningful alternatives;
- a beginner-to-advanced learning path.

Do not raise maturity mechanically. Use `docs/MODULE_DEEPENING_CHECKLIST.md` and the kind-specific editorial checklist before claiming a maturity change.

## Improve discovery without changing knowledge claims

Use this path for search metadata, taxonomy fit, comparison discovery, generated navigation, or other findability improvements that do not alter substantive technical claims.

Expected change:

- explain which discovery problem is being solved;
- keep ranking or taxonomy changes narrow and deterministic;
- preview generated catalog/search artifacts;
- test representative queries or navigation paths;
- verify that existing stable module addresses do not regress.

See `docs/GENERATED_ARTIFACT_PREVIEW.md` before opening the pull request.

## Keep pull requests narrow

A contribution is easier to review when it has one primary purpose. If a correction uncovers a separate architecture rewrite or new comparison opportunity, prefer a follow-up pull request unless the changes are inseparable.

For every path:

- preserve stable module identifiers;
- do not copy upstream manuals wholesale;
- do not treat generated text as an authoritative source;
- do not make unrelated schema, maturity, or graph changes;
- run the relevant local validators before requesting review;
- describe what was intentionally left unchanged.

The goal is not to maximize changed lines. The goal is to leave one useful part of the map more accurate, teachable, connected, or discoverable than it was before.
