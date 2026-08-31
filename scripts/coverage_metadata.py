#!/usr/bin/env python3
"""Helpers for validating module-to-Technology-Universe coverage metadata."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_UNIVERSE = ROOT / "coverage/technology-universe-v1.yaml"


@lru_cache(maxsize=4)
def load_coverage_map(path: str | Path = DEFAULT_UNIVERSE) -> dict[str, set[str]]:
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError(f"{path}: unsupported coverage schema")

    result: dict[str, set[str]] = {}
    for area in data.get("areas", []):
        if not isinstance(area, dict):
            continue
        area_id = area.get("id")
        topics = area.get("topics")
        if isinstance(area_id, str) and isinstance(topics, list):
            result[area_id] = {topic for topic in topics if isinstance(topic, str)}
    if not result:
        raise ValueError(f"{path}: no coverage areas found")
    return result


def validate_coverage_metadata(value: object, path: str | Path = DEFAULT_UNIVERSE) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, dict):
        return ["coverage must be an object"]

    area = value.get("area")
    topics = value.get("topics")
    coverage_map = load_coverage_map(path)

    errors: list[str] = []
    if not isinstance(area, str) or area not in coverage_map:
        errors.append("coverage area is not defined in the Technology Universe")
        return errors

    if not isinstance(topics, list) or not topics:
        errors.append("coverage topics must be a non-empty list")
        return errors
    if len(topics) != len(set(topics)):
        errors.append("coverage topics must be unique")
    unknown = sorted(topic for topic in topics if topic not in coverage_map[area])
    if unknown:
        errors.append(f"coverage topics are not valid for {area}: {', '.join(unknown)}")
    return errors
