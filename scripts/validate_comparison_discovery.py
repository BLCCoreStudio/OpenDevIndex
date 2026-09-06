#!/usr/bin/env python3
"""Cross-validate OpenDevIndex comparison discovery artifacts and semantic search cases."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import yaml

from search_comparisons import search as search_comparisons
from search_index import search as search_modules


def _read_json(path: Path, schema_version: int) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != schema_version:
        raise ValueError(f"{path}: schema_version must be {schema_version}")
    return data


def _unique_map(items: object, key: str, context: str) -> dict[str, dict]:
    if not isinstance(items, list):
        raise ValueError(f"{context}: expected a list")
    result: dict[str, dict] = {}
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"{context}: record {index} must be a mapping")
        value = item.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"{context}: record {index} has invalid {key}")
        if value in result:
            raise ValueError(f"{context}: duplicate {key} {value}")
        result[value] = item
    return result


def load_semantic_cases(path: Path, comparison_ids: set[str]) -> list[dict]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError(f"{path}: schema_version must be 1")
    unexpected = set(data) - {"schema_version", "cases"}
    if unexpected:
        raise ValueError(f"{path}: unsupported keys: {', '.join(sorted(unexpected))}")

    raw_cases = data.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError(f"{path}: cases must be a non-empty list")

    cases: list[dict] = []
    seen: set[tuple[str, str]] = set()
    covered: set[str] = set()
    for index, raw in enumerate(raw_cases, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"{path}: case {index} must be a mapping")
        if set(raw) - {"comparison", "query"}:
            raise ValueError(f"{path}: case {index} has unsupported keys")
        comparison_id = raw.get("comparison")
        query = raw.get("query")
        if not isinstance(comparison_id, str) or comparison_id not in comparison_ids:
            raise ValueError(f"{path}: case {index} references unknown comparison {comparison_id!r}")
        if not isinstance(query, str) or not query.strip():
            raise ValueError(f"{path}: case {index} query must be a non-empty string")
        query = " ".join(query.split())
        pair = (comparison_id, query.casefold())
        if pair in seen:
            raise ValueError(f"{path}: duplicate semantic case for {comparison_id}: {query}")
        seen.add(pair)
        covered.add(comparison_id)
        cases.append({"comparison": comparison_id, "query": query})

    missing = sorted(comparison_ids - covered)
    if missing:
        raise ValueError(
            f"{path}: every comparison needs at least one semantic search case; missing {', '.join(missing)}"
        )
    return cases


def validate(
    comparisons_path: Path,
    reverse_index_path: Path,
    comparison_search_path: Path,
    module_search_path: Path,
    semantic_cases_path: Path,
) -> dict:
    comparisons_payload = _read_json(comparisons_path, 1)
    reverse_payload = _read_json(reverse_index_path, 1)
    comparison_search_payload = _read_json(comparison_search_path, 1)
    module_search_payload = _read_json(module_search_path, 3)

    comparisons = _unique_map(comparisons_payload.get("comparisons"), "id", str(comparisons_path))
    reverse = _unique_map(reverse_payload.get("modules"), "ref", str(reverse_index_path))
    comparison_search = _unique_map(
        comparison_search_payload.get("entries"), "id", str(comparison_search_path)
    )
    module_search = _unique_map(module_search_payload.get("entries"), "ref", str(module_search_path))

    if comparisons_payload.get("comparison_count") != len(comparisons):
        raise ValueError(f"{comparisons_path}: comparison_count does not match records")
    if comparison_search_payload.get("comparison_count") != len(comparison_search):
        raise ValueError(f"{comparison_search_path}: comparison_count does not match records")
    if reverse_payload.get("module_count") != len(reverse):
        raise ValueError(f"{reverse_index_path}: module_count does not match records")
    if set(comparisons) != set(comparison_search):
        raise ValueError("comparison/search id mismatch")

    expected_by_module: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for comparison_id, comparison in comparisons.items():
        title = comparison.get("title")
        modules = comparison.get("modules")
        if not isinstance(title, str) or not title:
            raise ValueError(f"{comparison_id}: invalid title")
        if not isinstance(modules, list) or len(modules) < 2:
            raise ValueError(f"{comparison_id}: modules must contain at least two records")

        refs: list[str] = []
        for index, module in enumerate(modules, start=1):
            if not isinstance(module, dict):
                raise ValueError(f"{comparison_id}: module {index} must be a mapping")
            ref = module.get("ref")
            if not isinstance(ref, str) or not ref:
                raise ValueError(f"{comparison_id}: module {index} has invalid ref")
            if ref in refs:
                raise ValueError(f"{comparison_id}: duplicate module {ref}")
            if ref not in module_search:
                raise ValueError(f"{comparison_id}: module {ref} missing from module search index")
            refs.append(ref)
            expected_by_module[ref].append((title, comparison_id))

        compact = comparison_search[comparison_id]
        if compact.get("title") != title or compact.get("module_refs") != refs:
            raise ValueError(f"{comparison_id}: comparison search record drift")

        by_id = search_comparisons(list(comparison_search.values()), comparison_id, limit=len(comparisons) + 1)
        if not by_id or by_id[0].get("id") != comparison_id:
            raise ValueError(f"{comparison_id}: exact id search does not rank itself first")
        by_title = search_comparisons(list(comparison_search.values()), title, limit=len(comparisons) + 1)
        if not by_title or by_title[0].get("id") != comparison_id:
            raise ValueError(f"{comparison_id}: exact title search does not rank itself first")

        members = search_modules(
            list(module_search.values()),
            "",
            comparison=comparison_id,
            limit=len(module_search) + 1,
        )
        actual_refs = {entry.get("ref") for entry in members}
        if actual_refs != set(refs):
            raise ValueError(f"{comparison_id}: module-search membership mismatch")

    expected_linked_refs = set(expected_by_module)
    if set(reverse) != expected_linked_refs:
        raise ValueError("reverse-index module mismatch")

    for ref, pairs in expected_by_module.items():
        pairs.sort(key=lambda item: (item[0].casefold(), item[1]))
        expected_ids = [comparison_id for _, comparison_id in pairs]

        reverse_items = reverse[ref].get("comparisons")
        if not isinstance(reverse_items, list):
            raise ValueError(f"{ref}: reverse-index comparisons must be a list")
        reverse_ids = [item.get("id") for item in reverse_items if isinstance(item, dict)]
        if reverse_ids != expected_ids:
            raise ValueError(
                f"{ref}: reverse-index ordering/membership drift; expected={expected_ids} actual={reverse_ids}"
            )

        module_items = module_search[ref].get("comparisons")
        if not isinstance(module_items, list):
            raise ValueError(f"{ref}: module-search comparisons must be a list")
        module_ids = [item.get("id") for item in module_items if isinstance(item, dict)]
        if module_ids != expected_ids:
            raise ValueError(f"{ref}: module-search backlink drift")
        if module_search[ref].get("comparison_count") != len(expected_ids):
            raise ValueError(f"{ref}: comparison_count does not match backlinks")

        containing = search_comparisons(
            list(comparison_search.values()),
            "",
            module=ref,
            limit=len(comparisons) + 1,
        )
        containing_ids = [entry.get("id") for entry in containing]
        if containing_ids != expected_ids:
            raise ValueError(f"{ref}: comparison-search module membership/order drift")

    if module_search_payload.get("comparison_linked_module_count") != len(expected_linked_refs):
        raise ValueError(f"{module_search_path}: comparison_linked_module_count does not match derived graph")

    cases = load_semantic_cases(semantic_cases_path, set(comparisons))
    comparison_entries = list(comparison_search.values())
    for case in cases:
        results = search_comparisons(comparison_entries, case["query"], limit=len(comparisons) + 1)
        if not results or results[0].get("id") != case["comparison"]:
            actual = results[0].get("id") if results else None
            raise ValueError(
                f"semantic search failed for {case['comparison']!r} query {case['query']!r}: rank-1 was {actual!r}"
            )

    return {
        "schema_version": 1,
        "comparison_count": len(comparisons),
        "linked_module_count": len(expected_linked_refs),
        "multi_comparison_module_count": sum(1 for pairs in expected_by_module.values() if len(pairs) > 1),
        "semantic_case_count": len(cases),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comparisons", default="dist/comparisons/comparisons.json")
    parser.add_argument("--reverse-index", default="dist/comparisons/module-comparisons.json")
    parser.add_argument("--comparison-search", default="dist/comparisons/search.json")
    parser.add_argument("--module-search", default="dist/index/search.json")
    parser.add_argument("--semantic-cases", default="comparisons/_meta/search-smoke.yaml")
    parser.add_argument("--output", default="dist/comparisons/discovery-validation.json")
    args = parser.parse_args()

    try:
        result = validate(
            Path(args.comparisons),
            Path(args.reverse_index),
            Path(args.comparison_search),
            Path(args.module_search),
            Path(args.semantic_cases),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"OpenDevIndex comparison discovery validation failed: {exc}", file=sys.stderr)
        return 1

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "OpenDevIndex comparison discovery validated: "
        f"{result['comparison_count']} comparison(s), "
        f"{result['linked_module_count']} linked module(s), "
        f"{result['multi_comparison_module_count']} multi-comparison module(s), "
        f"{result['semantic_case_count']} semantic search case(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
