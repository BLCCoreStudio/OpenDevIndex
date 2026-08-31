from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from coverage_metadata import load_coverage_map, validate_coverage_metadata  # noqa: E402


class CoverageMetadataTests(unittest.TestCase):
    def test_known_area_and_topic_are_valid(self) -> None:
        value = {"area": "developer-tools", "topics": ["developer-experience"]}
        self.assertEqual(validate_coverage_metadata(value), [])

    def test_topic_must_belong_to_selected_area(self) -> None:
        value = {"area": "developer-tools", "topics": ["cryptography"]}
        errors = validate_coverage_metadata(value)
        self.assertTrue(any("not valid for developer-tools" in error for error in errors))

    def test_coverage_map_contains_all_major_areas(self) -> None:
        coverage_map = load_coverage_map()
        self.assertEqual(len(coverage_map), 20)
        self.assertIn("ai-ml", coverage_map)
        self.assertIn("cybersecurity-privacy", coverage_map)
        self.assertIn("hardware-architecture", coverage_map)


if __name__ == "__main__":
    unittest.main()
