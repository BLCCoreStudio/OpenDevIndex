#!/usr/bin/env python3
"""OpenDevIndex taxonomy loading, validation, and enrichment helpers."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Iterable

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TAXONOMY = ROOT / "taxonomy/v3.yaml"
SUPPORTED_TAXONOMY_VERSIONS = {2, 3}


@lru_cache(maxsize=4)
def load_taxonomy(path: str | Path = DEFAULT_TAXONOMY) -> dict:
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") not in SUPPORTED_TAXONOMY_VERSIONS:
        supported = ", ".join(str(value) for value in sorted(SUPPORTED_TAXONOMY_VERSIONS))
        raise ValueError(f"{path}: taxonomy schema_version must be one of {supported}")

    required_lists = ("canonical_kinds", "legacy_address_categories", "domains", "deployment_types")
    for key in required_lists:
        value = data.get(key)
        if not isinstance(value, list) or not value or len(value) != len(set(value)):
            raise ValueError(f"{path}: {key} must be a non-empty unique list")

    if data.get("schema_version") >= 3:
        relationship_types = data.get("relationship_types")
        if not isinstance(relationship_types, list) or not relationship_types or len(relationship_types) != len(set(relationship_types)):
            raise ValueError(f"{path}: relationship_types must be a non-empty unique list")

    defaults = data.get("category_defaults")
    if not isinstance(defaults, dict) or not defaults:
        raise ValueError(f"{path}: category_defaults must be a non-empty mapping")

    kinds = set(data["canonical_kinds"])
    domains = set(data["domains"])
    for category, default in defaults.items():
        if not isinstance(default, dict) or default.get("kind") not in kinds:
            raise ValueError(f"{path}: invalid default kind for {category}")
        default_domains = default.get("domains", [])
        if any(domain not in domains for domain in default_domains):
            raise ValueError(f"{path}: invalid default domain for {category}")

    return data


def supported_address_categories(taxonomy: dict | None = None) -> set[str]:
    taxonomy = taxonomy or load_taxonomy()
    return set(taxonomy["category_defaults"])


def supported_relationship_types(taxonomy: dict | None = None) -> set[str]:
    taxonomy = taxonomy or load_taxonomy()
    return set(taxonomy.get("relationship_types", []))


def stable_unique(values: Iterable[str], order: list[str] | None = None) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    if order:
        rank = {value: index for index, value in enumerate(order)}
        result.sort(key=lambda value: (rank.get(value, len(rank)), value))
    return result


def enrich_entry(entry: dict, taxonomy: dict | None = None) -> dict:
    """Return an entry enriched with canonical kind/domain facets.

    Stable address namespaces are deliberately separated from semantic type
    (`kind`). Explicit catalog facets take precedence over curated overrides and
    category defaults; recognized tags may add discovery facets without
    replacing them.
    """
    taxonomy = taxonomy or load_taxonomy()
    enriched = dict(entry)
    module_ref = enriched.get("module_ref") or f"{enriched['category']}/{enriched['id']}"
    enriched["module_ref"] = module_ref

    default = taxonomy["category_defaults"].get(enriched["category"], {})
    override = taxonomy.get("overrides", {}).get(module_ref, {})

    kind = enriched.get("kind") or override.get("kind") or default.get("kind")
    if kind not in set(taxonomy["canonical_kinds"]):
        raise ValueError(f"{module_ref}: unsupported canonical kind {kind!r}")

    if enriched.get("domains"):
        base_domains = list(enriched["domains"])
    elif override.get("domains"):
        base_domains = list(override["domains"])
    else:
        base_domains = list(default.get("domains", []))

    tag_domains = taxonomy.get("tag_domains", {})
    derived_domains = [tag_domains[tag] for tag in enriched.get("tags", []) if tag in tag_domains]
    domains = stable_unique([*base_domains, *derived_domains], order=list(taxonomy["domains"]))
    unknown = sorted(set(domains) - set(taxonomy["domains"]))
    if unknown:
        raise ValueError(f"{module_ref}: unsupported domains: {', '.join(unknown)}")

    relationship_types = supported_relationship_types(taxonomy)
    for relationship in enriched.get("relationships", []):
        if not isinstance(relationship, dict):
            raise ValueError(f"{module_ref}: relationships must contain mappings")
        relationship_type = relationship.get("type")
        if relationship_types and relationship_type not in relationship_types:
            raise ValueError(f"{module_ref}: unsupported relationship type {relationship_type!r}")

    enriched["kind"] = kind
    enriched["domains"] = domains
    enriched["address_category"] = enriched["category"]
    return enriched
