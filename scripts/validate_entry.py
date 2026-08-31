#!/usr/bin/env python3
"""Validate an OpenDevIndex knowledge module."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

import yaml

from url_safety import is_safe_https_url

CATEGORIES = {
    "tool",
    "language",
    "framework",
    "ai",
    "security",
    "cloud",
    "database",
    "protocol",
    "concept",
    "opensource",
}
CORE_PREFIXES = ("feat/", "fix/", "docs/", "chore/", "ci/", "refactor/", "release/")
REQUIRED_FILES = (
    Path("entry/README.md"),
    Path("entry/entry.yaml"),
    Path("entry/sources.md"),
    Path("entry/history.md"),
)
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
TAG_RE = re.compile(r"^[a-z0-9][a-z0-9.+_-]*$")


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def validate(branch: str) -> list[str]:
    errors: list[str] = []

    if branch == "main" or branch.startswith(CORE_PREFIXES):
        return errors

    if "/" not in branch:
        fail("Knowledge module ref must use <category>/<slug>.", errors)
        return errors

    category, slug = branch.split("/", 1)
    if category not in CATEGORIES:
        fail(f"Unsupported category prefix: {category}", errors)
    if not SLUG_RE.fullmatch(slug):
        fail(f"Invalid module slug: {slug}", errors)

    for path in REQUIRED_FILES:
        if not path.is_file():
            fail(f"Missing required file: {path}", errors)

    metadata_path = Path("entry/entry.yaml")
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
        "schema_version",
        "id",
        "name",
        "category",
        "summary",
        "status",
        "verified_at",
        "tags",
        "sources",
    }
    missing = sorted(required - data.keys())
    if missing:
        fail(f"Missing metadata keys: {', '.join(missing)}", errors)

    if data.get("schema_version") != 1:
        fail("schema_version must be 1.", errors)
    if data.get("id") != slug:
        fail(f"metadata id must match module slug '{slug}'.", errors)
    if data.get("category") != category:
        fail(f"metadata category must match module category '{category}'.", errors)

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

    tags = data.get("tags")
    if not isinstance(tags, list) or len(tags) < 2:
        fail("tags must contain at least two values.", errors)
    elif len(tags) != len(set(tags)):
        fail("tags must be unique.", errors)
    elif any(not isinstance(tag, str) or not TAG_RE.fullmatch(tag) for tag in tags):
        fail("tags must use lowercase slug-like values.", errors)

    for field in ("homepage", "repository"):
        value = data.get(field)
        if value is not None and not is_safe_https_url(value):
            fail(f"{field} must be a public HTTPS URL when present.", errors)

    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        fail("sources must contain at least one source.", errors)
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

    readme = Path("entry/README.md")
    if readme.is_file() and len(readme.read_text(encoding="utf-8").strip()) < 300:
        fail("entry/README.md is too short to be a useful module (minimum 300 characters).", errors)

    sources_md = Path("entry/sources.md")
    if sources_md.is_file() and "https://" not in sources_md.read_text(encoding="utf-8"):
        fail("entry/sources.md must contain at least one HTTPS reference.", errors)

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", required=True, help="Module ref or core branch name being validated")
    args = parser.parse_args()

    errors = validate(args.branch)
    if errors:
        print("OpenDevIndex validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"OpenDevIndex validation passed for {args.branch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
