#!/usr/bin/env python3
"""Score OpenDevIndex catalog entries against an editorial quality rubric."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from catalog_utils import collect_entries, discover_catalogs


PRIMARY_SOURCE_TYPES = {"official", "repository", "standard", "documentation", "research"}


def score_entry(entry: dict) -> tuple[int, list[str], list[str]]:
    score = 0
    critical: list[str] = []
    warnings: list[str] = []

    summary_len = len(entry.get("summary", "").strip())
    if summary_len >= 80:
        score += 10
    elif summary_len >= 40:
        score += 6
        warnings.append("summary could be more descriptive")
    else:
        critical.append("summary is too short")

    tags = entry.get("tags", [])
    score += 10 if len(tags) >= 3 else 6 if len(tags) >= 2 else 0
    if len(tags) < 3:
        warnings.append("fewer than three discovery tags")

    sources = entry.get("sources", [])
    if len(sources) >= 2:
        score += 15
    elif sources:
        score += 8
        warnings.append("only one verified source")
    else:
        critical.append("no verified sources")
    source_types = {source.get("type") for source in sources if isinstance(source, dict)}
    if source_types & PRIMARY_SOURCE_TYPES:
        score += 10
    else:
        critical.append("no primary or canonical source type")

    use_cases = entry.get("use_cases", [])
    if len(use_cases) >= 3:
        score += 15
    elif len(use_cases) >= 2:
        score += 9
        warnings.append("fewer than three use cases")
    else:
        critical.append("insufficient use cases")

    key_points = entry.get("key_points", [])
    if len(key_points) >= 3:
        score += 15
    elif len(key_points) >= 2:
        score += 9
        warnings.append("fewer than three key points")
    else:
        critical.append("insufficient key points")

    if entry.get("kind") and entry.get("domains"):
        score += 15
    else:
        critical.append("missing taxonomy facets")

    if entry.get("homepage") or entry.get("repository"):
        score += 10
    else:
        warnings.append("no canonical homepage or repository")

    if entry.get("license"):
        score += 3
    else:
        warnings.append("license metadata not yet curated")
    if entry.get("deployment_types"):
        score += 2
    else:
        warnings.append("deployment metadata not yet curated")

    return min(score, 100), critical, warnings


def audit(catalog_dir: Path) -> dict:
    entries, catalogs = collect_entries(discover_catalogs(catalog_dir))
    results = []
    tiers: Counter[str] = Counter()
    for entry in entries:
        score, critical, warnings = score_entry(entry)
        tier = "excellent" if score >= 95 else "strong" if score >= 85 else "needs-review" if score >= 70 else "insufficient"
        tiers[tier] += 1
        results.append(
            {
                "ref": entry["module_ref"],
                "name": entry["name"],
                "kind": entry["kind"],
                "domains": entry.get("domains", []),
                "score": score,
                "tier": tier,
                "critical": critical,
                "warnings": warnings,
            }
        )
    results.sort(key=lambda item: (item["score"], item["ref"]))
    return {
        "schema_version": 1,
        "module_count": len(results),
        "catalog_count": len(catalogs),
        "tier_counts": dict(tiers),
        "minimum_score": min((item["score"] for item in results), default=0),
        "average_score": round(sum(item["score"] for item in results) / len(results), 2) if results else 0,
        "results": results,
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# OpenDevIndex Quality Report",
        "",
        f"- Modules audited: **{report['module_count']}**",
        f"- Average score: **{report['average_score']} / 100**",
        f"- Minimum score: **{report['minimum_score']} / 100**",
        "",
        "## Quality tiers",
        "",
        "| Tier | Modules |",
        "| --- | ---: |",
    ]
    for tier in ("excellent", "strong", "needs-review", "insufficient"):
        lines.append(f"| {tier} | {report['tier_counts'].get(tier, 0)} |")

    lines.extend(["", "## Lowest-scoring modules", "", "| Module | Score | Notes |", "| --- | ---: | --- |"])
    for item in report["results"][:25]:
        notes = [*item["critical"], *item["warnings"]]
        note_text = "; ".join(notes[:4]) if notes else "No issues"
        lines.append(f"| `{item['ref']}` | {item['score']} | {note_text} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog-dir", default="catalog")
    parser.add_argument("--minimum", type=int, default=80)
    parser.add_argument("--report-json", default="dist/quality/quality-report.json")
    parser.add_argument("--report-md", default="dist/quality/quality-report.md")
    args = parser.parse_args()

    report = audit(Path(args.catalog_dir))
    json_path = Path(args.report_json)
    md_path = Path(args.report_md)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")

    print(
        f"OpenDevIndex quality audit: {report['module_count']} modules, "
        f"average {report['average_score']}, minimum {report['minimum_score']}"
    )
    failed = [item for item in report["results"] if item["score"] < args.minimum or item["critical"]]
    if failed:
        for item in failed[:20]:
            print(f"- {item['ref']}: {item['score']} — {', '.join(item['critical']) or 'below minimum'}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
