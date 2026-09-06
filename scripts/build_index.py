#!/usr/bin/env python3
"""Build deterministic OpenDevIndex search/catalog artifacts."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from catalog_utils import category_counts, collect_entries, discover_catalogs, domain_counts, kind_counts
from module_maturity import load_maturity_manifest, maturity_counts, module_level

TOKEN_RE = re.compile(r"[^a-z0-9.+_-]+")
REPOSITORY_URL = "https://github.com/BLCCoreStudio/OpenDevIndex"


def normalize_text(value: object) -> str:
    text = str(value or "").casefold()
    return " ".join(part for part in TOKEN_RE.split(text) if part)


def module_url(module_ref: str) -> str:
    return f"{REPOSITORY_URL}/tree/{module_ref}/entry"


def comparison_url(path: str) -> str:
    return f"{REPOSITORY_URL}/blob/main/docs/comparisons/{path}"


def load_comparison_index(path: Path, known_refs: set[str]) -> dict[str, list[dict]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid comparison index {path}: {exc}") from exc

    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError(f"{path}: comparison index schema_version must be 1")

    modules = data.get("modules")
    if not isinstance(modules, list):
        raise ValueError(f"{path}: comparison index modules must be a list")

    result: dict[str, list[dict]] = {}
    for index, module in enumerate(modules, start=1):
        if not isinstance(module, dict):
            raise ValueError(f"{path}: module record {index} must be a mapping")
        ref = module.get("ref")
        if not isinstance(ref, str) or ref not in known_refs:
            raise ValueError(f"{path}: module record {index} references unknown module {ref!r}")
        if ref in result:
            raise ValueError(f"{path}: duplicate module record {ref}")

        comparisons = module.get("comparisons")
        if not isinstance(comparisons, list) or not comparisons:
            raise ValueError(f"{path}: module {ref} must contain at least one comparison")

        normalized: list[dict] = []
        seen_ids: set[str] = set()
        for comparison_index, comparison in enumerate(comparisons, start=1):
            if not isinstance(comparison, dict):
                raise ValueError(
                    f"{path}: comparison {comparison_index} for {ref} must be a mapping"
                )
            comparison_id = comparison.get("id")
            title = comparison.get("title")
            summary = comparison.get("summary")
            verified_at = comparison.get("verified_at")
            comparison_path = comparison.get("path")
            if not isinstance(comparison_id, str) or not comparison_id:
                raise ValueError(f"{path}: comparison {comparison_index} for {ref} has invalid id")
            if comparison_id in seen_ids:
                raise ValueError(f"{path}: duplicate comparison {comparison_id} for {ref}")
            if not isinstance(title, str) or not title:
                raise ValueError(f"{path}: comparison {comparison_id} for {ref} has invalid title")
            if not isinstance(summary, str) or not summary:
                raise ValueError(f"{path}: comparison {comparison_id} for {ref} has invalid summary")
            if not isinstance(verified_at, str) or not verified_at:
                raise ValueError(f"{path}: comparison {comparison_id} for {ref} has invalid verified_at")
            if not isinstance(comparison_path, str) or comparison_path != f"{comparison_id}.md":
                raise ValueError(
                    f"{path}: comparison {comparison_id} for {ref} must use path {comparison_id}.md"
                )
            seen_ids.add(comparison_id)
            normalized.append(
                {
                    "id": comparison_id,
                    "title": title,
                    "summary": summary,
                    "verified_at": verified_at,
                    "path": comparison_path,
                    "url": comparison_url(comparison_path),
                }
            )

        normalized.sort(key=lambda item: (item["title"].casefold(), item["id"]))
        result[ref] = normalized

    return result


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


def search_text(entry: dict, maturity: str = "overview", comparisons: list[dict] | None = None) -> str:
    coverage = entry.get("coverage") or {}
    comparison_values: list[str] = []
    for comparison in comparisons or []:
        comparison_values.extend([comparison["id"], comparison["title"]])
    values: list[str] = [
        entry["module_ref"],
        entry["id"],
        entry["name"],
        entry["category"],
        entry["kind"],
        maturity,
        entry["summary"],
        *entry.get("domains", []),
        *entry.get("tags", []),
        *entry.get("deployment_types", []),
        entry.get("license", ""),
        coverage.get("area", ""),
        *coverage.get("topics", []),
        *entry.get("use_cases", []),
        *entry.get("key_points", []),
        *comparison_values,
    ]
    return normalize_text(" ".join(values))


def public_record(
    entry: dict,
    maturity: str = "overview",
    comparisons: list[dict] | None = None,
) -> dict:
    coverage = entry.get("coverage") or {}
    comparison_records = list(comparisons or [])
    return {
        "ref": entry["module_ref"],
        "url": module_url(entry["module_ref"]),
        "slug": entry["id"],
        "name": entry["name"],
        "address_category": entry["category"],
        "kind": entry["kind"],
        "maturity": maturity,
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
        "comparison_count": len(comparison_records),
        "comparisons": comparison_records,
    }


def search_record(
    entry: dict,
    maturity: str = "overview",
    comparisons: list[dict] | None = None,
) -> dict:
    record = public_record(entry, maturity, comparisons)
    record["search_text"] = search_text(entry, maturity, comparisons)
    return record


def render_markdown(
    entries: list[dict],
    kinds: dict[str, int],
    domains: dict[str, int],
    coverage_areas: dict[str, int],
    maturity_manifest: dict | None = None,
    comparison_map: dict[str, list[dict]] | None = None,
) -> str:
    comparison_map = comparison_map or {}
    depth_counts = maturity_counts([entry["module_ref"] for entry in entries], maturity_manifest)
    lines = [
        "# OpenDevIndex — Browse the Index",
        "",
        "This file is generated from validated OpenDevIndex catalogs. Each module link opens its independently versioned knowledge entry.",
        "",
        f"**Indexed modules:** {len(entries)}",
        "",
        f"**Modules in curated comparisons:** {len(comparison_map)}",
        "",
        "See [`docs/comparisons/index.md`](docs/comparisons/index.md) for comparison-first browsing or [`docs/comparisons/by-module.md`](docs/comparisons/by-module.md) for the reverse index.",
        "",
        "## Content depth",
        "",
        "Depth describes how far a module has progressed beyond its source-backed overview. See [`docs/MODULE_STANDARD.md`](docs/MODULE_STANDARD.md).",
        "",
        "| Level | Modules |",
        "| --- | ---: |",
    ]
    for level in ("deep-dive", "guide", "overview"):
        if level in depth_counts:
            lines.append(f"| `{level}` | {depth_counts[level]} |")

    lines.extend(["", "## Browse by kind", "", "| Kind | Modules |", "| --- | ---: |"])
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
                    "| Module | Depth | Domains | Comparisons | Summary |",
                    "| --- | --- | --- | --- | --- |",
                ]
            )
        domains_text = ", ".join(f"`{domain}`" for domain in entry.get("domains", []))
        summary = entry["summary"].replace("|", "\\|")
        name = entry["name"].replace("|", "\\|")
        ref = entry["module_ref"]
        maturity = module_level(ref, maturity_manifest)
        comparisons = comparison_map.get(ref, [])
        comparisons_text = "<br>".join(
            f"[{item['title']}](docs/comparisons/{item['path']})" for item in comparisons
        ) or "—"
        lines.append(
            f"| [{name}]({module_url(ref)}) (`{ref}`) | `{maturity}` | {domains_text} | {comparisons_text} | {summary} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "OpenDevIndex separates stable module addresses from taxonomy facets. Legacy addresses remain valid while `kind`, `domains`, schema-v3 coverage metadata, independently reviewed maturity metadata, and curated comparison backlinks provide consistent discovery and filtering.",
            "",
        ]
    )
    return "\n".join(lines)


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build(
    catalog_dir: Path,
    output_dir: Path,
    public_index: Path | None = None,
    maturity_manifest_path: Path | None = None,
    comparison_index_path: Path | None = None,
) -> dict:
    paths = discover_catalogs(catalog_dir)
    entries, catalogs = collect_entries(paths)
    categories = category_counts(entries)
    kinds = kind_counts(entries)
    domains = domain_counts(entries)
    coverage_areas = coverage_area_counts(entries)
    coverage_topics = coverage_topic_counts(entries)
    known_refs = {entry["module_ref"] for entry in entries}

    maturity_manifest = None
    if maturity_manifest_path is not None:
        maturity_manifest = load_maturity_manifest(maturity_manifest_path, known_refs)
    depth_counts = maturity_counts([entry["module_ref"] for entry in entries], maturity_manifest)

    comparison_map: dict[str, list[dict]] = {}
    if comparison_index_path is not None:
        comparison_map = load_comparison_index(comparison_index_path, known_refs)

    output_dir.mkdir(parents=True, exist_ok=True)

    catalog_payload = {
        "schema_version": 3,
        "module_count": len(entries),
        "comparison_linked_module_count": len(comparison_map),
        "address_category_counts": categories,
        "kind_counts": kinds,
        "domain_counts": domains,
        "maturity_counts": depth_counts,
        "coverage_area_counts": coverage_areas,
        "coverage_topic_counts": coverage_topics,
        "catalogs": catalogs,
        "entries": [
            public_record(
                entry,
                module_level(entry["module_ref"], maturity_manifest),
                comparison_map.get(entry["module_ref"], []),
            )
            for entry in entries
        ],
    }
    search_payload = {
        "schema_version": 3,
        "module_count": len(entries),
        "comparison_linked_module_count": len(comparison_map),
        "kind_counts": kinds,
        "domain_counts": domains,
        "maturity_counts": depth_counts,
        "coverage_area_counts": coverage_areas,
        "coverage_topic_counts": coverage_topics,
        "entries": [
            search_record(
                entry,
                module_level(entry["module_ref"], maturity_manifest),
                comparison_map.get(entry["module_ref"], []),
            )
            for entry in entries
        ],
    }

    markdown = render_markdown(
        entries,
        kinds,
        domains,
        coverage_areas,
        maturity_manifest,
        comparison_map,
    )
    write_json(output_dir / "catalog.json", catalog_payload)
    write_json(output_dir / "search.json", search_payload)
    (output_dir / "catalog.md").write_text(markdown, encoding="utf-8")
    if public_index is not None:
        public_index.write_text(markdown, encoding="utf-8")

    return {
        "module_count": len(entries),
        "comparison_linked_module_count": len(comparison_map),
        "address_category_counts": categories,
        "kind_counts": kinds,
        "domain_counts": domains,
        "maturity_counts": depth_counts,
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
    parser.add_argument(
        "--maturity-manifest",
        default="quality/module-maturity.yaml",
        help="Validated Overview / Guide / Deep-dive quality manifest",
    )
    parser.add_argument(
        "--comparison-index",
        help="Optional generated module-comparisons.json to join curated comparison backlinks",
    )
    args = parser.parse_args()

    result = build(
        Path(args.catalog_dir),
        Path(args.output_dir),
        Path(args.public_index) if args.public_index else None,
        Path(args.maturity_manifest) if args.maturity_manifest else None,
        Path(args.comparison_index) if args.comparison_index else None,
    )
    print(
        "OpenDevIndex search index built: "
        f"{result['module_count']} modules, "
        f"{result['comparison_linked_module_count']} comparison-linked -> {result['output_dir']}"
    )
    for kind, count in result["kind_counts"].items():
        print(f"- {kind}: {count}")
    for level, count in result["maturity_counts"].items():
        print(f"- maturity/{level}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
