#!/usr/bin/env python3
"""Validate a curated OpenDevIndex milestone catalog."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

from url_safety import is_safe_https_url

CATEGORIES = {
    "tool", "language", "framework", "ai", "security",
    "cloud", "database", "protocol", "concept", "opensource",
}
SOURCE_TYPES = {"official", "repository", "standard", "advisory", "research", "documentation"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
TAG_RE = re.compile(r"^[a-z0-9][a-z0-9.+_-]*$")


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path}: invalid YAML: {exc}"]

    if not isinstance(data, dict):
        return [f"{path}: top level must be a mapping"]

    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    target = data.get("target_modules")
    entries = data.get("entries")
    expected = data.get("expected_categories")

    if not isinstance(entries, list):
        return errors + ["entries must be a list"]
    if not isinstance(target, int) or target <= 0:
        errors.append("target_modules must be a positive integer")
    elif len(entries) != target:
        errors.append(f"catalog has {len(entries)} entries but target_modules is {target}")

    verified_at = data.get("verified_at")
    try:
        verified_date = dt.date.fromisoformat(str(verified_at))
        if verified_date > dt.date.today():
            errors.append("verified_at cannot be in the future")
    except ValueError:
        errors.append("verified_at must be YYYY-MM-DD")

    seen: set[str] = set()
    counts: Counter[str] = Counter()

    for number, entry in enumerate(entries, start=1):
        prefix = f"entry #{number}"
        if not isinstance(entry, dict):
            errors.append(f"{prefix}: must be a mapping")
            continue

        category = entry.get("category")
        slug = entry.get("id")
        name = entry.get("name")
        summary = entry.get("summary")
        module_ref = f"{category}/{slug}"

        if category not in CATEGORIES:
            errors.append(f"{prefix}: unsupported category {category!r}")
        else:
            counts[category] += 1

        if not isinstance(slug, str) or not SLUG_RE.fullmatch(slug):
            errors.append(f"{prefix}: invalid id {slug!r}")

        if module_ref in seen:
            errors.append(f"{prefix}: duplicate module {module_ref}")
        seen.add(module_ref)

        if not isinstance(name, str) or not name.strip() or len(name) > 100:
            errors.append(f"{prefix}: name must be 1..100 characters")

        if not isinstance(summary, str) or not 40 <= len(summary.strip()) <= 320:
            errors.append(f"{prefix}: summary must be 40..320 characters")

        tags = entry.get("tags")
        if not isinstance(tags, list) or len(tags) < 2:
            errors.append(f"{prefix}: tags must contain at least two values")
        elif len(tags) != len(set(tags)):
            errors.append(f"{prefix}: tags must be unique")
        elif any(not isinstance(tag, str) or not TAG_RE.fullmatch(tag) for tag in tags):
            errors.append(f"{prefix}: invalid tag")

        for field in ("homepage", "repository"):
            value = entry.get(field)
            if value is not None and not is_safe_https_url(value):
                errors.append(f"{prefix}: {field} must be a public HTTPS URL")

        sources = entry.get("sources")
        if not isinstance(sources, list) or not sources:
            errors.append(f"{prefix}: sources must not be empty")
        else:
            for i, source in enumerate(sources, start=1):
                if not isinstance(source, dict):
                    errors.append(f"{prefix}: source #{i} must be a mapping")
                    continue
                if not source.get("title"):
                    errors.append(f"{prefix}: source #{i} missing title")
                if not is_safe_https_url(source.get("url")):
                    errors.append(f"{prefix}: source #{i} must use a public HTTPS URL")
                if source.get("type") not in SOURCE_TYPES:
                    errors.append(f"{prefix}: source #{i} has invalid type")

        for field in ("use_cases", "key_points"):
            values = entry.get(field)
            if not isinstance(values, list) or len(values) < 2:
                errors.append(f"{prefix}: {field} must contain at least two curated items")
            elif any(not isinstance(value, str) or len(value.strip()) < 10 for value in values):
                errors.append(f"{prefix}: {field} items must be meaningful text")

    if not isinstance(expected, dict):
        errors.append("expected_categories must be a mapping")
    else:
        try:
            normalized = {str(k): int(v) for k, v in expected.items()}
        except (TypeError, ValueError):
            errors.append("expected_categories values must be integers")
            normalized = {}
        if normalized and normalized != dict(counts):
            errors.append(
                "category distribution mismatch: "
                f"expected {normalized}, actual {dict(counts)}"
            )
        if normalized and isinstance(target, int) and sum(normalized.values()) != target:
            errors.append("expected_categories must sum to target_modules")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("catalog", nargs="?", default="catalog/v0.1.yaml")
    args = parser.parse_args()
    path = Path(args.catalog)

    errors = validate(path)
    if errors:
        print("OpenDevIndex catalog validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"OpenDevIndex catalog validation passed: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
