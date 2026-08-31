#!/usr/bin/env python3
"""Validate the machine-readable OpenDevIndex technology-universe plan."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path}: invalid YAML: {exc}"]

    if not isinstance(data, dict):
        return ["top level must be a mapping"]
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    target = data.get("target_modules")
    if not isinstance(target, int) or target <= 0:
        errors.append("target_modules must be a positive integer")

    areas = data.get("areas")
    if not isinstance(areas, list) or not areas:
        return errors + ["areas must be a non-empty list"]

    seen_areas: set[str] = set()
    allocated = 0
    for index, area in enumerate(areas, start=1):
        prefix = f"area #{index}"
        if not isinstance(area, dict):
            errors.append(f"{prefix}: must be a mapping")
            continue

        area_id = area.get("id")
        if not isinstance(area_id, str) or not SLUG_RE.fullmatch(area_id):
            errors.append(f"{prefix}: invalid id")
        elif area_id in seen_areas:
            errors.append(f"{prefix}: duplicate id {area_id}")
        else:
            seen_areas.add(area_id)

        if not isinstance(area.get("name"), str) or not area["name"].strip():
            errors.append(f"{prefix}: name must be non-empty")

        count = area.get("target_modules")
        if not isinstance(count, int) or count <= 0:
            errors.append(f"{prefix}: target_modules must be positive")
        else:
            allocated += count

        topics = area.get("topics")
        if not isinstance(topics, list) or len(topics) < 5:
            errors.append(f"{prefix}: topics must contain at least 5 values")
        elif len(topics) != len(set(topics)):
            errors.append(f"{prefix}: topics must be unique")
        elif any(not isinstance(topic, str) or not SLUG_RE.fullmatch(topic) for topic in topics):
            errors.append(f"{prefix}: topics must use lowercase slug-like values")

    if isinstance(target, int) and allocated != target:
        errors.append(f"area allocation is {allocated}, expected {target}")
    if target != 10000:
        errors.append("technology-universe v1 must allocate exactly 10,000 modules")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("coverage", nargs="?", default="coverage/technology-universe-v1.yaml")
    args = parser.parse_args()
    errors = validate(Path(args.coverage))
    if errors:
        print("OpenDevIndex coverage validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"OpenDevIndex coverage validation passed: {args.coverage}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
