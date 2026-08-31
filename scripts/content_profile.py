#!/usr/bin/env python3
"""Validation helpers for deep OpenDevIndex schema v4 content profiles."""

from __future__ import annotations

REQUIRED_TEXT = {
    "what_it_is": 80,
    "why_it_exists": 80,
    "how_it_works": 120,
    "security": 80,
    "performance": 80,
}
REQUIRED_LISTS = {
    "architecture": (2, 20),
    "concepts": (3, 10),
    "use_cases": (3, 15),
    "learning_path": (4, 10),
}
OPTIONAL_TEXT = {
    "operations": 60,
    "ecosystem": 60,
}
OPTIONAL_LISTS = {
    "examples": (1, 15),
    "prerequisites": (1, 10),
}


def validate_content_profile(value: object) -> list[str]:
    if not isinstance(value, dict):
        return ["content must be an object"]

    errors: list[str] = []
    for field, minimum in REQUIRED_TEXT.items():
        text = value.get(field)
        if not isinstance(text, str) or len(text.strip()) < minimum:
            errors.append(f"content.{field} must contain at least {minimum} characters")

    for field, (minimum_items, minimum_length) in REQUIRED_LISTS.items():
        items = value.get(field)
        if not isinstance(items, list) or len(items) < minimum_items:
            errors.append(f"content.{field} must contain at least {minimum_items} items")
            continue
        if any(not isinstance(item, str) or len(item.strip()) < minimum_length for item in items):
            errors.append(f"content.{field} items must contain at least {minimum_length} characters")

    alternatives = value.get("alternatives")
    if not isinstance(alternatives, list) or len(alternatives) < 2:
        errors.append("content.alternatives must contain at least 2 alternatives")
    else:
        for index, alternative in enumerate(alternatives, start=1):
            if not isinstance(alternative, dict):
                errors.append(f"content.alternatives #{index} must be an object")
                continue
            name = alternative.get("name")
            tradeoff = alternative.get("tradeoff")
            if not isinstance(name, str) or not name.strip():
                errors.append(f"content.alternatives #{index} requires a name")
            if not isinstance(tradeoff, str) or len(tradeoff.strip()) < 30:
                errors.append(f"content.alternatives #{index} tradeoff must contain at least 30 characters")

    for field, minimum in OPTIONAL_TEXT.items():
        text = value.get(field)
        if text is not None and (not isinstance(text, str) or len(text.strip()) < minimum):
            errors.append(f"content.{field} must contain at least {minimum} characters when present")

    for field, (minimum_items, minimum_length) in OPTIONAL_LISTS.items():
        items = value.get(field)
        if items is None:
            continue
        if not isinstance(items, list) or len(items) < minimum_items:
            errors.append(f"content.{field} must contain at least {minimum_items} items when present")
        elif any(not isinstance(item, str) or len(item.strip()) < minimum_length for item in items):
            errors.append(f"content.{field} items must contain at least {minimum_length} characters")

    allowed = set(REQUIRED_TEXT) | set(REQUIRED_LISTS) | set(OPTIONAL_TEXT) | set(OPTIONAL_LISTS) | {"alternatives"}
    unknown = sorted(set(value) - allowed)
    if unknown:
        errors.append(f"content contains unsupported fields: {', '.join(unknown)}")
    return errors
