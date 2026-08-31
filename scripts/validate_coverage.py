#!/usr/bin/env python3
"""Validate OpenDevIndex technology-universe and detailed topic allocations."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def _load(path: Path) -> tuple[dict | None, list[str]]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, [f"{path}: invalid YAML: {exc}"]
    if not isinstance(data, dict):
        return None, [f"{path}: top level must be a mapping"]
    return data, []


def validate(path: Path) -> list[str]:
    """Validate the high-level 10,000-module Technology Universe plan."""
    data, errors = _load(path)
    if data is None:
        return errors
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


def validate_topic_allocation(allocation_path: Path, universe_path: Path) -> list[str]:
    """Validate per-topic targets against the canonical Technology Universe plan."""
    allocation, errors = _load(allocation_path)
    universe, universe_errors = _load(universe_path)
    if allocation is None or universe is None:
        return errors + universe_errors

    if allocation.get("schema_version") != 1:
        errors.append("topic allocation schema_version must be 1")
    if allocation.get("target_modules") != universe.get("target_modules"):
        errors.append("topic allocation target must match technology universe target")

    universe_areas = {
        area.get("id"): area
        for area in universe.get("areas", [])
        if isinstance(area, dict) and isinstance(area.get("id"), str)
    }
    allocation_areas = allocation.get("areas")
    if not isinstance(allocation_areas, list) or not allocation_areas:
        return errors + ["topic allocation areas must be a non-empty list"]

    seen: set[str] = set()
    grand_total = 0
    for index, area in enumerate(allocation_areas, start=1):
        prefix = f"topic allocation area #{index}"
        if not isinstance(area, dict):
            errors.append(f"{prefix}: must be a mapping")
            continue
        area_id = area.get("id")
        if area_id in seen:
            errors.append(f"{prefix}: duplicate area {area_id}")
            continue
        seen.add(area_id)
        source_area = universe_areas.get(area_id)
        if source_area is None:
            errors.append(f"{prefix}: unknown area {area_id!r}")
            continue

        area_target = area.get("target_modules")
        if area_target != source_area.get("target_modules"):
            errors.append(f"{prefix}: target does not match technology universe")

        topic_targets = area.get("topic_targets")
        if not isinstance(topic_targets, dict) or not topic_targets:
            errors.append(f"{prefix}: topic_targets must be a non-empty mapping")
            continue

        expected_topics = source_area.get("topics", [])
        if set(topic_targets) != set(expected_topics):
            missing = sorted(set(expected_topics) - set(topic_targets))
            extra = sorted(set(topic_targets) - set(expected_topics))
            if missing:
                errors.append(f"{prefix}: missing topics: {', '.join(missing)}")
            if extra:
                errors.append(f"{prefix}: unexpected topics: {', '.join(extra)}")

        bad = [topic for topic, value in topic_targets.items() if not isinstance(value, int) or value <= 0]
        if bad:
            errors.append(f"{prefix}: topic targets must be positive integers: {', '.join(sorted(bad))}")
            continue

        topic_total = sum(topic_targets.values())
        if isinstance(area_target, int) and topic_total != area_target:
            errors.append(f"{prefix}: topic allocation is {topic_total}, expected {area_target}")
        grand_total += topic_total

    missing_areas = sorted(set(universe_areas) - seen)
    if missing_areas:
        errors.append(f"topic allocation missing areas: {', '.join(missing_areas)}")
    if grand_total != universe.get("target_modules"):
        errors.append(f"topic allocation total is {grand_total}, expected {universe.get('target_modules')}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("coverage", nargs="?", default="coverage/technology-universe-v1.yaml")
    parser.add_argument("--topic-allocation", default=None)
    args = parser.parse_args()

    coverage_path = Path(args.coverage)
    errors = validate(coverage_path)
    if args.topic_allocation:
        errors.extend(validate_topic_allocation(Path(args.topic_allocation), coverage_path))

    if errors:
        print("OpenDevIndex coverage validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"OpenDevIndex coverage validation passed: {coverage_path}")
    if args.topic_allocation:
        print(f"OpenDevIndex topic allocation validation passed: {args.topic_allocation}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
