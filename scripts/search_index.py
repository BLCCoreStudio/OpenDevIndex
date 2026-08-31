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


def score_entry(entry: dict, query: str) -> int:
    query_norm = normalize(query)
    query_tokens = tokens(query)
    if not query_tokens:
        return 0

    name = normalize(entry.get("name"))
    slug = normalize(entry.get("slug"))
    ref = normalize(entry.get("ref"))
    category = normalize(entry.get("category"))
    summary = normalize(entry.get("summary"))
    tags = [normalize(tag) for tag in entry.get("tags", [])]
    use_cases = normalize(" ".join(entry.get("use_cases", [])))
    key_points = normalize(" ".join(entry.get("key_points", [])))
    haystack = entry.get("search_text") or normalize(
        " ".join([ref, slug, name, category, summary, *tags, use_cases, key_points])
    )

    if any(token not in haystack for token in query_tokens):
        return 0

    score = 0
    if query_norm in {name, slug, ref}:
        score += 120
    elif name.startswith(query_norm) or slug.startswith(query_norm):
        score += 70
    elif query_norm in name:
        score += 45

    for token in query_tokens:
        if token == name or token == slug:
            score += 35
        if token in name:
            score += 22
        if token == category:
            score += 16
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

    return score


def search(entries: list[dict], query: str, category: str | None, limit: int) -> list[dict]:
    ranked: list[tuple[int, dict]] = []
    for entry in entries:
        if category and entry.get("category") != category:
            continue
        score = score_entry(entry, query)
        if score:
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
    parser.add_argument("query", help="Search terms")
    parser.add_argument("--index", default="dist/index/search.json")
    parser.add_argument("--category")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    if args.limit <= 0:
        parser.error("--limit must be greater than zero")

    try:
        entries = load_index(Path(args.index))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"OpenDevIndex search failed: {exc}", file=sys.stderr)
        return 2

    results = search(entries, args.query, args.category, args.limit)
    if args.as_json:
        print(json.dumps(results, indent=2, ensure_ascii=False, sort_keys=True))
        return 0

    if not results:
        print("No matching OpenDevIndex modules found.")
        return 0

    for number, entry in enumerate(results, start=1):
        tags = ", ".join(entry.get("tags", []))
        print(f"{number}. {entry['name']} [{entry['ref']}] — score {entry['score']}")
        print(f"   {entry['summary']}")
        if tags:
            print(f"   tags: {tags}")
        if entry.get("homepage"):
            print(f"   {entry['homepage']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
