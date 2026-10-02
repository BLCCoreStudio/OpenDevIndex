#!/usr/bin/env python3
"""Validate schema-v3 OpenDevIndex knowledge-graph relationships."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

from taxonomy import load_taxonomy, supported_address_categories, supported_relationship_types

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def validate_entry_relationships(entry: dict, schema_version: int, taxonomy: dict | None = None) -> list[str]:
    taxonomy = taxonomy or load_taxonomy()
    relationships = entry.get("relationships")
    if relationships is None:
        return []

    module_ref = f"{entry.get('category')}/{entry.get('id')}"
    errors: list[str] = []
    if schema_version != 3:
        return [f"{module_ref}: relationships require schema_version 3"]
    if not isinstance(relationships, list):
        return [f"{module_ref}: relationships must be a list"]

    allowed_types = supported_relationship_types(taxonomy)
    allowed_categories = supported_address_categories(taxonomy)
    seen: set[tuple[str, str]] = set()

    for number, relationship in enumerate(relationships, start=1):
        prefix = f"{module_ref}: relationship #{number}"
        if not isinstance(relationship, dict):
            errors.append(f"{prefix} must be a mapping")
            continue

        unexpected = set(relationship) - {"type", "target", "note"}
        if unexpected:
            errors.append(f"{prefix} contains unsupported keys: {', '.join(sorted(unexpected))}")

        relationship_type = relationship.get("type")
        target = relationship.get("target")
        note = relationship.get("note")

        if relationship_type not in allowed_types:
            errors.append(f"{prefix} has unsupported type {relationship_type!r}")

        target_valid = False
        if isinstance(target, str) and target.count("/") == 1:
            category, slug = target.split("/", 1)
            target_valid = category in allowed_categories and bool(SLUG_RE.fullmatch(slug))
        if not target_valid:
            errors.append(f"{prefix} target must use a supported <category>/<slug> address")
        elif target == module_ref:
            errors.append(f"{prefix} cannot target the module itself")

        pair = (str(relationship_type), str(target))
        if pair in seen:
            errors.append(f"{prefix} duplicates an existing type/target pair")
        seen.add(pair)

        if note is not None and (
            not isinstance(note, str) or not note.strip() or len(note) > 240
        ):
            errors.append(f"{prefix} note must be a non-empty string up to 240 characters")

    return errors


def _load_catalog(path: Path) -> tuple[dict | None, list[str]]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, [f"{path}: invalid YAML: {exc}"]
    if not isinstance(data, dict):
        return None, [f"{path}: top level must be a mapping"]
    return data, []


def validate_catalog(path: Path) -> list[str]:
    data, load_errors = _load_catalog(path)
    if load_errors:
        return load_errors
    assert data is not None

    schema_version = data.get("schema_version")
    if not isinstance(schema_version, int):
        return [f"{path}: schema_version must be an integer"]

    entries = data.get("entries")
    if not isinstance(entries, list):
        return [f"{path}: entries must be a list"]

    taxonomy = load_taxonomy()
    errors: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        errors.extend(validate_entry_relationships(entry, schema_version, taxonomy))
    return [f"{path}: {error}" for error in errors]


def validate_relationship_targets(paths: list[Path]) -> list[str]:
    """Require valid relationship targets to resolve within the supplied catalog set."""
    loaded: list[tuple[Path, dict]] = []
    module_refs: set[str] = set()

    for path in paths:
        data, load_errors = _load_catalog(path)
        if load_errors or data is None:
            continue
        entries = data.get("entries")
        if not isinstance(entries, list):
            continue
        loaded.append((path, data))
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            category = entry.get("category")
            module_id = entry.get("id")
            if isinstance(category, str) and isinstance(module_id, str):
                module_refs.add(f"{category}/{module_id}")

    errors: list[str] = []
    for path, data in loaded:
        for entry in data.get("entries", []):
            if not isinstance(entry, dict):
                continue
            relationships = entry.get("relationships")
            if not isinstance(relationships, list):
                continue
            module_ref = f"{entry.get('category')}/{entry.get('id')}"
            for number, relationship in enumerate(relationships, start=1):
                if not isinstance(relationship, dict):
                    continue
                target = relationship.get("target")
                if not isinstance(target, str) or target.count("/") != 1:
                    continue
                if target not in module_refs:
                    errors.append(
                        f"{path}: {module_ref}: relationship #{number} target {target!r} "
                        "does not exist in the supplied catalogs"
                    )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("catalogs", nargs="+", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    for path in args.catalogs:
        errors.extend(validate_catalog(path))
    errors.extend(validate_relationship_targets(args.catalogs))

    if errors:
        print("OpenDevIndex relationship validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"OpenDevIndex relationship validation passed for {len(args.catalogs)} catalog(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
