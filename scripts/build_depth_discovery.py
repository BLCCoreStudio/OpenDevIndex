#!/usr/bin/env python3
"""Build deterministic discovery artifacts for reviewed guide and deep-dive modules."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from catalog_utils import collect_entries, discover_catalogs
from module_maturity import load_maturity_manifest, module_level

REPOSITORY_URL = "https://github.com/BLCCoreStudio/OpenDevIndex"
DISCOVERABLE_LEVELS = ("deep-dive", "guide")


def module_url(module_ref: str) -> str:
    return f"{REPOSITORY_URL}/tree/{module_ref}/entry"


def build_records(catalog_dir: Path, maturity_manifest_path: Path) -> list[dict]:
    entries, _ = collect_entries(discover_catalogs(catalog_dir))
    known_refs = {entry["module_ref"] for entry in entries}
    manifest = load_maturity_manifest(maturity_manifest_path, known_refs)

    records: list[dict] = []
    for entry in entries:
        ref = entry["module_ref"]
        level = module_level(ref, manifest)
        if level not in DISCOVERABLE_LEVELS:
            continue
        maturity = manifest["modules"].get(ref, {})
        records.append(
            {
                "ref": ref,
                "name": entry["name"],
                "kind": entry["kind"],
                "domains": sorted(entry.get("domains", [])),
                "maturity": level,
                "reviewed_at": maturity.get("reviewed_at"),
                "summary": entry["summary"],
                "url": module_url(ref),
            }
        )

    level_rank = {level: index for index, level in enumerate(DISCOVERABLE_LEVELS)}
    records.sort(
        key=lambda item: (
            level_rank[item["maturity"]],
            item["kind"].casefold(),
            item["name"].casefold(),
            item["ref"],
        )
    )
    return records


def discovery_counts(records: list[dict]) -> tuple[Counter, Counter, Counter]:
    maturity_counts = Counter(record["maturity"] for record in records)
    kind_counts = Counter(record["kind"] for record in records)
    domain_counts = Counter(
        domain for record in records for domain in record.get("domains", [])
    )
    return maturity_counts, kind_counts, domain_counts


def module_links(records: list[dict]) -> str:
    ordered = sorted(
        records,
        key=lambda item: (item["name"].casefold(), item["ref"]),
    )
    return ", ".join(
        f"[{record['name'].replace('|', '\\|')}]({record['url']})"
        for record in ordered
    )


def render_markdown(records: list[dict]) -> str:
    counts, kind_counts, domain_counts = discovery_counts(records)
    lines = [
        "# OpenDevIndex — Reviewed Depth",
        "",
        "This generated view highlights modules that have progressed beyond overview maturity after explicit editorial review.",
        "",
        f"**Deep dives:** {counts['deep-dive']}",
        "",
        f"**Guides:** {counts['guide']}",
    ]

    if kind_counts:
        lines.extend(
            [
                "",
                "## Reviewed depth by kind",
                "",
                "| Kind | Modules | Browse |",
                "| --- | ---: | --- |",
            ]
        )
        for kind, count in sorted(kind_counts.items()):
            matching = [record for record in records if record["kind"] == kind]
            lines.append(f"| `{kind}` | {count} | {module_links(matching)} |")

    if domain_counts:
        lines.extend(
            [
                "",
                "## Reviewed depth by domain",
                "",
                "| Domain | Modules | Browse |",
                "| --- | ---: | --- |",
            ]
        )
        for domain, count in sorted(domain_counts.items()):
            matching = [record for record in records if domain in record.get("domains", [])]
            lines.append(f"| `{domain}` | {count} | {module_links(matching)} |")

    for level, heading in (("deep-dive", "Deep dives"), ("guide", "Guides")):
        level_records = [record for record in records if record["maturity"] == level]
        lines.extend(["", f"## {heading}", ""])
        if not level_records:
            lines.append("_No reviewed modules at this depth yet._")
            continue
        lines.extend(
            [
                "| Module | Kind | Domains | Reviewed | Summary |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for record in level_records:
            name = record["name"].replace("|", "\\|")
            summary = record["summary"].replace("|", "\\|")
            domains = ", ".join(f"`{domain}`" for domain in record["domains"]) or "—"
            reviewed_at = record["reviewed_at"] or "—"
            lines.append(
                f"| [{name}]({record['url']}) (`{record['ref']}`) | `{record['kind']}` | {domains} | {reviewed_at} | {summary} |"
            )

    lines.extend(
        [
            "",
            "---",
            "",
            "Maturity is independently reviewed metadata. An overview module is not considered lower quality; it simply has a narrower editorial scope.",
            "",
        ]
    )
    return "\n".join(lines)


def build(
    catalog_dir: Path,
    maturity_manifest_path: Path,
    output_dir: Path,
    public_file: Path | None = None,
) -> dict:
    records = build_records(catalog_dir, maturity_manifest_path)
    counts, kind_counts, domain_counts = discovery_counts(records)
    payload = {
        "schema_version": 1,
        "module_count": len(records),
        "maturity_counts": {
            level: counts[level] for level in DISCOVERABLE_LEVELS if counts[level]
        },
        "kind_counts": dict(sorted(kind_counts.items())),
        "domain_counts": dict(sorted(domain_counts.items())),
        "entries": records,
    }

    rendered = render_markdown(records)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "depth.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "depth.md").write_text(rendered, encoding="utf-8")
    if public_file is not None:
        public_file.parent.mkdir(parents=True, exist_ok=True)
        public_file.write_text(rendered, encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog-dir", default="catalog")
    parser.add_argument("--maturity-manifest", default="quality/module-maturity.yaml")
    parser.add_argument("--output-dir", default="dist/depth")
    parser.add_argument(
        "--public-file",
        help="Optional generated Markdown path for the public reviewed-depth view",
    )
    args = parser.parse_args()

    try:
        payload = build(
            Path(args.catalog_dir),
            Path(args.maturity_manifest),
            Path(args.output_dir),
            Path(args.public_file) if args.public_file else None,
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    counts = payload["maturity_counts"]
    print(
        "Built reviewed-depth discovery: "
        f"{counts.get('deep-dive', 0)} deep dive(s), {counts.get('guide', 0)} guide(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
