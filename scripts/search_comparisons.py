#!/usr/bin/env python3
"""Search generated OpenDevIndex curated comparison artifacts."""

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


def load_index(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(
            f"comparison search index not found: {path}. Run scripts/build_comparison_search.py first."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError(f"{path}: schema_version must be 1")
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise ValueError(f"{path}: expected an entries list")
    return entries


def score_entry(entry: dict, query: str) -> int:
    query_norm = normalize(query)
    query_tokens = tokens(query)
    if not query_tokens:
        return 0

    comparison_id = normalize(entry.get("id"))
    title = normalize(entry.get("title"))
    summary = normalize(entry.get("summary"))
    module_refs = [normalize(value) for value in entry.get("module_refs", [])]
    module_names = [normalize(value) for value in entry.get("module_names", [])]
    dimension_ids = [normalize(value) for value in entry.get("dimension_ids", [])]
    dimension_labels = [normalize(value) for value in entry.get("dimension_labels", [])]
    haystack = entry.get("search_text") or normalize(
        " ".join(
            [
                comparison_id,
                title,
                summary,
                *module_refs,
                *module_names,
                *dimension_ids,
                *dimension_labels,
            ]
        )
    )

    if any(token not in haystack for token in query_tokens):
        return 0

    score = 0
    if query_norm == comparison_id:
        score += 150
    elif query_norm == title:
        score += 140
    elif title.startswith(query_norm):
        score += 90
    elif query_norm in title:
        score += 70

    for token in query_tokens:
        if token == comparison_id:
            score += 50
        elif token in comparison_id:
            score += 30
        if token in title:
            score += 35
        if token in module_refs:
            score += 32
        elif any(token in ref for ref in module_refs):
            score += 20
        if token in module_names:
            score += 30
        elif any(token in name for name in module_names):
            score += 18
        if token in dimension_ids:
            score += 22
        elif any(token in dimension_id for dimension_id in dimension_ids):
            score += 14
        if token in dimension_labels:
            score += 22
        elif any(token in label for label in dimension_labels):
            score += 14
        if token in summary:
            score += 8
        if token in haystack:
            score += 3
    return score


def search(
    entries: list[dict],
    query: str,
    *,
    module: str | None = None,
    limit: int = 10,
) -> list[dict]:
    module_filter = normalize(module) if module else None
    query_norm = normalize(query)
    ranked: list[tuple[int, dict]] = []

    for entry in entries:
        module_refs = [normalize(value) for value in entry.get("module_refs", [])]
        if module_filter and module_filter not in module_refs:
            continue
        if query_norm:
            score = score_entry(entry, query)
            if not score:
                continue
        else:
            score = 1
        ranked.append((score, entry))

    ranked.sort(
        key=lambda item: (
            -item[0],
            item[1].get("title", "").casefold(),
            item[1].get("id", ""),
        )
    )
    return [dict(entry, score=score) for score, entry in ranked[:limit]]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "query",
        nargs="?",
        default="",
        help="Search terms; optional when --module is supplied",
    )
    parser.add_argument("--index", default="dist/comparisons/search.json")
    parser.add_argument(
        "--module",
        help="Return only comparisons containing the exact normalized module ref",
    )
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    if args.limit <= 0:
        parser.error("--limit must be greater than zero")
    if not normalize(args.query) and not args.module:
        parser.error("query is required unless --module is used")

    try:
        entries = load_index(Path(args.index))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"OpenDevIndex comparison search failed: {exc}", file=sys.stderr)
        return 2

    results = search(entries, args.query, module=args.module, limit=args.limit)
    if args.as_json:
        print(json.dumps(results, indent=2, ensure_ascii=False, sort_keys=True))
        return 0

    if not results:
        print("No matching OpenDevIndex comparisons found.")
        return 0

    for number, entry in enumerate(results, start=1):
        modules = ", ".join(entry.get("module_names", []))
        print(f"{number}. {entry['title']} [{entry['id']}] — score {entry['score']}")
        print(f"   modules: {modules or 'none'}")
        print(
            f"   dimensions: {entry.get('dimension_count', 0)} | "
            f"decision rules: {entry.get('decision_rule_count', 0)} | "
            f"verified: {entry.get('verified_at', 'unknown')}"
        )
        print(f"   {entry['summary']}")
        if entry.get("url"):
            print(f"   comparison: {entry['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
