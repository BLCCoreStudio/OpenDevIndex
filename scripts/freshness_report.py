#!/usr/bin/env python3
"""Report OpenDevIndex modules whose verification date is older than a cutoff."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path


def parse_verified_at(value: object) -> date:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("verified_at must be a non-empty ISO date")
    text = value.strip()
    try:
        return date.fromisoformat(text)
    except ValueError:
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
        except ValueError as exc:
            raise ValueError(f"invalid verified_at value: {value!r}") from exc


def stale_entries(entries: list[dict], *, as_of: date, max_age_days: int) -> list[dict]:
    if max_age_days < 0:
        raise ValueError("max_age_days must be zero or greater")

    cutoff = as_of - timedelta(days=max_age_days)
    stale: list[dict] = []
    for entry in entries:
        verified = parse_verified_at(entry.get("verified_at"))
        if verified > as_of:
            raise ValueError(
                f"{entry.get('ref', '<unknown>')}: verified_at {verified.isoformat()} is after as-of date {as_of.isoformat()}"
            )
        if verified < cutoff:
            stale.append(
                {
                    "ref": entry.get("ref"),
                    "name": entry.get("name"),
                    "maturity": entry.get("maturity", "overview"),
                    "verified_at": verified.isoformat(),
                    "age_days": (as_of - verified).days,
                    "url": entry.get("url"),
                }
            )

    stale.sort(key=lambda item: (-item["age_days"], str(item.get("name") or "").casefold(), str(item.get("ref") or "")))
    return stale


def load_entries(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(
            f"search index not found: {path}. Run scripts/build_index.py first."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("entries") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise ValueError(f"{path}: expected an object with an entries list")
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List modules whose verified_at date is older than an explicit freshness window."
    )
    parser.add_argument("--index", default="dist/index/search.json")
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=365,
        help="Maximum accepted verification age in days (default: 365)",
    )
    parser.add_argument(
        "--as-of",
        default=date.today().isoformat(),
        help="ISO date used as the deterministic reference point (default: today)",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    if args.max_age_days < 0:
        parser.error("--max-age-days must be zero or greater")
    try:
        as_of = date.fromisoformat(args.as_of)
    except ValueError:
        parser.error("--as-of must be an ISO date in YYYY-MM-DD form")

    try:
        entries = load_entries(Path(args.index))
        results = stale_entries(entries, as_of=as_of, max_age_days=args.max_age_days)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"OpenDevIndex freshness report failed: {exc}", file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(results, indent=2, ensure_ascii=False, sort_keys=True))
        return 0

    if not results:
        print("No stale OpenDevIndex modules found for the selected freshness window.")
        return 0

    print(
        f"Stale modules as of {as_of.isoformat()} (older than {args.max_age_days} days): {len(results)}"
    )
    for number, entry in enumerate(results, start=1):
        print(
            f"{number}. {entry.get('name') or entry.get('ref')} [{entry.get('ref')}] — "
            f"verified {entry['verified_at']} ({entry['age_days']} days ago), "
            f"depth {entry['maturity']}"
        )
        if entry.get("url"):
            print(f"   {entry['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
