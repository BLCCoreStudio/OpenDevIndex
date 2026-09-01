#!/usr/bin/env python3
"""Publish or refresh validated OpenDevIndex knowledge modules."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from module_workflow import sync_module_workflow
from taxonomy import enrich_entry, load_taxonomy

ROOT = Path(__file__).resolve().parents[1]
CURATED_CONTENT_TAGS = {"deep-dive"}


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
        if "refs/heads/" in line:
            branches.add(line.split("refs/heads/", 1)[1])
    return branches


def render_metadata(entry: dict, verified_at: str, schema_version: int) -> str:
    metadata = {
        "schema_version": schema_version,
        "id": entry["id"],
        "name": entry["name"],
        "category": entry["category"],
        "kind": entry.get("kind"),
        "domains": entry.get("domains"),
        "summary": entry["summary"],
        "homepage": entry.get("homepage"),
        "repository": entry.get("repository"),
        "license": entry.get("license"),
        "deployment_types": entry.get("deployment_types"),
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
    domains = ", ".join(f"`{value}`" for value in entry.get("domains", [])) or "none"
    deployments = ", ".join(f"`{value}`" for value in entry.get("deployment_types", [])) or "not yet curated"
    license_text = entry.get("license") or "not yet curated"

    return f"""# {entry['name']}

> {entry['summary']}

## What it is

{entry['name']} is indexed as a **{entry['kind']}**. Its stable OpenDevIndex address is `{entry['module_ref']}`; taxonomy facets are kept separate from that address so classification can improve without breaking links.

## Why it matters

The module focuses on the technology's practical role, high-signal characteristics, common use cases, and authoritative references. Fast-changing details should be verified against the sources below rather than inferred from stale copies.

## Typical use cases

{use_cases}

## Key points

{key_points}

## Taxonomy

- Kind: `{entry['kind']}`
- Domains: {domains}
- Deployment: {deployments}
- License metadata: `{license_text}`

## Primary links

{links_text}

## Verified sources

{source_links}

## Verification

The catalog metadata and source references for this module were reviewed on **{entry['verified_at']}**. Automated checks validate structure and source reachability; factual updates still require source-backed editorial review.

## Maintenance

Update this independently versioned module when material facts, project status, canonical documentation, or important trade-offs change. Preserve the stable module address unless a compatibility migration is explicitly documented.
"""


def render_sources(entry: dict, verified_at: str, milestone: str) -> str:
    items = "\n".join(
        f"- **{source['title']}** — {source['url']} (`{source['type']}`)"
        for source in entry["sources"]
    )
    return f"""# Sources

Verified for the OpenDevIndex **{milestone}** catalog on **{verified_at}**.

{items}

Sources are selected to prefer official project pages, canonical documentation, standards, primary repositories, advisories, or original research.
"""


def render_history(entry: dict, verified_at: str, milestone: str, previous: str | None = None) -> str:
    update = f"""# History

## {verified_at} — {milestone}

- Reviewed `{entry['module_ref']}` against the current OpenDevIndex catalog and taxonomy.
- Recorded canonical kind `{entry['kind']}` and domain facets: {', '.join(entry.get('domains', []))}.
- Re-rendered module documentation from validated source-backed metadata.
"""
    if previous:
        body = previous.strip()
        if body.startswith("# History"):
            body = body[len("# History"):].lstrip()
        if body:
            update += "\n## Earlier history\n\n" + body + "\n"
    return update


def load_existing_metadata(worktree: Path) -> dict:
    metadata_path = worktree / "entry" / "entry.yaml"
    if not metadata_path.is_file():
        return {}
    try:
        data = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def refresh_protection_reason(worktree: Path, incoming_schema_version: int) -> str | None:
    """Return why an existing module refresh should be protected by default."""
    metadata = load_existing_metadata(worktree)
    tags = metadata.get("tags") or []
    if isinstance(tags, list):
        curated = sorted(CURATED_CONTENT_TAGS.intersection(str(tag) for tag in tags))
        if curated:
            return f"curated content tag(s): {', '.join(curated)}"

    existing_schema = metadata.get("schema_version")
    if isinstance(existing_schema, int) and incoming_schema_version < existing_schema:
        return f"schema downgrade {existing_schema} -> {incoming_schema_version}"
    return None


def write_entry(worktree: Path, entry: dict, verified_at: str, milestone: str, schema_version: int, preserve_history: bool) -> None:
    entry_dir = worktree / "entry"
    old_history = None
    if preserve_history and (entry_dir / "history.md").is_file():
        old_history = (entry_dir / "history.md").read_text(encoding="utf-8")
    if entry_dir.exists():
        shutil.rmtree(entry_dir)
    entry_dir.mkdir(parents=True)
    (entry_dir / "README.md").write_text(render_readme(entry), encoding="utf-8")
    (entry_dir / "entry.yaml").write_text(render_metadata(entry, verified_at, schema_version), encoding="utf-8")
    (entry_dir / "sources.md").write_text(render_sources(entry, verified_at, milestone), encoding="utf-8")
    (entry_dir / "history.md").write_text(render_history(entry, verified_at, milestone, old_history), encoding="utf-8")


def commit_worktree(worktree: Path, branch: str, message: str, push: bool) -> tuple[str, bool]:
    if not run("git", "status", "--porcelain", cwd=worktree, capture=True):
        return run("git", "rev-parse", "HEAD", cwd=worktree, capture=True), False
    run("git", "add", "entry", ".github/workflows", cwd=worktree)
    run("git", "commit", "-m", message, cwd=worktree)
    commit_sha = run("git", "rev-parse", "HEAD", cwd=worktree, capture=True)
    if push:
        run("git", "push", "origin", f"HEAD:refs/heads/{branch}", cwd=worktree)
    return commit_sha, True


def publish_entry(
    base_ref: str,
    entry: dict,
    verified_at: str,
    milestone: str,
    schema_version: int,
    push: bool,
    refresh: bool,
    overwrite_curated: bool = False,
) -> tuple[str, bool]:
    branch = entry["module_ref"]
    temp_root = Path(tempfile.mkdtemp(prefix="opendevindex-"))
    worktree = temp_root / "worktree"
    try:
        run("git", "worktree", "add", "--detach", str(worktree), base_ref)
        run("git", "config", "user.name", "OpenDevIndex Publisher", cwd=worktree)
        run("git", "config", "user.email", "207100624+BLCCoreStudio@users.noreply.github.com", cwd=worktree)

        if refresh and not overwrite_curated:
            protection_reason = refresh_protection_reason(worktree, schema_version)
            if protection_reason:
                workflow_changed = sync_module_workflow(worktree)
                print(
                    f"Protecting {branch} from automatic content refresh ({protection_reason}). "
                    "Module CI may still be synchronized. Use --overwrite-curated for an intentional content replacement.",
                    flush=True,
                )
                if not workflow_changed:
                    return run("git", "rev-parse", "HEAD", cwd=worktree, capture=True), False
                return commit_worktree(
                    worktree,
                    branch,
                    "ci: sync module validation workflow",
                    push,
                )

        write_entry(worktree, entry, verified_at, milestone, schema_version, preserve_history=refresh)
        sync_module_workflow(worktree)
        run(
            sys.executable,
            str(ROOT / "scripts/validate_entry.py"),
            "--branch",
            branch,
            "--root",
            str(worktree),
            cwd=ROOT,
        )
        message = "entry: refresh taxonomy and metadata" if refresh else f"entry: add {entry['name']} knowledge module"
        return commit_worktree(worktree, branch, message, push)
    finally:
        try:
            run("git", "worktree", "remove", "--force", str(worktree))
        except Exception:
            pass
        shutil.rmtree(temp_root, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default="catalog/v0.1.yaml")
    parser.add_argument("--limit", type=int, default=0, help="0 means all eligible entries")
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--report", default="seed-report.md")
    parser.add_argument("--refresh-existing", action="store_true", help="Refresh entry files on existing module branches")
    parser.add_argument("--refresh-only", action="store_true", help="Do not create missing module branches")
    parser.add_argument(
        "--overwrite-curated",
        action="store_true",
        help="Allow refreshes to replace deep-dive modules or downgrade an existing module schema",
    )
    args = parser.parse_args()

    catalog_path = ROOT / args.catalog
    catalog = load_catalog(catalog_path)
    verified_at = str(catalog["verified_at"])
    milestone = str(catalog.get("milestone", catalog_path.stem))
    schema_version = int(catalog.get("schema_version", 1))
    run(sys.executable, "scripts/validate_catalog.py", str(catalog_path))

    taxonomy = load_taxonomy()
    entries = []
    for raw in catalog["entries"]:
        entry = dict(raw)
        entry["module_ref"] = f"{entry['category']}/{entry['id']}"
        entry["verified_at"] = verified_at
        entries.append(enrich_entry(entry, taxonomy))

    existing = remote_branches()
    base_sha = run("git", "rev-parse", args.base_ref, capture=True)
    created: list[tuple[str, str]] = []
    refreshed: list[tuple[str, str]] = []
    unchanged: list[str] = []
    skipped: list[str] = []
    processed = 0

    for entry in entries:
        branch = entry["module_ref"]
        is_existing = branch in existing
        if args.limit and processed >= args.limit:
            break

        if is_existing:
            if not args.refresh_existing:
                skipped.append(branch)
                continue
            print(f"Refreshing {branch} ...", flush=True)
            run("git", "fetch", "origin", f"refs/heads/{branch}:refs/remotes/origin/{branch}")
            commit_sha, changed = publish_entry(
                f"origin/{branch}",
                entry,
                verified_at,
                milestone,
                schema_version,
                args.push,
                refresh=True,
                overwrite_curated=args.overwrite_curated,
            )
            (refreshed if changed else unchanged).append((branch, commit_sha) if changed else branch)
            processed += 1
            continue

        if args.refresh_only:
            skipped.append(branch)
            continue

        print(f"Publishing {branch} ...", flush=True)
        commit_sha, _ = publish_entry(base_sha, entry, verified_at, milestone, schema_version, args.push, refresh=False)
        created.append((branch, commit_sha))
        existing.add(branch)
        processed += 1

    report = [
        "# OpenDevIndex publication report",
        "",
        f"- Catalog: `{args.catalog}`",
        f"- Milestone: `{milestone}`",
        f"- Created: **{len(created)}**",
        f"- Refreshed: **{len(refreshed)}**",
        f"- Unchanged: **{len(unchanged)}**",
        f"- Skipped: **{len(skipped)}**",
        f"- Push enabled: **{args.push}**",
        "",
    ]
    if created:
        report.extend(["## Created", "", *[f"- `{branch}` — `{sha}`" for branch, sha in created], ""])
    if refreshed:
        report.extend(["## Refreshed", "", *[f"- `{branch}` — `{sha}`" for branch, sha in refreshed], ""])

    report_path = ROOT / args.report
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(report_path.read_text(encoding="utf-8"))

    json_summary = {
        "created": [{"branch": branch, "commit": sha} for branch, sha in created],
        "refreshed": [{"branch": branch, "commit": sha} for branch, sha in refreshed],
        "unchanged": unchanged,
        "skipped": skipped,
        "base": base_sha,
        "verified_at": verified_at,
        "milestone": milestone,
    }
    (ROOT / "seed-report.json").write_text(json.dumps(json_summary, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
