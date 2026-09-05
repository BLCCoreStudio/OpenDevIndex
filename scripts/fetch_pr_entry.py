#!/usr/bin/env python3
"""Safely materialize entry files from a module pull request as untrusted data.

This helper is intended for a trusted ``pull_request_target`` workflow. It never
executes code from the pull-request head: it fetches only the four text files in
``entry/`` through GitHub's Contents API and writes them under a caller-provided
directory for the trusted validator to inspect.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable

from taxonomy import load_taxonomy, supported_address_categories

REQUIRED_ENTRY_PATHS = (
    "entry/README.md",
    "entry/entry.yaml",
    "entry/sources.md",
    "entry/history.md",
)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
MAX_FILE_BYTES = 1_000_000
API_ROOT = "https://api.github.com"


class PullRequestEntryError(ValueError):
    """Raised when pull-request metadata or fetched entry content is unsafe."""


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise PullRequestEntryError(f"{label} must be a non-empty string")
    return value


def module_ref_from_event(event: dict) -> str:
    try:
        base_ref = _require_string(event["pull_request"]["base"]["ref"], "base ref")
    except (KeyError, TypeError) as exc:
        raise PullRequestEntryError("event is missing pull_request.base.ref") from exc

    if base_ref.count("/") != 1:
        raise PullRequestEntryError(
            f"module pull request must target <category>/<slug>, got {base_ref!r}"
        )

    category, slug = base_ref.split("/", 1)
    categories = supported_address_categories(load_taxonomy())
    if category not in categories:
        raise PullRequestEntryError(f"unsupported module category in base ref: {category}")
    if not SLUG_RE.fullmatch(slug):
        raise PullRequestEntryError(f"invalid module slug in base ref: {slug}")
    return base_ref


def head_coordinates(event: dict) -> tuple[str, str]:
    try:
        head = event["pull_request"]["head"]
        repo = _require_string(head["repo"]["full_name"], "head repository")
        sha = _require_string(head["sha"], "head SHA")
    except (KeyError, TypeError) as exc:
        raise PullRequestEntryError("event is missing pull-request head coordinates") from exc

    if not REPO_RE.fullmatch(repo):
        raise PullRequestEntryError(f"invalid head repository name: {repo!r}")
    if not SHA_RE.fullmatch(sha):
        raise PullRequestEntryError("head SHA must be a full 40-character lowercase hex SHA")
    return repo, sha


def _contents_url(repository: str, sha: str, path: str) -> str:
    owner, name = repository.split("/", 1)
    quoted_path = urllib.parse.quote(path, safe="/")
    return (
        f"{API_ROOT}/repos/{urllib.parse.quote(owner, safe='')}/"
        f"{urllib.parse.quote(name, safe='')}/contents/{quoted_path}"
        f"?ref={urllib.parse.quote(sha, safe='')}"
    )


def fetch_contents_api(repository: str, sha: str, path: str, token: str | None) -> bytes:
    request = urllib.request.Request(
        _contents_url(repository, sha, path),
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "OpenDevIndex-module-pr-validator",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise PullRequestEntryError(f"could not fetch {path}: {exc}") from exc

    if not isinstance(payload, dict) or payload.get("type") != "file":
        raise PullRequestEntryError(f"{path} did not resolve to a file")
    if payload.get("encoding") != "base64" or not isinstance(payload.get("content"), str):
        raise PullRequestEntryError(f"{path} did not return base64 file content")

    try:
        data = base64.b64decode(payload["content"], validate=True)
    except (ValueError, TypeError) as exc:
        raise PullRequestEntryError(f"{path} returned invalid base64 content") from exc
    return data


def materialize_entry(
    event: dict,
    output_root: Path,
    fetcher: Callable[[str, str, str, str | None], bytes] = fetch_contents_api,
    token: str | None = None,
) -> tuple[str, str]:
    module_ref = module_ref_from_event(event)
    repository, sha = head_coordinates(event)

    output_root = output_root.resolve()
    entry_root = output_root / "entry"
    entry_root.mkdir(parents=True, exist_ok=True)

    for relative in REQUIRED_ENTRY_PATHS:
        data = fetcher(repository, sha, relative, token)
        if len(data) > MAX_FILE_BYTES:
            raise PullRequestEntryError(
                f"{relative} exceeds the {MAX_FILE_BYTES}-byte validation limit"
            )
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PullRequestEntryError(f"{relative} must be UTF-8 text") from exc
        if "\x00" in text:
            raise PullRequestEntryError(f"{relative} must not contain NUL bytes")

        destination = output_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")

    return module_ref, sha


def _write_github_output(path: Path, module_ref: str, sha: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"module_ref={module_ref}\n")
        handle.write(f"head_sha={sha}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True, help="GitHub event JSON path")
    parser.add_argument("--output", required=True, help="Directory to materialize candidate entry files")
    parser.add_argument("--github-output", help="Optional GITHUB_OUTPUT file for module_ref/head_sha")
    args = parser.parse_args()

    try:
        event = json.loads(Path(args.event).read_text(encoding="utf-8"))
        if not isinstance(event, dict):
            raise PullRequestEntryError("event JSON must contain an object")
        module_ref, sha = materialize_entry(
            event,
            Path(args.output),
            token=os.environ.get("GITHUB_TOKEN"),
        )
        if args.github_output:
            _write_github_output(Path(args.github_output), module_ref, sha)
    except (OSError, json.JSONDecodeError, PullRequestEntryError) as exc:
        print(f"OpenDevIndex module PR materialization failed: {exc}", file=sys.stderr)
        return 1

    print(f"Materialized untrusted entry data for {module_ref} at {sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
