#!/usr/bin/env python3
"""Build a deterministic search artifact from curated comparison records."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TOKEN_RE = re.compile(r"[^a-z0-9.+_-]+")
REPOSITORY_URL = "https://github.com/BLCCoreStudio/OpenDevIndex"


def normalize(value: object) -> str:
    return " ".join(
        part for part in TOKEN_RE.split(str(value or "").casefold()) if part
    )


def comparison_url(comparison_id: str) -> str:
    return f"{REPOSITORY_URL}/blob/main/docs/comparisons/{comparison_id}.md"


def _load_payload(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid comparison artifact {path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError(f"{path}: schema_version must be 1")
    comparisons = data.get("comparisons")
    if not isinstance(comparisons, list):
        raise ValueError(f"{path}: comparisons must be a list")
    return data


def _require_string(record: dict, field: str, *, context: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}: {field} must be a non-empty string")
    return value.strip()


def search_record(record: dict) -> dict:
    comparison_id = _require_string(record, "id", context="comparison")
    title = _require_string(record, "title", context=comparison_id)
    summary = _require_string(record, "summary", context=comparison_id)
    verified_at = _require_string(record, "verified_at", context=comparison_id)

    modules = record.get("modules")
    dimensions = record.get("dimensions")
    decision_rules = record.get("decision_rules", [])
    notes = record.get("notes", [])
    if not isinstance(modules, list) or len(modules) < 2:
        raise ValueError(f"{comparison_id}: modules must contain at least two records")
    if not isinstance(dimensions, list) or not dimensions:
        raise ValueError(f"{comparison_id}: dimensions must be a non-empty list")
    if not isinstance(decision_rules, list):
        raise ValueError(f"{comparison_id}: decision_rules must be a list")
    if not isinstance(notes, list):
        raise ValueError(f"{comparison_id}: notes must be a list")

    module_refs: list[str] = []
    module_names: list[str] = []
    module_summaries: list[str] = []
    for index, module in enumerate(modules, start=1):
        if not isinstance(module, dict):
            raise ValueError(f"{comparison_id}: module {index} must be a mapping")
        module_refs.append(_require_string(module, "ref", context=f"{comparison_id} module {index}"))
        module_names.append(_require_string(module, "name", context=f"{comparison_id} module {index}"))
        module_summaries.append(_require_string(module, "summary", context=f"{comparison_id} module {index}"))

    dimension_ids: list[str] = []
    dimension_labels: list[str] = []
    dimension_values: list[str] = []
    for index, dimension in enumerate(dimensions, start=1):
        if not isinstance(dimension, dict):
            raise ValueError(f"{comparison_id}: dimension {index} must be a mapping")
        dimension_ids.append(_require_string(dimension, "id", context=f"{comparison_id} dimension {index}"))
        dimension_labels.append(_require_string(dimension, "label", context=f"{comparison_id} dimension {index}"))
        values = dimension.get("values")
        if not isinstance(values, dict):
            raise ValueError(f"{comparison_id}: dimension {index} values must be a mapping")
        for value in values.values():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{comparison_id}: dimension {index} contains an invalid value")
            dimension_values.append(value.strip())

    decision_conditions: list[str] = []
    decision_reasons: list[str] = []
    decision_consider: list[str] = []
    for index, rule in enumerate(decision_rules, start=1):
        if not isinstance(rule, dict):
            raise ValueError(f"{comparison_id}: decision rule {index} must be a mapping")
        decision_conditions.append(_require_string(rule, "condition", context=f"{comparison_id} decision rule {index}"))
        decision_reasons.append(_require_string(rule, "reason", context=f"{comparison_id} decision rule {index}"))
        consider = rule.get("consider")
        if not isinstance(consider, list):
            raise ValueError(f"{comparison_id}: decision rule {index} consider must be a list")
        decision_consider.extend(str(value) for value in consider)

    normalized_notes: list[str] = []
    for index, note in enumerate(notes, start=1):
        if not isinstance(note, str) or not note.strip():
            raise ValueError(f"{comparison_id}: note {index} must be a non-empty string")
        normalized_notes.append(note.strip())

    searchable_values = [
        comparison_id,
        title,
        summary,
        *module_refs,
        *module_names,
        *module_summaries,
        *dimension_ids,
        *dimension_labels,
        *dimension_values,
        *decision_conditions,
        *decision_reasons,
        *decision_consider,
        *normalized_notes,
    ]

    return {
        "id": comparison_id,
        "title": title,
        "summary": summary,
        "verified_at": verified_at,
        "path": f"{comparison_id}.md",
        "url": comparison_url(comparison_id),
        "module_count": len(module_refs),
        "module_refs": module_refs,
        "module_names": module_names,
        "dimension_count": len(dimension_ids),
        "dimension_ids": dimension_ids,
        "dimension_labels": dimension_labels,
        "decision_rule_count": len(decision_rules),
        "search_text": normalize(" ".join(searchable_values)),
    }


def build(input_path: Path, output_path: Path) -> dict:
    payload = _load_payload(input_path)
    entries: list[dict] = []
    seen_ids: set[str] = set()
    for raw in payload["comparisons"]:
        if not isinstance(raw, dict):
            raise ValueError(f"{input_path}: every comparison must be a mapping")
        record = search_record(raw)
        if record["id"] in seen_ids:
            raise ValueError(f"{input_path}: duplicate comparison id {record['id']}")
        seen_ids.add(record["id"])
        entries.append(record)

    entries.sort(key=lambda item: (item["title"].casefold(), item["id"]))
    output = {
        "schema_version": 1,
        "comparison_count": len(entries),
        "entries": entries,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="dist/comparisons/comparisons.json")
    parser.add_argument("--output", default="dist/comparisons/search.json")
    args = parser.parse_args()

    try:
        payload = build(Path(args.input), Path(args.output))
    except (OSError, ValueError) as exc:
        print(f"OpenDevIndex comparison search build failed: {exc}", file=sys.stderr)
        return 1

    print(
        "OpenDevIndex comparison search built: "
        f"{payload['comparison_count']} comparison(s) -> {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
