#!/usr/bin/env python3
"""Schema v3 adapter for the existing trusted OpenDevIndex module publisher."""

from __future__ import annotations

import yaml

import seed_modules

_ORIGINAL_RENDER_METADATA = seed_modules.render_metadata


def render_metadata_v3(entry: dict, verified_at: str, schema_version: int) -> str:
    """Preserve v3 graph/coverage fields while reusing the existing publisher."""
    rendered = _ORIGINAL_RENDER_METADATA(entry, verified_at, schema_version)
    if schema_version < 3:
        return rendered

    metadata = yaml.safe_load(rendered)
    if not isinstance(metadata, dict):
        raise ValueError("publisher metadata renderer returned invalid YAML")

    coverage = entry.get("coverage")
    if not isinstance(coverage, dict):
        raise ValueError("schema v3 publication requires coverage metadata")
    metadata["coverage"] = coverage

    relationships = entry.get("relationships")
    if relationships:
        metadata["relationships"] = relationships

    return yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True, width=1000)


def install_adapter() -> None:
    seed_modules.render_metadata = render_metadata_v3


def main() -> int:
    install_adapter()
    return seed_modules.main()


if __name__ == "__main__":
    raise SystemExit(main())
