#!/usr/bin/env python3
"""Measure validated catalog coverage against the 10,000-module plan."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import yaml

from catalog_utils import collect_entries, discover_catalogs

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALLOCATION = ROOT / "coverage/topic-allocation-v1.yaml"


def load_allocation(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError(f"{path}: invalid topic allocation")
    return data


def build_progress(catalog_dir: Path, allocation_path: Path = DEFAULT_ALLOCATION) -> dict:
    allocation = load_allocation(allocation_path)
    entries, _ = collect_entries(discover_catalogs(catalog_dir))

    area_counts: Counter[str] = Counter()
    topic_counts: Counter[str] = Counter()
    mapped_modules = 0
    for entry in entries:
        coverage = entry.get("coverage") or {}
        area = coverage.get("area")
        topics = coverage.get("topics", [])
        if not isinstance(area, str) or not area:
            continue
        mapped_modules += 1
        area_counts[area] += 1
        for topic in topics:
            if isinstance(topic, str):
                topic_counts[f"{area}/{topic}"] += 1

    areas: list[dict] = []
    topics: list[dict] = []
    for area in allocation.get("areas", []):
        area_id = area["id"]
        target = int(area["target_modules"])
        mapped = int(area_counts.get(area_id, 0))
        areas.append(
            {
                "area": area_id,
                "mapped": mapped,
                "target": target,
                "remaining": max(target - mapped, 0),
                "percent": round((mapped / target) * 100, 2) if target else 0.0,
            }
        )
        for topic, topic_target in area.get("topic_targets", {}).items():
            key = f"{area_id}/{topic}"
            topic_mapped = int(topic_counts.get(key, 0))
            topic_target = int(topic_target)
            topics.append(
                {
                    "topic": key,
                    "mapped": topic_mapped,
                    "target": topic_target,
                    "remaining": max(topic_target - topic_mapped, 0),
                    "percent": round((topic_mapped / topic_target) * 100, 2) if topic_target else 0.0,
                }
            )

    target_modules = int(allocation["target_modules"])
    return {
        "schema_version": 1,
        "catalog_modules": len(entries),
        "mapped_modules": mapped_modules,
        "unmapped_modules": len(entries) - mapped_modules,
        "target_modules": target_modules,
        "overall_percent": round((mapped_modules / target_modules) * 100, 2) if target_modules else 0.0,
        "areas": areas,
        "topics": topics,
    }


def render_markdown(progress: dict) -> str:
    lines = [
        "# OpenDevIndex Coverage Progress",
        "",
        "This report counts only validated catalog modules with explicit schema v3 coverage metadata. Planned slots are never counted as published knowledge.",
        "",
        f"- Validated catalog modules: **{progress['catalog_modules']}**",
        f"- Coverage-mapped modules: **{progress['mapped_modules']}**",
        f"- Unmapped legacy modules: **{progress['unmapped_modules']}**",
        f"- Technology Universe target: **{progress['target_modules']}**",
        f"- Overall mapped progress: **{progress['overall_percent']:.2f}%**",
        "",
        "## Areas",
        "",
        "| Area | Mapped | Target | Remaining | Progress |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in progress["areas"]:
        lines.append(
            f"| `{row['area']}` | {row['mapped']} | {row['target']} | {row['remaining']} | {row['percent']:.2f}% |"
        )

    lines.extend(
        [
            "",
            "## Topics with mapped modules",
            "",
            "| Topic | Mapped | Target | Remaining | Progress |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    mapped_topics = [row for row in progress["topics"] if row["mapped"]]
    if mapped_topics:
        for row in mapped_topics:
            lines.append(
                f"| `{row['topic']}` | {row['mapped']} | {row['target']} | {row['remaining']} | {row['percent']:.2f}% |"
            )
    else:
        lines.append("| _No schema v3 topic mappings published yet_ | 0 | — | — | — |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog-dir", default="catalog")
    parser.add_argument("--allocation", default="coverage/topic-allocation-v1.yaml")
    parser.add_argument("--json-output")
    parser.add_argument("--markdown-output")
    args = parser.parse_args()

    progress = build_progress(Path(args.catalog_dir), Path(args.allocation))
    if args.json_output:
        Path(args.json_output).write_text(
            json.dumps(progress, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    markdown = render_markdown(progress)
    if args.markdown_output:
        Path(args.markdown_output).write_text(markdown, encoding="utf-8")
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
