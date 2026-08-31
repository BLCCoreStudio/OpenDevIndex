#!/usr/bin/env python3
"""Shared catalog loading helpers for OpenDevIndex tooling."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Iterable

import yaml

from taxonomy import enrich_entry, load_taxonomy
from validate_catalog import validate as validate_catalog


def discover_catalogs(catalog_dir: Path) -> list[Path]:
    """Return milestone catalogs in stable filename order."""
    paths = sorted(
        path
        for path in catalog_dir.glob("*.yaml")
        if path.is_file() and not path.name.startswith("_")
    )
    if not paths:
        raise ValueError(f"no catalog YAML files found in {catalog_dir}")
    return paths


def load_catalog(path: Path) -> dict:
    """Load one catalog after running the repository validator."""
    errors = validate_catalog(path)
    if errors:
        joined = "\n".join(f"- {error}" for error in errors)
        raise ValueError(f"catalog validation failed for {path}:\n{joined}")

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top level must be a mapping")
    return data


def collect_entries(paths: Iterable[Path]) -> tuple[list[dict], list[dict]]:
    """Collect and taxonomy-enrich entries while rejecting cross-catalog duplicates."""
    entries: list[dict] = []
    catalogs: list[dict] = []
    seen_refs: set[str] = set()
    taxonomy = load_taxonomy()

    for path in paths:
        data = load_catalog(path)
        verified_at = str(data["verified_at"])
        milestone = str(data.get("milestone", path.stem))
        catalog_entries = data["entries"]

        catalogs.append(
            {
                "path": path.as_posix(),
                "milestone": milestone,
                "verified_at": verified_at,
                "schema_version": data.get("schema_version", 1),
                "module_count": len(catalog_entries),
            }
        )

        for raw in catalog_entries:
            entry = dict(raw)
            module_ref = f"{entry['category']}/{entry['id']}"
            if module_ref in seen_refs:
                raise ValueError(f"duplicate module across catalogs: {module_ref}")
            seen_refs.add(module_ref)
            entry["module_ref"] = module_ref
            entry["catalog"] = path.as_posix()
            entry["milestone"] = milestone
            entry["verified_at"] = verified_at
            entry["catalog_schema_version"] = data.get("schema_version", 1)
            entries.append(enrich_entry(entry, taxonomy))

    kind_order = {kind: index for index, kind in enumerate(taxonomy["canonical_kinds"])}
    entries.sort(
        key=lambda item: (
            kind_order.get(item["kind"], len(kind_order)),
            item["name"].casefold(),
            item["module_ref"],
        )
    )
    return entries, catalogs


def category_counts(entries: Iterable[dict]) -> dict[str, int]:
    counts = Counter(entry["category"] for entry in entries)
    return dict(sorted(counts.items()))


def kind_counts(entries: Iterable[dict]) -> dict[str, int]:
    taxonomy = load_taxonomy()
    counts = Counter(entry["kind"] for entry in entries)
    return {
        kind: counts[kind]
        for kind in taxonomy["canonical_kinds"]
        if counts.get(kind, 0)
    }


def domain_counts(entries: Iterable[dict]) -> dict[str, int]:
    taxonomy = load_taxonomy()
    counts: Counter[str] = Counter()
    for entry in entries:
        counts.update(entry.get("domains", []))
    return {
        domain: counts[domain]
        for domain in taxonomy["domains"]
        if counts.get(domain, 0)
    }
