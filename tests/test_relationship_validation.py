from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validate_relationships import validate_entry_relationships  # noqa: E402


class RelationshipValidationTests(unittest.TestCase):
    def make_entry(self) -> dict:
        return {
            "category": "tool",
            "id": "demo",
            "relationships": [
                {
                    "type": "integrates-with",
                    "target": "tool/git",
                    "note": "Used to verify a valid typed graph edge.",
                }
            ],
        }

    def test_valid_relationship_passes(self) -> None:
        self.assertEqual(validate_entry_relationships(self.make_entry(), 3), [])

    def test_relationships_require_schema_v3(self) -> None:
        errors = validate_entry_relationships(self.make_entry(), 2)
        self.assertTrue(any("require schema_version 3" in error for error in errors), errors)

    def test_unknown_relationship_type_fails(self) -> None:
        entry = self.make_entry()
        entry["relationships"][0]["type"] = "unknown-edge"
        errors = validate_entry_relationships(entry, 3)
        self.assertTrue(any("unsupported type" in error for error in errors), errors)

    def test_invalid_target_address_fails(self) -> None:
        entry = self.make_entry()
        entry["relationships"][0]["target"] = "not/a/valid/ref"
        errors = validate_entry_relationships(entry, 3)
        self.assertTrue(any("supported <category>/<slug>" in error for error in errors), errors)

    def test_self_relationship_fails(self) -> None:
        entry = self.make_entry()
        entry["relationships"][0]["target"] = "tool/demo"
        errors = validate_entry_relationships(entry, 3)
        self.assertTrue(any("cannot target the module itself" in error for error in errors), errors)

    def test_duplicate_relationship_fails(self) -> None:
        entry = self.make_entry()
        entry["relationships"].append(dict(entry["relationships"][0]))
        errors = validate_entry_relationships(entry, 3)
        self.assertTrue(any("duplicates" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
