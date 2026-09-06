#!/usr/bin/env python3
"""Validate and build deterministic OpenDevIndex comparison views."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import yaml

from catalog_utils import collect_entries, discover_catalogs
from module_maturity import load_maturity_manifest, module_level

REPOSITORY_URL = "https://github.com/BLCCoreStudio/OpenDevIndex"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
MODULE_REF_RE = re.compile(r"^[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9._-]*$")
ALLOWED_TOP_LEVEL_KEYS = {
    "schema_version",
    "id",
    "title",
    "summary",
    "verified_at",
    "modules",
    "dimensions",
    "decision_rules",
    "notes",
}
ALLOWED_DIMENSION_KEYS = {"id", "label", "values"}
ALLOWED_DECISION_KEYS = {"condition", "consider", "reason"}


def _read_yaml(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top level must be a mapping")
    return data


def _clean_text(value: object, *, path: Path, field: str, minimum: int, maximum: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{path}: {field} must be a string")
    text = " ".join(value.split())
    if not minimum <= len(text) <= maximum:
        raise ValueError(f"{path}: {field} must be {minimum}-{maximum} characters")
    return text


def load_comparison(path: Path, known_refs: set[str]) -> dict:
    data = _read_yaml(path)

    unexpected = set(data) - ALLOWED_TOP_LEVEL_KEYS
    if unexpected:
        raise ValueError(f"{path}: unsupported keys: {', '.join(sorted(unexpected))}")
    if data.get("schema_version") != 1:
        raise ValueError(f"{path}: schema_version must be 1")

    comparison_id = data.get("id")
    if not isinstance(comparison_id, str) or not SLUG_RE.fullmatch(comparison_id):
        raise ValueError(f"{path}: id must be a lowercase slug")
    if path.stem != comparison_id:
        raise ValueError(f"{path}: filename must match id ({comparison_id}.yaml)")

    title = _clean_text(data.get("title"), path=path, field="title", minimum=4, maximum=120)
    summary = _clean_text(data.get("summary"), path=path, field="summary", minimum=40, maximum=320)

    verified_at = data.get("verified_at")
    try:
        verified_date = dt.date.fromisoformat(str(verified_at))
    except ValueError as exc:
        raise ValueError(f"{path}: verified_at must be YYYY-MM-DD") from exc
    if verified_date > dt.date.today():
        raise ValueError(f"{path}: verified_at cannot be in the future")

    modules = data.get("modules")
    if not isinstance(modules, list) or not 2 <= len(modules) <= 6:
        raise ValueError(f"{path}: modules must contain 2-6 module references")
    if len(set(modules)) != len(modules):
        raise ValueError(f"{path}: modules must be unique")
    normalized_modules: list[str] = []
    for ref in modules:
        if not isinstance(ref, str) or not MODULE_REF_RE.fullmatch(ref):
            raise ValueError(f"{path}: invalid module reference {ref!r}")
        if ref not in known_refs:
            raise ValueError(f"{path}: comparison references unknown module {ref}")
        normalized_modules.append(ref)
    module_set = set(normalized_modules)

    raw_dimensions = data.get("dimensions")
    if not isinstance(raw_dimensions, list) or not 2 <= len(raw_dimensions) <= 24:
        raise ValueError(f"{path}: dimensions must contain 2-24 entries")

    dimension_ids: set[str] = set()
    dimensions: list[dict] = []
    for index, raw in enumerate(raw_dimensions, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"{path}: dimension {index} must be a mapping")
        unexpected_dimension = set(raw) - ALLOWED_DIMENSION_KEYS
        if unexpected_dimension:
            raise ValueError(
                f"{path}: dimension {index} has unsupported keys: "
                f"{', '.join(sorted(unexpected_dimension))}"
            )

        dimension_id = raw.get("id")
        if not isinstance(dimension_id, str) or not SLUG_RE.fullmatch(dimension_id):
            raise ValueError(f"{path}: dimension {index} id must be a lowercase slug")
        if dimension_id in dimension_ids:
            raise ValueError(f"{path}: duplicate dimension id {dimension_id}")
        dimension_ids.add(dimension_id)

        label = _clean_text(
            raw.get("label"), path=path, field=f"dimension {dimension_id} label", minimum=2, maximum=80
        )
        values = raw.get("values")
        if not isinstance(values, dict):
            raise ValueError(f"{path}: dimension {dimension_id} values must be a mapping")
        if set(values) != module_set:
            missing = sorted(module_set - set(values))
            extra = sorted(set(values) - module_set)
            parts: list[str] = []
            if missing:
                parts.append(f"missing {', '.join(missing)}")
            if extra:
                parts.append(f"unexpected {', '.join(extra)}")
            raise ValueError(f"{path}: dimension {dimension_id} values must cover every module ({'; '.join(parts)})")

        normalized_values = {
            ref: _clean_text(
                values[ref],
                path=path,
                field=f"dimension {dimension_id} value for {ref}",
                minimum=1,
                maximum=420,
            )
            for ref in normalized_modules
        }
        dimensions.append({"id": dimension_id, "label": label, "values": normalized_values})

    decision_rules: list[dict] = []
    raw_rules = data.get("decision_rules", [])
    if not isinstance(raw_rules, list) or len(raw_rules) > 16:
        raise ValueError(f"{path}: decision_rules must be a list with at most 16 entries")
    for index, raw in enumerate(raw_rules, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"{path}: decision rule {index} must be a mapping")
        unexpected_rule = set(raw) - ALLOWED_DECISION_KEYS
        if unexpected_rule:
            raise ValueError(
                f"{path}: decision rule {index} has unsupported keys: "
                f"{', '.join(sorted(unexpected_rule))}"
            )
        condition = _clean_text(
            raw.get("condition"), path=path, field=f"decision rule {index} condition", minimum=8, maximum=240
        )
        reason = _clean_text(
            raw.get("reason"), path=path, field=f"decision rule {index} reason", minimum=8, maximum=320
        )
        consider = raw.get("consider")
        if not isinstance(consider, list) or not consider:
            raise ValueError(f"{path}: decision rule {index} consider must be a non-empty list")
        if len(set(consider)) != len(consider):
            raise ValueError(f"{path}: decision rule {index} consider values must be unique")
        for ref in consider:
            if ref not in module_set:
                raise ValueError(f"{path}: decision rule {index} references module outside comparison: {ref}")
        decision_rules.append({"condition": condition, "consider": list(consider), "reason": reason})

    notes: list[str] = []
    raw_notes = data.get("notes", [])
    if not isinstance(raw_notes, list) or len(raw_notes) > 12:
        raise ValueError(f"{path}: notes must be a list with at most 12 entries")
    for index, note in enumerate(raw_notes, start=1):
        notes.append(
            _clean_text(note, path=path, field=f"note {index}", minimum=8, maximum=320)
        )

    return {
        "schema_version": 1,
        "id": comparison_id,
        "title": title,
        "summary": summary,
        "verified_at": str(verified_at),
        "modules": normalized_modules,
        "dimensions": dimensions,
        "decision_rules": decision_rules,
        "notes": notes,
    }


def module_url(module_ref: str) -> str:
    return f"{REPOSITORY_URL}/tree/{module_ref}/entry"


def comparison_record(comparison: dict, entries_by_ref: dict[str, dict], maturity_manifest: dict | None) -> dict:
    modules = []
    for ref in comparison["modules"]:
        entry = entries_by_ref[ref]
        modules.append(
            {
                "ref": ref,
                "name": entry["name"],
                "url": module_url(ref),
                "maturity": module_level(ref, maturity_manifest),
                "summary": entry["summary"],
            }
        )
    return {**comparison, "modules": modules}


def build_module_comparison_index(records: list[dict]) -> list[dict]:
    modules: dict[str, dict] = {}
    for record in records:
        comparison_link = {
            "id": record["id"],
            "title": record["title"],
            "summary": record["summary"],
            "verified_at": record["verified_at"],
            "path": f"{record['id']}.md",
        }
        for module in record["modules"]:
            item = modules.setdefault(
                module["ref"],
                {
                    "ref": module["ref"],
                    "name": module["name"],
                    "url": module["url"],
                    "maturity": module["maturity"],
                    "summary": module["summary"],
                    "comparisons": [],
                },
            )
            item["comparisons"].append(dict(comparison_link))

    result = sorted(modules.values(), key=lambda item: (item["name"].casefold(), item["ref"]))
    for module in result:
        module["comparisons"].sort(key=lambda item: (item["title"].casefold(), item["id"]))
    return result


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def render_comparison(record: dict) -> str:
    modules = record["modules"]
    refs = [module["ref"] for module in modules]
    names = {module["ref"]: module["name"] for module in modules}
    urls = {module["ref"]: module["url"] for module in modules}

    lines = [
        f"# {record['title']}",
        "",
        record["summary"],
        "",
        f"**Verified:** {record['verified_at']}",
        "",
        "## Compared modules",
        "",
    ]
    for module in modules:
        lines.append(
            f"- [{module['name']}]({module['url']}) (`{module['ref']}`) — `{module['maturity']}` — {module['summary']}"
        )

    lines.extend(["", "## Comparison", ""])
    header = "| Dimension | " + " | ".join(f"[{names[ref]}]({urls[ref]})" for ref in refs) + " |"
    separator = "| --- | " + " | ".join("---" for _ in refs) + " |"
    lines.extend([header, separator])
    for dimension in record["dimensions"]:
        values = " | ".join(_escape_table(dimension["values"][ref]) for ref in refs)
        lines.append(f"| **{_escape_table(dimension['label'])}** | {values} |")

    if record["decision_rules"]:
        lines.extend(["", "## Decision guide", ""])
        for rule in record["decision_rules"]:
            considered = ", ".join(f"[{names[ref]}]({urls[ref]})" for ref in rule["consider"])
            lines.append(f"- **When:** {rule['condition']} **Consider:** {considered}. {rule['reason']}")

    if record["notes"]:
        lines.extend(["", "## Notes", ""])
        lines.extend(f"- {note}" for note in record["notes"])

    lines.extend(
        [
            "",
            "## Source discipline",
            "",
            "This is a curated navigation and trade-off view, not a benchmark or ranking. Technical claims should remain consistent with the linked OpenDevIndex modules and their authoritative source lists. Follow each module for architecture details, version-sensitive facts, and verification history.",
            "",
        ]
    )
    return "\n".join(lines)


def render_index(records: list[dict]) -> str:
    lines = [
        "# OpenDevIndex Comparisons",
        "",
        "Curated comparison views connect technologies that solve related problems without reducing them to popularity rankings or generic scorecards.",
        "",
        "[Browse comparisons by module](by-module.md)",
        "",
    ]
    for record in records:
        lines.extend(
            [
                f"## [{record['title']}]({record['id']}.md)",
                "",
                record["summary"],
                "",
                "Compared modules: " + ", ".join(f"`{module['ref']}`" for module in record["modules"]),
                "",
            ]
        )
    return "\n".join(lines)


def render_module_index(modules: list[dict]) -> str:
    lines = [
        "# Comparisons by module",
        "",
        "This reverse index shows every OpenDevIndex module currently included in at least one curated comparison.",
        "",
        "[Browse all comparisons](index.md)",
        "",
    ]
    for module in modules:
        lines.extend(
            [
                f"## [{module['name']}]({module['url']})",
                "",
                f"`{module['ref']}` — `{module['maturity']}`",
                "",
            ]
        )
        for comparison in module["comparisons"]:
            lines.append(
                f"- [{comparison['title']}]({comparison['path']}) — {comparison['summary']}"
            )
        lines.append("")
    return "\n".join(lines)


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _write_markdown_set(target_dir: Path, records: list[dict], modules: list[dict]) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    for stale in target_dir.glob("*.md"):
        stale.unlink()
    (target_dir / "index.md").write_text(render_index(records), encoding="utf-8")
    (target_dir / "by-module.md").write_text(render_module_index(modules), encoding="utf-8")
    for record in records:
        (target_dir / f"{record['id']}.md").write_text(render_comparison(record), encoding="utf-8")


def build(
    comparisons_dir: Path,
    catalog_dir: Path,
    output_dir: Path,
    maturity_manifest_path: Path | None = None,
    public_dir: Path | None = None,
) -> dict:
    entries, _ = collect_entries(discover_catalogs(catalog_dir))
    entries_by_ref = {entry["module_ref"]: entry for entry in entries}
    known_refs = set(entries_by_ref)

    maturity_manifest = None
    if maturity_manifest_path is not None:
        maturity_manifest = load_maturity_manifest(maturity_manifest_path, known_refs)

    paths = sorted(path for path in comparisons_dir.glob("*.yaml") if path.is_file())
    if not paths:
        raise ValueError(f"no comparison YAML files found in {comparisons_dir}")

    records: list[dict] = []
    seen_ids: set[str] = set()
    for path in paths:
        comparison = load_comparison(path, known_refs)
        if comparison["id"] in seen_ids:
            raise ValueError(f"duplicate comparison id {comparison['id']}")
        seen_ids.add(comparison["id"])
        records.append(comparison_record(comparison, entries_by_ref, maturity_manifest))

    module_index = build_module_comparison_index(records)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        output_dir / "comparisons.json",
        {"schema_version": 1, "comparison_count": len(records), "comparisons": records},
    )
    write_json(
        output_dir / "module-comparisons.json",
        {"schema_version": 1, "module_count": len(module_index), "modules": module_index},
    )
    _write_markdown_set(output_dir, records, module_index)
    if public_dir is not None:
        _write_markdown_set(public_dir, records, module_index)

    return {
        "comparison_count": len(records),
        "comparison_ids": [record["id"] for record in records],
        "module_count": len(module_index),
        "output_dir": output_dir.as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comparisons-dir", default="comparisons")
    parser.add_argument("--catalog-dir", default="catalog")
    parser.add_argument("--output-dir", default="dist/comparisons")
    parser.add_argument("--maturity-manifest", default="quality/module-maturity.yaml")
    parser.add_argument("--public-dir")
    args = parser.parse_args()

    try:
        result = build(
            Path(args.comparisons_dir),
            Path(args.catalog_dir),
            Path(args.output_dir),
            Path(args.maturity_manifest) if args.maturity_manifest else None,
            Path(args.public_dir) if args.public_dir else None,
        )
    except (OSError, ValueError) as exc:
        print(f"OpenDevIndex comparison build failed: {exc}", file=sys.stderr)
        return 1

    print(
        "OpenDevIndex comparisons built: "
        f"{result['comparison_count']} view(s), {result['module_count']} indexed module(s) -> {result['output_dir']}"
    )
    for comparison_id in result["comparison_ids"]:
        print(f"- {comparison_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
