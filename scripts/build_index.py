#!/usr/bin/env python3
"""Build deterministic OpenDevIndex search/catalog artifacts."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from catalog_utils import category_counts, collect_entries, discover_catalogs, domain_counts, kind_counts

TOKEN_RE = re.compile(r"[^a-z0-9.+_-]+")
REPOSITORY_URL = "https://github.com/BLCCoreStudio/OpenDevIndex"


def normalize_text(value: object) -> str:
    text = str(value or "").casefold()
    return " ".join(part for part in TOKEN_RE.split(text) if part)


def module_url(module_ref: str) -> str:
    return f"{REPOSITORY_URL}/tree/{module_ref}/entry"


def coverage_area_counts(entries: list[dict]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for entry in entries:
        coverage = entry.get("coverage") or {}
        area = coverage.get("area")
        if isinstance(area, str) and area:
            counts[area] += 1
    return dict(sorted(counts.items()))


def coverage_topic_counts(entries: list[dict]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for entry in entries:
        coverage = entry.get("coverage") or {}
        area = coverage.get("area")
        for topic in coverage.get("topics", []):
            if isinstance(area, str) and isinstance(topic, str):
                counts[f"{area}/{topic}"] += 1
    return dict(sorted(counts.items()))


def search_text(entry: dict) -> str:
    coverage = entry.get("coverage") or {}
    values: list[str] = [
        entry["module_ref"],
        entry["id"],
        entry["name"],
        entry["category"],
        entry["kind"],
        entry["summary"],
        *entry.get("domains", []),
        *entry.get("tags", []),
        *entry.get("deployment_types", []),
        entry.get("license", ""),
        coverage.get("area", ""),
        *coverage.get("topics", []),
        *entry.get("use_cases", []),
        *entry.get("key_points", []),
    ]
    return normalize_text(" ".join(values))


def public_record(entry: dict) -> dict:
    coverage = entry.get("coverage") or {}
    return {
        "ref": entry["module_ref"],
        "url": module_url(entry["module_ref"]),
        "slug": entry["id"],
        "name": entry["name"],
        "address_category": entry["category"],
        "kind": entry["kind"],
        "domains": entry.get("domains", []),
        "coverage_area": coverage.get("area"),
        "coverage_topics": coverage.get("topics", []),
        "summary": entry["summary"],
        "tags": entry.get("tags", []),
        "deployment_types": entry.get("deployment_types", []),
        "license": entry.get("license"),
        "use_cases": entry.get("use_cases", []),
        "key_points": entry.get("key_points", []),
        "homepage": entry.get("homepage"),
        "repository": entry.get("repository"),
        "sources": entry.get("sources", []),
        "verified_at": entry["verified_at"],
        "milestone": entry["milestone"],
    }


def search_record(entry: dict) -> dict:
    record = public_record(entry)
    record["search_text"] = search_text(entry)
    return record


def render_markdown(entries: list[dict], kinds: dict[str, int], domains: dict[str, int], coverage_areas: dict[str, int]) -> str:
    lines = [
        "# OpenDevIndex — Browse the Index",
        "",
        "This file is generated from validated OpenDevIndex catalogs. Each module link opens its independently versioned knowledge entry.",
        "",
        f"**Indexed modules:** {len(entries)}",
        "",
        "## Browse by kind",
        "",
        "| Kind | Modules |",
        "| --- | ---: |",
    ]
    for kind, count in kinds.items():
        lines.append(f"| `{kind}` | {count} |")

    lines.extend(["", "## Domain coverage", "", "| Domain | Modules |", "| --- | ---: |"])
    for domain, count in domains.items():
        lines.append(f"| `{domain}` | {count} |")

    if coverage_areas:
        lines.extend(["", "## Technology Universe coverage", "", "| Area | Mapped modules |", "| --- | ---: |"])
        for area, count in coverage_areas.items():
            lines.append(f"| `{area}` | {count} |")

    current: str | None = None
    for entry in entries:
        if entry["kind"] != current:
            current = entry["kind"]
            lines.extend(
                [
                    "",
                    f"## {current}",
                    "",
                    "| Module | Domains | Summary |",
                    "| --- | --- | --- |",
                ]
            )
        domains_text = ", ".join(f"`{domain}`" for domain in entry.get("domains", []))
        summary = entry["summary"].replace("|", "\\|")
        name = entry["name"].replace("|", "\\|")
        ref = entry["module_ref"]
        lines.append(f"| [{name}]({module_url(ref)}) (`{ref}`) | {domains_text} | {summary} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "OpenDevIndex separates stable module addresses from taxonomy facets. Legacy addresses remain valid while `kind`, `domains`, and schema v3 coverage metadata provide consistent discovery and filtering.",
            "",
        ]
    )
    return "\n".join(lines)


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build(catalog_dir: Path, output_dir: Path, public_index: Path | None = None) -> dict:
    paths = discover_catalogs(catalog_dir)
    entries, catalogs = collect_entries(paths)
    categories = category_counts(entries)
    kinds = kind_counts(entries)
    domains = domain_counts(entries)
    coverage_areas = coverage_area_counts(entries)
    coverage_topics = coverage_topic_counts(entries)
    output_dir.mkdir(parents=True, exist_ok=True)

    catalog_payload = {
        "schema_version": 3,
        "module_count": len(entries),
        "address_category_counts": categories,
        "kind_counts": kinds,
        "domain_counts": domains,
        "coverage_area_counts": coverage_areas,
        "coverage_topic_counts": coverage_topics,
        "catalogs": catalogs,
        "entries": [public_record(entry) for entry in entries],
    }
    search_payload = {
        "schema_version": 3,
        "module_count": len(entries),
        "kind_counts": kinds,
        "domain_counts": domains,
        "coverage_area_counts": coverage_areas,
        "coverage_topic_counts": coverage_topics,
        "entries": [search_record(entry) for entry in entries],
    }

    markdown = render_markdown(entries, kinds, domains, coverage_areas)
    write_json(output_dir / "catalog.json", catalog_payload)
    write_json(output_dir / "search.json", search_payload)
    (output_dir / "catalog.md").write_text(markdown, encoding="utf-8")
    if public_index is not None:
        public_index.write_text(markdown, encoding="utf-8")

    return {
        "module_count": len(entries),
        "address_category_counts": categories,
        "kind_counts": kinds,
        "domain_counts": domains,
        "coverage_area_counts": coverage_areas,
        "coverage_topic_counts": coverage_topics,
        "catalogs": [item["path"] for item in catalogs],
        "output_dir": output_dir.as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog-dir", default="catalog")
    parser.add_argument("--output-dir", default="dist/index")
    parser.add_argument("--public-index", help="Optional generated Markdown index path, e.g. INDEX.md")
    args = parser.parse_args()

    result = build(
        Path(args.catalog_dir),
        Path(args.output_dir),
        Path(args.public_index) if args.public_index else None,
    )
    print(
        "OpenDevIndex search index built: "
        f"{result['module_count']} modules -> {result['output_dir']}"
    )
    for kind, count in result["kind_counts"].items():
        print(f"- {kind}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
