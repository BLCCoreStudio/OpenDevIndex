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

from taxonomy import (
    load_taxonomy,
    supported_address_categories,
    supported_relationship_types,
)
from url_safety import is_safe_https_url

SOURCE_TYPES = {"official", "repository", "standard", "advisory", "research", "documentation"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
TAG_RE = re.compile(r"^[a-z0-9][a-z0-9.+_-]*$")
MODULE_REF_RE = re.compile(r"^[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9._-]*$")


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path}: invalid YAML: {exc}"]

    if not isinstance(data, dict):
        return [f"{path}: top level must be a mapping"]

    schema_version = data.get("schema_version")
    if schema_version not in {1, 2, 3}:
        errors.append("schema_version must be 1, 2, or 3")

    try:
        taxonomy = load_taxonomy()
    except Exception as exc:
        return errors + [f"taxonomy validation failed: {exc}"]

    categories = supported_address_categories(taxonomy)
    kinds = set(taxonomy["canonical_kinds"])
    domains_allowed = set(taxonomy["domains"])
    deployments_allowed = set(taxonomy["deployment_types"])
    relationships_allowed = supported_relationship_types(taxonomy)

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

        if category not in categories:
            errors.append(f"{prefix}: unsupported address category {category!r}")
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

        min_curated = 3 if schema_version in {2, 3} else 2
        tags = entry.get("tags")
        if not isinstance(tags, list) or len(tags) < min_curated:
            errors.append(f"{prefix}: tags must contain at least {min_curated} values")
        elif len(tags) != len(set(tags)):
            errors.append(f"{prefix}: tags must be unique")
        elif any(not isinstance(tag, str) or not TAG_RE.fullmatch(tag) for tag in tags):
            errors.append(f"{prefix}: invalid tag")

        kind = entry.get("kind")
        domains = entry.get("domains")
        if schema_version in {2, 3} and kind is None:
            errors.append(f"{prefix}: taxonomy v{schema_version} entries require kind")
        if kind is not None and kind not in kinds:
            errors.append(f"{prefix}: unsupported kind {kind!r}")
        if schema_version in {2, 3} and not domains:
            errors.append(f"{prefix}: taxonomy v{schema_version} entries require domains")
        if domains is not None:
            if not isinstance(domains, list) or not domains:
                errors.append(f"{prefix}: domains must be a non-empty list")
            elif len(domains) != len(set(domains)):
                errors.append(f"{prefix}: domains must be unique")
            elif any(domain not in domains_allowed for domain in domains):
                errors.append(f"{prefix}: unsupported domain")

        deployment_types = entry.get("deployment_types")
        if deployment_types is not None:
            if not isinstance(deployment_types, list) or not deployment_types:
                errors.append(f"{prefix}: deployment_types must be a non-empty list when present")
            elif len(deployment_types) != len(set(deployment_types)):
                errors.append(f"{prefix}: deployment_types must be unique")
            elif any(value not in deployments_allowed for value in deployment_types):
                errors.append(f"{prefix}: unsupported deployment type")

        relationships = entry.get("relationships")
        if relationships is not None:
            if schema_version != 3:
                errors.append(f"{prefix}: relationships require schema_version 3")
            if not isinstance(relationships, list):
                errors.append(f"{prefix}: relationships must be a list when present")
            else:
                seen_relationships: set[tuple[str, str]] = set()
                for relation_number, relationship in enumerate(relationships, start=1):
                    relation_prefix = f"{prefix}: relationship #{relation_number}"
                    if not isinstance(relationship, dict):
                        errors.append(f"{relation_prefix} must be a mapping")
                        continue
                    unexpected = set(relationship) - {"type", "target", "note"}
                    if unexpected:
                        errors.append(
                            f"{relation_prefix} contains unsupported keys: {', '.join(sorted(unexpected))}"
                        )
                    relationship_type = relationship.get("type")
                    relationship_target = relationship.get("target")
                    if relationship_type not in relationships_allowed:
                        errors.append(f"{relation_prefix} has unsupported type")
                    if not isinstance(relationship_target, str) or not MODULE_REF_RE.fullmatch(relationship_target):
                        errors.append(f"{relation_prefix} target must use <category>/<slug>")
                    pair = (relationship_type, relationship_target)
                    if pair in seen_relationships:
                        errors.append(f"{relation_prefix} duplicates an existing type/target pair")
                    seen_relationships.add(pair)
                    note = relationship.get("note")
                    if note is not None and (
                        not isinstance(note, str) or not note.strip() or len(note) > 240
                    ):
                        errors.append(
                            f"{relation_prefix} note must be a non-empty string up to 240 characters"
                        )

        license_value = entry.get("license")
        if license_value is not None and (not isinstance(license_value, str) or not license_value.strip() or len(license_value) > 100):
            errors.append(f"{prefix}: license must be a non-empty string up to 100 characters")

        for field in ("homepage", "repository"):
            value = entry.get(field)
            if value is not None and not is_safe_https_url(value):
                errors.append(f"{prefix}: {field} must be a public HTTPS URL")

        sources = entry.get("sources")
        min_sources = 2 if schema_version in {2, 3} else 1
        if not isinstance(sources, list) or len(sources) < min_sources:
            errors.append(f"{prefix}: sources must contain at least {min_sources} reference(s)")
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
            if not isinstance(values, list) or len(values) < min_curated:
                errors.append(f"{prefix}: {field} must contain at least {min_curated} curated items")
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
