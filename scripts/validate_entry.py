#!/usr/bin/env python3
"""Validate an OpenDevIndex knowledge module."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

import yaml

from coverage_metadata import validate_coverage_metadata
from taxonomy import load_taxonomy, supported_address_categories, supported_relationship_types
from url_safety import is_safe_https_url

CORE_PREFIXES = ("feat/", "fix/", "docs/", "chore/", "ci/", "refactor/", "release/")
REQUIRED_FILES = (
    Path("entry/README.md"),
    Path("entry/entry.yaml"),
    Path("entry/sources.md"),
    Path("entry/history.md"),
)
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
TAG_RE = re.compile(r"^[a-z0-9][a-z0-9.+_-]*$")
MODULE_REF_RE = re.compile(r"^[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9._-]*$")


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def validate(branch: str, root: Path | None = None) -> list[str]:
    errors: list[str] = []
    root = root or Path.cwd()

    if branch == "main" or branch.startswith(CORE_PREFIXES):
        return errors

    if "/" not in branch:
        fail("Knowledge module ref must use <category>/<slug>.", errors)
        return errors

    taxonomy = load_taxonomy()
    categories = supported_address_categories(taxonomy)
    kinds = set(taxonomy["canonical_kinds"])
    domains_allowed = set(taxonomy["domains"])
    deployment_allowed = set(taxonomy["deployment_types"])
    relationship_allowed = supported_relationship_types(taxonomy)

    category, slug = branch.split("/", 1)
    if category not in categories:
        fail(f"Unsupported category prefix: {category}", errors)
    if not SLUG_RE.fullmatch(slug):
        fail(f"Invalid module slug: {slug}", errors)

    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            fail(f"Missing required file: {relative}", errors)

    metadata_path = root / "entry/entry.yaml"
    if not metadata_path.is_file():
        return errors

    try:
        data = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"entry/entry.yaml is not valid YAML: {exc}", errors)
        return errors

    if not isinstance(data, dict):
        fail("entry/entry.yaml must contain a mapping/object.", errors)
        return errors

    required = {
        "schema_version", "id", "name", "category", "summary", "status",
        "verified_at", "tags", "sources",
    }
    missing = sorted(required - data.keys())
    if missing:
        fail(f"Missing metadata keys: {', '.join(missing)}", errors)

    schema_version = data.get("schema_version")
    if schema_version not in {1, 2, 3}:
        fail("schema_version must be 1, 2, or 3.", errors)
    if schema_version in {2, 3}:
        for key in ("kind", "domains"):
            if key not in data:
                fail(f"schema v{schema_version} requires metadata key: {key}", errors)
    if schema_version == 3 and "coverage" not in data:
        fail("schema v3 requires metadata key: coverage", errors)

    if data.get("id") != slug:
        fail(f"metadata id must match module slug '{slug}'.", errors)
    if data.get("category") != category:
        fail(f"metadata category must match module category '{category}'.", errors)

    kind = data.get("kind")
    if kind is not None and kind not in kinds:
        fail(f"unsupported canonical kind: {kind}", errors)

    domains = data.get("domains")
    if domains is not None:
        if not isinstance(domains, list) or not domains:
            fail("domains must be a non-empty list.", errors)
        elif len(domains) != len(set(domains)):
            fail("domains must be unique.", errors)
        elif any(domain not in domains_allowed for domain in domains):
            fail("domains contain an unsupported taxonomy value.", errors)

    for coverage_error in validate_coverage_metadata(data.get("coverage")):
        fail(coverage_error, errors)

    deployments = data.get("deployment_types")
    if deployments is not None:
        if not isinstance(deployments, list) or not deployments:
            fail("deployment_types must be a non-empty list when present.", errors)
        elif len(deployments) != len(set(deployments)):
            fail("deployment_types must be unique.", errors)
        elif any(value not in deployment_allowed for value in deployments):
            fail("deployment_types contain an unsupported value.", errors)

    relationships = data.get("relationships")
    if relationships is not None:
        if not isinstance(relationships, list):
            fail("relationships must be a list when present.", errors)
        else:
            seen_relationships: set[tuple[str, str]] = set()
            for index, relationship in enumerate(relationships, start=1):
                if not isinstance(relationship, dict):
                    fail(f"relationship #{index} must be an object.", errors)
                    continue
                relationship_type = relationship.get("type")
                target = relationship.get("target")
                if relationship_type not in relationship_allowed:
                    fail(f"relationship #{index} has unsupported type.", errors)
                if not isinstance(target, str) or not MODULE_REF_RE.fullmatch(target):
                    fail(f"relationship #{index} target must use <category>/<slug>.", errors)
                pair = (relationship_type, target)
                if pair in seen_relationships:
                    fail(f"relationship #{index} duplicates an existing type/target pair.", errors)
                seen_relationships.add(pair)
                note = relationship.get("note")
                if note is not None and (not isinstance(note, str) or not note.strip() or len(note) > 240):
                    fail(f"relationship #{index} note must be a non-empty string up to 240 characters.", errors)

    license_value = data.get("license")
    if license_value is not None and (not isinstance(license_value, str) or not license_value.strip() or len(license_value) > 100):
        fail("license must be a non-empty string up to 100 characters.", errors)

    name = data.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 100:
        fail("name must be a non-empty string up to 100 characters.", errors)

    summary = data.get("summary")
    if not isinstance(summary, str) or not (40 <= len(summary.strip()) <= 320):
        fail("summary must be between 40 and 320 characters.", errors)

    if data.get("status") not in {"active", "maintenance", "deprecated", "historical"}:
        fail("status must be active, maintenance, deprecated, or historical.", errors)

    verified_at = data.get("verified_at")
    if isinstance(verified_at, dt.date):
        verified_date = verified_at
    elif isinstance(verified_at, str):
        try:
            verified_date = dt.date.fromisoformat(verified_at)
        except ValueError:
            verified_date = None
    else:
        verified_date = None
    if verified_date is None:
        fail("verified_at must be an ISO date (YYYY-MM-DD).", errors)
    elif verified_date > dt.date.today():
        fail("verified_at cannot be in the future.", errors)

    min_curated = 3 if schema_version in {2, 3} else 2
    tags = data.get("tags")
    if not isinstance(tags, list) or len(tags) < min_curated:
        fail(f"tags must contain at least {min_curated} values.", errors)
    elif len(tags) != len(set(tags)):
        fail("tags must be unique.", errors)
    elif any(not isinstance(tag, str) or not TAG_RE.fullmatch(tag) for tag in tags):
        fail("tags must use lowercase slug-like values.", errors)

    for field in ("homepage", "repository"):
        value = data.get(field)
        if value is not None and not is_safe_https_url(value):
            fail(f"{field} must be a public HTTPS URL when present.", errors)

    sources = data.get("sources")
    min_sources = 2 if schema_version in {2, 3} else 1
    if not isinstance(sources, list) or len(sources) < min_sources:
        fail(f"sources must contain at least {min_sources} source(s).", errors)
    else:
        allowed_types = {"official", "repository", "standard", "advisory", "research", "documentation"}
        for index, source in enumerate(sources, start=1):
            if not isinstance(source, dict):
                fail(f"source #{index} must be an object.", errors)
                continue
            if not source.get("title"):
                fail(f"source #{index} is missing title.", errors)
            if not is_safe_https_url(source.get("url")):
                fail(f"source #{index} must use a public HTTPS URL.", errors)
            if source.get("type") not in allowed_types:
                fail(f"source #{index} has unsupported type.", errors)

    readme = root / "entry/README.md"
    minimum_readme = 600 if schema_version == 3 else (450 if schema_version == 2 else 300)
    if readme.is_file() and len(readme.read_text(encoding="utf-8").strip()) < minimum_readme:
        fail(f"entry/README.md is too short to be useful (minimum {minimum_readme} characters).", errors)

    sources_md = root / "entry/sources.md"
    if sources_md.is_file() and "https://" not in sources_md.read_text(encoding="utf-8"):
        fail("entry/sources.md must contain at least one HTTPS reference.", errors)

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", required=True, help="Module ref or core branch name being validated")
    parser.add_argument("--root", default=".", help="Repository/worktree root containing entry/")
    args = parser.parse_args()

    errors = validate(args.branch, Path(args.root).resolve())
    if errors:
        print("OpenDevIndex validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"OpenDevIndex validation passed for {args.branch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
