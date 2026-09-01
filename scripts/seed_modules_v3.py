#!/usr/bin/env python3
"""Schema v3 adapter for the existing trusted OpenDevIndex module publisher."""

from __future__ import annotations

import yaml

import seed_modules

_ORIGINAL_RENDER_METADATA = seed_modules.render_metadata
_ORIGINAL_RENDER_README = seed_modules.render_readme
_ORIGINAL_RENDER_HISTORY = seed_modules.render_history


def _validate_relationships(entry: dict) -> list[dict]:
    relationships = entry.get("relationships") or []
    if not isinstance(relationships, list):
        raise ValueError("schema v3 relationships must be a list")

    allowed = seed_modules.load_taxonomy().get("relationship_types", [])
    allowed_types = set(allowed)
    seen: set[tuple[str, str]] = set()
    normalized: list[dict] = []

    for index, relationship in enumerate(relationships, start=1):
        if not isinstance(relationship, dict):
            raise ValueError(f"relationship #{index} must be a mapping")
        unexpected = set(relationship) - {"type", "target", "note"}
        if unexpected:
            raise ValueError(
                f"relationship #{index} contains unsupported keys: {', '.join(sorted(unexpected))}"
            )

        relationship_type = relationship.get("type")
        target = relationship.get("target")
        note = relationship.get("note")
        if relationship_type not in allowed_types:
            raise ValueError(f"relationship #{index} has unsupported type {relationship_type!r}")
        if not isinstance(target, str) or "/" not in target or target.startswith("/") or target.endswith("/"):
            raise ValueError(f"relationship #{index} target must use <category>/<slug>")
        if target == entry.get("module_ref"):
            raise ValueError(f"relationship #{index} cannot target the module itself")
        if note is not None and (
            not isinstance(note, str) or not note.strip() or len(note) > 240
        ):
            raise ValueError(f"relationship #{index} note must be non-empty and at most 240 characters")

        pair = (relationship_type, target)
        if pair in seen:
            raise ValueError(f"relationship #{index} duplicates an existing type/target pair")
        seen.add(pair)
        normalized.append(relationship)

    return normalized


def render_metadata_v3(entry: dict, verified_at: str, schema_version: int) -> str:
    """Preserve v3 graph/coverage fields while reusing the existing publisher."""
    rendered = _ORIGINAL_RENDER_METADATA(entry, verified_at, schema_version)
    if schema_version < 3:
        return rendered

    metadata = yaml.safe_load(rendered)
    if not isinstance(metadata, dict):
        raise ValueError("publisher metadata renderer returned invalid YAML")

    coverage = entry.get("coverage")
    if not isinstance(coverage, dict):
        raise ValueError("schema v3 publication requires coverage metadata")
    metadata["coverage"] = coverage

    relationships = _validate_relationships(entry)
    if relationships:
        metadata["relationships"] = relationships

    return yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True, width=1000)


def render_relationships_v3(entry: dict) -> str:
    relationships = _validate_relationships(entry)
    if not relationships:
        return "- No curated knowledge-graph relationships yet."

    lines: list[str] = []
    for relationship in relationships:
        note = relationship.get("note")
        suffix = f" — {note}" if note else ""
        lines.append(
            f"- `{relationship['type']}` → `{relationship['target']}`{suffix}"
        )
    return "\n".join(lines)


def render_readme_v3(entry: dict) -> str:
    rendered = _ORIGINAL_RENDER_README(entry)
    if not entry.get("relationships"):
        return rendered

    marker = "\n## Primary links\n"
    relationships_section = (
        "\n## Knowledge graph\n\n"
        f"{render_relationships_v3(entry)}\n"
    )
    if marker not in rendered:
        return rendered.rstrip() + relationships_section + "\n"
    return rendered.replace(marker, relationships_section + marker, 1)


def render_history_v3(
    entry: dict,
    verified_at: str,
    milestone: str,
    previous: str | None = None,
) -> str:
    rendered = _ORIGINAL_RENDER_HISTORY(entry, verified_at, milestone, previous)
    relationships = _validate_relationships(entry)
    if not relationships:
        return rendered

    marker = "- Re-rendered module documentation from validated source-backed metadata."
    graph_line = f"- Recorded **{len(relationships)}** typed knowledge-graph relationship(s).\n"
    if marker in rendered:
        return rendered.replace(marker, graph_line + marker, 1)
    return rendered.rstrip() + "\n" + graph_line


def install_adapter() -> None:
    seed_modules.render_metadata = render_metadata_v3
    seed_modules.render_readme = render_readme_v3
    seed_modules.render_history = render_history_v3


def main() -> int:
    install_adapter()
    return seed_modules.main()


if __name__ == "__main__":
    raise SystemExit(main())
