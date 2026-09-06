#!/usr/bin/env python3
"""Search generated OpenDevIndex artifacts from the command line."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TOKEN_RE = re.compile(r"[^a-z0-9.+_-]+")


def normalize(value: object) -> str:
    return " ".join(
        part for part in TOKEN_RE.split(str(value or "").casefold()) if part
    )


def tokens(value: str) -> list[str]:
    return normalize(value).split()


def comparison_search_fields(entry: dict) -> tuple[list[str], list[str]]:
    ids: list[str] = []
    titles: list[str] = []
    for comparison in entry.get("comparisons", []):
        if not isinstance(comparison, dict):
            continue
        comparison_id = normalize(comparison.get("id"))
        title = normalize(comparison.get("title"))
        if comparison_id:
            ids.append(comparison_id)
        if title:
            titles.append(title)
    return ids, titles


def has_curated_comparison(entry: dict) -> bool:
    comparison_ids, _ = comparison_search_fields(entry)
    return bool(comparison_ids)


def score_entry(entry: dict, query: str) -> int:
    query_norm = normalize(query)
    query_tokens = tokens(query)
    if not query_tokens:
        return 0

    name = normalize(entry.get("name"))
    slug = normalize(entry.get("slug"))
    ref = normalize(entry.get("ref"))
    category = normalize(entry.get("address_category") or entry.get("category"))
    kind = normalize(entry.get("kind"))
    maturity = normalize(entry.get("maturity"))
    domains = [normalize(value) for value in entry.get("domains", [])]
    coverage_area = normalize(entry.get("coverage_area"))
    coverage_topics = [normalize(value) for value in entry.get("coverage_topics", [])]
    summary = normalize(entry.get("summary"))
    tags = [normalize(tag) for tag in entry.get("tags", [])]
    deployment = [normalize(value) for value in entry.get("deployment_types", [])]
    use_cases = normalize(" ".join(entry.get("use_cases", [])))
    key_points = normalize(" ".join(entry.get("key_points", [])))
    comparison_ids, comparison_titles = comparison_search_fields(entry)
    comparison_text = normalize(" ".join([*comparison_ids, *comparison_titles]))
    haystack = entry.get("search_text") or normalize(
        " ".join([
            ref, slug, name, category, kind, maturity, summary, coverage_area,
            *coverage_topics, *domains, *tags, *deployment, use_cases, key_points,
            comparison_text,
        ])
    )

    if any(token not in haystack for token in query_tokens):
        return 0

    score = 0
    if query_norm in {name, slug, ref}:
        score += 120
    elif query_norm in comparison_ids:
        score += 90
    elif query_norm in comparison_titles:
        score += 80
    elif name.startswith(query_norm) or slug.startswith(query_norm):
        score += 70
    elif query_norm in name:
        score += 45
    elif any(query_norm in title for title in comparison_titles):
        score += 35

    for token in query_tokens:
        if token == name or token == slug:
            score += 35
        if token in name:
            score += 22
        if token == kind:
            score += 20
        if token == maturity:
            score += 12
        if token == category:
            score += 12
        if token == coverage_area:
            score += 22
        if token in coverage_topics:
            score += 22
        if token in domains:
            score += 20
        if token in tags:
            score += 18
        elif any(token in tag for tag in tags):
            score += 10
        if token in summary:
            score += 7
        if token in use_cases:
            score += 4
        if token in key_points:
            score += 4
        if token in comparison_ids:
            score += 24
        elif any(token in comparison_id for comparison_id in comparison_ids):
            score += 14
        if any(token == title for title in comparison_titles):
            score += 20
        elif any(token in title for title in comparison_titles):
            score += 12

    return score


def search(
    entries: list[dict],
    query: str,
    category: str | None = None,
    limit: int = 10,
    *,
    kind: str | None = None,
    maturity: str | None = None,
    domain: str | None = None,
    deployment: str | None = None,
    license_value: str | None = None,
    coverage_area: str | None = None,
    coverage_topic: str | None = None,
    has_comparison: bool = False,
    comparison: str | None = None,
) -> list[dict]:
    ranked: list[tuple[int, dict]] = []
    query_norm = normalize(query)
    comparison_filter = normalize(comparison) if comparison else None

    for entry in entries:
        address_category = entry.get("address_category") or entry.get("category")
        comparison_ids, _ = comparison_search_fields(entry)
        if category and address_category != category:
            continue
        if kind and entry.get("kind") != kind:
            continue
        if maturity and entry.get("maturity", "overview") != maturity:
            continue
        if domain and domain not in entry.get("domains", []):
            continue
        if deployment and deployment not in entry.get("deployment_types", []):
            continue
        if license_value and normalize(entry.get("license")) != normalize(license_value):
            continue
        if coverage_area and entry.get("coverage_area") != coverage_area:
            continue
        if coverage_topic and coverage_topic not in entry.get("coverage_topics", []):
            continue
        if has_comparison and not comparison_ids:
            continue
        if comparison_filter and comparison_filter not in comparison_ids:
            continue

        if query_norm:
            score = score_entry(entry, query)
            if not score:
                continue
        else:
            score = 1
        ranked.append((score, entry))

    ranked.sort(key=lambda item: (-item[0], item[1].get("name", "").casefold(), item[1].get("ref", "")))
    return [dict(entry, score=score) for score, entry in ranked[:limit]]


def load_index(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(
            f"search index not found: {path}. Run scripts/build_index.py first."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("entries") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise ValueError(f"{path}: expected an object with an entries list")
    return entries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "query",
        nargs="?",
        default="",
        help="Search terms; optional when --has-comparison or --comparison is used",
    )
    parser.add_argument("--index", default="dist/index/search.json")
    parser.add_argument("--category", help="Legacy/stable address namespace filter")
    parser.add_argument("--kind", help="Canonical taxonomy kind filter")
    parser.add_argument("--maturity", choices=["overview", "guide", "deep-dive"], help="Module content-depth filter")
    parser.add_argument("--domain", help="Domain facet filter")
    parser.add_argument("--coverage-area", help="Technology Universe area filter")
    parser.add_argument("--coverage-topic", help="Technology Universe topic filter")
    parser.add_argument("--deployment", help="Deployment-type filter")
    parser.add_argument("--license", dest="license_value", help="Exact license metadata filter")
    parser.add_argument(
        "--has-comparison",
        action="store_true",
        help="Return only modules that participate in at least one curated comparison",
    )
    parser.add_argument(
        "--comparison",
        help="Return only modules participating in the exact curated comparison id",
    )
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    if args.limit <= 0:
        parser.error("--limit must be greater than zero")
    if not normalize(args.query) and not args.has_comparison and not args.comparison:
        parser.error("query is required unless --has-comparison or --comparison is used")

    try:
        entries = load_index(Path(args.index))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"OpenDevIndex search failed: {exc}", file=sys.stderr)
        return 2

    results = search(
        entries,
        args.query,
        args.category,
        args.limit,
        kind=args.kind,
        maturity=args.maturity,
        domain=args.domain,
        deployment=args.deployment,
        license_value=args.license_value,
        coverage_area=args.coverage_area,
        coverage_topic=args.coverage_topic,
        has_comparison=args.has_comparison,
        comparison=args.comparison,
    )
    if args.as_json:
        print(json.dumps(results, indent=2, ensure_ascii=False, sort_keys=True))
        return 0

    if not results:
        print("No matching OpenDevIndex modules found.")
        return 0

    for number, entry in enumerate(results, start=1):
        domains = ", ".join(entry.get("domains", []))
        coverage = entry.get("coverage_area") or "unmapped"
        topics_text = ", ".join(entry.get("coverage_topics", [])) or "none"
        print(f"{number}. {entry['name']} [{entry['ref']}] — score {entry['score']}")
        print(
            f"   kind: {entry.get('kind', 'unknown')} | "
            f"depth: {entry.get('maturity', 'overview')} | domains: {domains or 'none'}"
        )
        print(f"   coverage: {coverage} | topics: {topics_text}")
        print(f"   {entry['summary']}")
        if entry.get("url"):
            print(f"   module: {entry['url']}")
        for comparison_item in entry.get("comparisons", []):
            if not isinstance(comparison_item, dict):
                continue
            title = comparison_item.get("title")
            url = comparison_item.get("url")
            if title and url:
                print(f"   comparison: {title} — {url}")
        if entry.get("homepage"):
            print(f"   homepage: {entry['homepage']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
