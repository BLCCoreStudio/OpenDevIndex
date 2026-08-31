# Module Coverage Metadata

Schema v3 modules map themselves into the Technology Universe so coverage can be measured instead of estimated.

A schema v3 entry must include:

```yaml
coverage:
  area: developer-tools
  topics:
    - developer-experience
```

The `area` must exist in [`coverage/technology-universe-v1.yaml`](../coverage/technology-universe-v1.yaml). Every topic must belong to that selected area. The validator rejects unknown areas, unknown topics, duplicate topics, and empty topic lists.

This metadata is separate from taxonomy. `kind` describes what a technology is, `domains` describe where it belongs semantically, and `coverage` describes which part of the 10,000-module Technology Universe plan the module fulfills.

For example, a debugger can have `kind: tool`, domains such as `developer-tools`, `systems`, and `testing`, while its coverage mapping can point to `testing-debugging-performance` with topics such as `debugging` and `profiling`.

Schema v1 and v2 modules remain compatible and do not require this field. New schema v3 modules require it so future coverage reports can calculate progress by area and topic without guessing from tags.
