#!/usr/bin/env python3
"""Load and validate OpenDevIndex module maturity metadata."""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from collections import Counter
from pathlib import Path

import yaml

LEVELS = ("overview", "guide", "deep-dive")
ALLOWED_MODULE_KEYS = {"level", "reviewed_at", "note"}


def load_maturity_manifest(path: Path, known_refs: set[str] | None = None) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"{path}: invalid YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"{path}: top level must be a mapping")
    if data.get("schema_version") != 1:
        raise ValueError(f"{path}: schema_version must be 1")

    default_level = data.get("default_level")
    if default_level not in LEVELS:
        raise ValueError(f"{path}: default_level must be one of {', '.join(LEVELS)}")

    declared_levels = data.get("levels")
    if declared_levels != list(LEVELS):
        raise ValueError(f"{path}: levels must exactly match {list(LEVELS)!r}")

    modules = data.get("modules")
    if not isinstance(modules, dict):
        raise ValueError(f"{path}: modules must be a mapping")

    normalized: dict[str, dict] = {}
    for module_ref, metadata in modules.items():
        if not isinstance(module_ref, str) or module_ref.count("/") != 1:
            raise ValueError(f"{path}: invalid module reference {module_ref!r}")
        if known_refs is not None and module_ref not in known_refs:
            raise ValueError(f"{path}: maturity entry references unknown module {module_ref}")
        if not isinstance(metadata, dict):
            raise ValueError(f"{path}: {module_ref} metadata must be a mapping")

        unexpected = set(metadata) - ALLOWED_MODULE_KEYS
        if unexpected:
            raise ValueError(
                f"{path}: {module_ref} contains unsupported keys: {', '.join(sorted(unexpected))}"
            )

        level = metadata.get("level")
        if level not in LEVELS:
            raise ValueError(f"{path}: {module_ref} has invalid level {level!r}")

        reviewed_at = metadata.get("reviewed_at")
        try:
            reviewed_date = dt.date.fromisoformat(str(reviewed_at))
        except ValueError as exc:
            raise ValueError(f"{path}: {module_ref} reviewed_at must be YYYY-MM-DD") from exc
        if reviewed_date > dt.date.today():
            raise ValueError(f"{path}: {module_ref} reviewed_at cannot be in the future")

        note = metadata.get("note")
        if note is not None and (
            not isinstance(note, str) or not note.strip() or len(note) > 240
        ):
            raise ValueError(f"{path}: {module_ref} note must be non-empty and at most 240 characters")

        normalized[module_ref] = {
            "level": level,
            "reviewed_at": str(reviewed_at),
            **({"note": note.strip()} if isinstance(note, str) else {}),
        }

    return {
        "schema_version": 1,
        "default_level": default_level,
        "levels": list(LEVELS),
        "modules": normalized,
    }


def module_level(module_ref: str, manifest: dict | None) -> str:
    if not manifest:
        return "overview"
    metadata = manifest.get("modules", {}).get(module_ref, {})
    return metadata.get("level", manifest.get("default_level", "overview"))


def maturity_counts(module_refs: list[str], manifest: dict | None) -> dict[str, int]:
    counts: Counter[str] = Counter(module_level(module_ref, manifest) for module_ref in module_refs)
    return {level: counts.get(level, 0) for level in LEVELS if counts.get(level, 0)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", nargs="?", default="quality/module-maturity.yaml")
    parser.add_argument("--known-ref", action="append", default=[])
    args = parser.parse_args()

    known_refs = set(args.known_ref) if args.known_ref else None
    try:
        manifest = load_maturity_manifest(Path(args.manifest), known_refs)
    except (OSError, ValueError) as exc:
        print(f"OpenDevIndex maturity validation failed: {exc}", file=sys.stderr)
        return 1

    print(
        "OpenDevIndex maturity validation passed: "
        f"{len(manifest['modules'])} explicit module rating(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
