#!/usr/bin/env python3
"""Create validated knowledge branches from a curated OpenDevIndex catalog."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, cwd: Path | None = None, capture: bool = False) -> str:
    result = subprocess.run(
        args,
        cwd=cwd or ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    return (result.stdout or "").strip()


def load_catalog(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        raise ValueError("catalog must contain an entries list")
    return data


def remote_branches() -> set[str]:
    output = run("git", "ls-remote", "--heads", "origin", capture=True)
    branches: set[str] = set()
    for line in output.splitlines():
        if "refs/heads/" not in line:
            continue
        branches.add(line.split("refs/heads/", 1)[1])
    return branches


def render_metadata(entry: dict, verified_at: str) -> str:
    metadata = {
        "schema_version": 1,
        "id": entry["id"],
        "name": entry["name"],
        "category": entry["category"],
        "summary": entry["summary"],
        "homepage": entry.get("homepage"),
        "repository": entry.get("repository"),
        "status": "active",
        "verified_at": verified_at,
        "tags": entry["tags"],
        "sources": entry["sources"],
    }
    metadata = {key: value for key, value in metadata.items() if value is not None}
    return yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True, width=1000)


def render_readme(entry: dict) -> str:
    use_cases = "\n".join(f"- {item}" for item in entry["use_cases"])
    key_points = "\n".join(f"- {item}" for item in entry["key_points"])
    source_links = "\n".join(
        f"- [{source['title']}]({source['url']}) — `{source['type']}`"
        for source in entry["sources"]
    )
    links = []
    if entry.get("homepage"):
        links.append(f"- Homepage: {entry['homepage']}")
    if entry.get("repository"):
        links.append(f"- Repository: {entry['repository']}")
    links_text = "\n".join(links) if links else "- See the verified sources below."

    return f"""# {entry['name']}

> {entry['summary']}

## Why it matters

{entry['name']} is indexed by OpenDevIndex as a `{entry['category']}` knowledge module. This page is intentionally concise: it explains the technology's role, common uses, and high-signal facts while linking back to authoritative sources for details that can change over time.

## Typical use cases

{use_cases}

## Key points

{key_points}

## Primary links

{links_text}

## Verified sources

{source_links}

## Maintenance

This module is independently versioned on branch `{entry['category']}/{entry['id']}`. When the technology, specification, project status, or canonical documentation changes, update this branch and refresh the verification date instead of silently changing unrelated modules.
"""


def render_sources(entry: dict, verified_at: str) -> str:
    items = "\n".join(
        f"- **{source['title']}** — {source['url']} (`{source['type']}`)"
        for source in entry["sources"]
    )
    return f"""# Sources

Verified for the OpenDevIndex v0.1 catalog on **{verified_at}**.

{items}

Sources are selected to prefer official project pages, canonical documentation, standards, primary repositories, advisories, or original research.
"""


def render_history(entry: dict, verified_at: str) -> str:
    return f"""# History

## {verified_at}

- Added `{entry['category']}/{entry['id']}` to the curated OpenDevIndex v0.1 catalog.
- Created the initial source-backed knowledge module.
- Verified metadata structure and required references with the repository validator.
"""


def write_entry(worktree: Path, entry: dict, verified_at: str) -> None:
    entry_dir = worktree / "entry"
    if entry_dir.exists():
        shutil.rmtree(entry_dir)
    entry_dir.mkdir(parents=True)
    (entry_dir / "README.md").write_text(render_readme(entry), encoding="utf-8")
    (entry_dir / "entry.yaml").write_text(render_metadata(entry, verified_at), encoding="utf-8")
    (entry_dir / "sources.md").write_text(render_sources(entry, verified_at), encoding="utf-8")
    (entry_dir / "history.md").write_text(render_history(entry, verified_at), encoding="utf-8")


def seed_entry(base_sha: str, entry: dict, verified_at: str, push: bool) -> str:
    branch = f"{entry['category']}/{entry['id']}"
    temp_root = Path(tempfile.mkdtemp(prefix="opendevindex-"))
    worktree = temp_root / "worktree"
    try:
        run("git", "worktree", "add", "--detach", str(worktree), base_sha)
        run("git", "config", "user.name", "OpenDevIndex Seeder", cwd=worktree)
        run("git", "config", "user.email", "207100624+BLCCoreStudio@users.noreply.github.com", cwd=worktree)
        write_entry(worktree, entry, verified_at)
        run(sys.executable, "scripts/validate_entry.py", "--branch", branch, cwd=worktree)
        run("git", "add", "entry", cwd=worktree)
        run("git", "commit", "-m", f"entry: add {entry['name']} knowledge module", cwd=worktree)
        commit_sha = run("git", "rev-parse", "HEAD", cwd=worktree, capture=True)
        if push:
            run("git", "push", "origin", f"HEAD:refs/heads/{branch}", cwd=worktree)
        return commit_sha
    finally:
        try:
            run("git", "worktree", "remove", "--force", str(worktree))
        except Exception:
            pass
        shutil.rmtree(temp_root, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default="catalog/v0.1.yaml")
    parser.add_argument("--limit", type=int, default=0, help="0 means all missing entries")
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--report", default="seed-report.md")
    args = parser.parse_args()

    catalog_path = ROOT / args.catalog
    catalog = load_catalog(catalog_path)
    verified_at = str(catalog["verified_at"])
    run(sys.executable, "scripts/validate_catalog.py", str(catalog_path))

    existing = remote_branches()
    base_sha = run("git", "rev-parse", args.base_ref, capture=True)
    created: list[tuple[str, str]] = []
    skipped: list[str] = []

    for entry in catalog["entries"]:
        branch = f"{entry['category']}/{entry['id']}"
        if branch in existing:
            skipped.append(branch)
            continue
        if args.limit and len(created) >= args.limit:
            break
        print(f"Seeding {branch} ...", flush=True)
        commit_sha = seed_entry(base_sha, entry, verified_at, args.push)
        created.append((branch, commit_sha))
        existing.add(branch)

    report = [
        "# OpenDevIndex seed report",
        "",
        f"- Catalog: `{args.catalog}`",
        f"- Base: `{base_sha}`",
        f"- Created: **{len(created)}**",
        f"- Already present: **{len(skipped)}**",
        f"- Push enabled: **{args.push}**",
        "",
        "## Created branches",
        "",
    ]
    report.extend(f"- `{branch}` — `{sha}`" for branch, sha in created)
    if not created:
        report.append("- None; catalog was already seeded or the limit was zero after filtering.")

    report_path = ROOT / args.report
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(report_path.read_text(encoding="utf-8"))

    json_summary = {
        "created": [{"branch": branch, "commit": sha} for branch, sha in created],
        "skipped": skipped,
        "base": base_sha,
        "verified_at": verified_at,
    }
    (ROOT / "seed-report.json").write_text(json.dumps(json_summary, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
