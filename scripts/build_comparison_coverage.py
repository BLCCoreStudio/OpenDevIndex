#!/usr/bin/env python3
"""Build deterministic curated-comparison coverage metrics from module search data."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

START_MARKER = "<!-- comparison-coverage:start -->"
END_MARKER = "<!-- comparison-coverage:end -->"
INDEX_START_MARKER = "<!-- comparison-coverage-link:start -->"
INDEX_END_MARKER = "<!-- comparison-coverage-link:end -->"


def _load_index(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid module index {path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 3:
        raise ValueError(f"{path}: schema_version must be 3")
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise ValueError(f"{path}: entries must be a list")
    return data


def calculate(entries: list[dict]) -> dict:
    deep_dive_refs: list[str] = []
    linked_refs: list[str] = []
    unlinked_refs: list[str] = []

    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"module record {index} must be a mapping")
        ref = entry.get("ref")
        if not isinstance(ref, str) or not ref:
            raise ValueError(f"module record {index} has invalid ref")
        if entry.get("maturity") != "deep-dive":
            continue
        deep_dive_refs.append(ref)
        comparisons = entry.get("comparisons", [])
        if not isinstance(comparisons, list):
            raise ValueError(f"{ref}: comparisons must be a list")
        comparison_count = entry.get("comparison_count", len(comparisons))
        if comparison_count != len(comparisons):
            raise ValueError(f"{ref}: comparison_count does not match comparisons")
        if comparisons:
            linked_refs.append(ref)
        else:
            unlinked_refs.append(ref)

    deep_dive_refs.sort()
    linked_refs.sort()
    unlinked_refs.sort()
    total = len(deep_dive_refs)
    linked = len(linked_refs)
    coverage_percent = round((linked / total * 100.0) if total else 0.0, 2)

    return {
        "schema_version": 1,
        "deep_dive_total": total,
        "deep_dive_linked": linked,
        "deep_dive_unlinked": len(unlinked_refs),
        "deep_dive_coverage_percent": coverage_percent,
        "linked_deep_dive_refs": linked_refs,
        "unlinked_deep_dive_refs": unlinked_refs,
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# Curated comparison coverage",
        "",
        "Comparison coverage measures reviewed `deep-dive` modules that participate in at least one curated comparison. It is a discovery-depth metric, not a target to create artificial graph edges.",
        "",
        f"- Deep-dive modules: **{report['deep_dive_total']}**",
        f"- Linked to at least one curated comparison: **{report['deep_dive_linked']}**",
        f"- Not yet linked: **{report['deep_dive_unlinked']}**",
        f"- Coverage: **{report['deep_dive_coverage_percent']:.2f}%**",
        "",
        "## Deep dives not yet in a curated comparison",
        "",
    ]
    if report["unlinked_deep_dive_refs"]:
        lines.extend(f"- `{ref}`" for ref in report["unlinked_deep_dive_refs"])
    else:
        lines.append("All current deep-dive modules participate in at least one curated comparison.")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A module should enter a comparison only when the comparison teaches a real architectural, operational, compatibility, or lifecycle distinction. An unlinked deep dive is a discovery opportunity, not a quality failure.",
            "",
        ]
    )
    return "\n".join(lines)


def _coverage_block(report: dict) -> str:
    unlinked = ", ".join(f"`{ref}`" for ref in report["unlinked_deep_dive_refs"]) or "none"
    return "\n".join(
        [
            START_MARKER,
            f"**Deep-dive comparison coverage:** {report['deep_dive_linked']} / {report['deep_dive_total']} ({report['deep_dive_coverage_percent']:.2f}%)",
            "",
            f"**Deep dives not yet in a curated comparison:** {unlinked}",
            END_MARKER,
        ]
    )


def annotate_markdown(path: Path, report: dict) -> None:
    text = path.read_text(encoding="utf-8")
    block = _coverage_block(report)
    if START_MARKER in text or END_MARKER in text:
        if text.count(START_MARKER) != 1 or text.count(END_MARKER) != 1:
            raise ValueError(f"{path}: invalid comparison coverage marker state")
        start = text.index(START_MARKER)
        end = text.index(END_MARKER) + len(END_MARKER)
        text = text[:start] + block + text[end:]
    else:
        anchor = "\nSee [`docs/comparisons/index.md`](docs/comparisons/index.md)"
        if anchor not in text:
            raise ValueError(f"{path}: comparison browse anchor not found")
        text = text.replace(anchor, "\n" + block + "\n" + anchor, 1)
    path.write_text(text, encoding="utf-8")


def annotate_comparison_index(path: Path, report: dict) -> None:
    text = path.read_text(encoding="utf-8")
    block = "\n".join(
        [
            INDEX_START_MARKER,
            f"[View deep-dive comparison coverage](coverage.md) — {report['deep_dive_linked']} / {report['deep_dive_total']} deep dives linked ({report['deep_dive_coverage_percent']:.2f}%).",
            INDEX_END_MARKER,
        ]
    )
    if INDEX_START_MARKER in text or INDEX_END_MARKER in text:
        if text.count(INDEX_START_MARKER) != 1 or text.count(INDEX_END_MARKER) != 1:
            raise ValueError(f"{path}: invalid comparison coverage link marker state")
        start = text.index(INDEX_START_MARKER)
        end = text.index(INDEX_END_MARKER) + len(INDEX_END_MARKER)
        text = text[:start] + block + text[end:]
    else:
        anchor = "\n[Browse comparisons by module](by-module.md)"
        if anchor not in text:
            raise ValueError(f"{path}: comparison by-module anchor not found")
        text = text.replace(anchor, "\n" + block + "\n" + anchor, 1)
    path.write_text(text, encoding="utf-8")


def annotate_json(path: Path, report: dict) -> None:
    data = _load_index(path)
    data["comparison_coverage"] = report
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build(
    module_search_path: Path,
    output_json: Path,
    output_markdown: Path,
    *,
    catalog_json: Path | None = None,
    search_json: Path | None = None,
    catalog_markdown: Path | None = None,
    public_index: Path | None = None,
    public_markdown: Path | None = None,
    comparison_index_markdown: Path | None = None,
) -> dict:
    module_search = _load_index(module_search_path)
    report = calculate(module_search["entries"])

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    output_markdown.parent.mkdir(parents=True, exist_ok=True)
    markdown = render_markdown(report)
    output_markdown.write_text(markdown, encoding="utf-8")

    for path in (catalog_json, search_json):
        if path is not None:
            annotate_json(path, report)
    for path in (catalog_markdown, public_index):
        if path is not None:
            annotate_markdown(path, report)
    if public_markdown is not None:
        public_markdown.parent.mkdir(parents=True, exist_ok=True)
        public_markdown.write_text(markdown, encoding="utf-8")
    if comparison_index_markdown is not None:
        annotate_comparison_index(comparison_index_markdown, report)

    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module-search", default="dist/index/search.json")
    parser.add_argument("--output-json", default="dist/comparisons/coverage.json")
    parser.add_argument("--output-markdown", default="dist/comparisons/coverage.md")
    parser.add_argument("--catalog-json")
    parser.add_argument("--search-json")
    parser.add_argument("--catalog-markdown")
    parser.add_argument("--public-index")
    parser.add_argument("--public-markdown")
    parser.add_argument("--comparison-index-markdown")
    args = parser.parse_args()

    try:
        report = build(
            Path(args.module_search),
            Path(args.output_json),
            Path(args.output_markdown),
            catalog_json=Path(args.catalog_json) if args.catalog_json else None,
            search_json=Path(args.search_json) if args.search_json else None,
            catalog_markdown=Path(args.catalog_markdown) if args.catalog_markdown else None,
            public_index=Path(args.public_index) if args.public_index else None,
            public_markdown=Path(args.public_markdown) if args.public_markdown else None,
            comparison_index_markdown=(
                Path(args.comparison_index_markdown) if args.comparison_index_markdown else None
            ),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"OpenDevIndex comparison coverage build failed: {exc}", file=sys.stderr)
        return 1

    print(
        "OpenDevIndex comparison coverage built: "
        f"{report['deep_dive_linked']} / {report['deep_dive_total']} deep dives "
        f"({report['deep_dive_coverage_percent']:.2f}%)"
    )
    for ref in report["unlinked_deep_dive_refs"]:
        print(f"- unlinked: {ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
