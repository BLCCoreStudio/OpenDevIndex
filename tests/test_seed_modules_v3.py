from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from seed_modules_v3 import render_metadata_v3  # noqa: E402


class SeedModulesV3Tests(unittest.TestCase):
    def test_v3_preserves_coverage_and_relationships(self) -> None:
        entry = {
            "id": "demo",
            "name": "Demo",
            "category": "tool",
            "kind": "tool",
            "domains": ["developer-tools"],
            "summary": "A sufficiently detailed summary used to test schema v3 publisher metadata preservation.",
            "homepage": "https://example.com",
            "repository": "https://github.com/example/demo",
            "license": "MIT",
            "deployment_types": ["cli"],
            "tags": ["demo", "developer-tools", "cli"],
            "coverage": {"area": "developer-tools", "topics": ["developer-experience"]},
            "relationships": [
                {"type": "related-to", "target": "concept/example-concept", "note": "Example edge."}
            ],
            "sources": [
                {"title": "Official", "url": "https://example.com", "type": "official"},
                {"title": "Repository", "url": "https://github.com/example/demo", "type": "repository"},
            ],
        }
        data = yaml.safe_load(render_metadata_v3(entry, "2026-08-31", 3))
        self.assertEqual(data["schema_version"], 3)
        self.assertEqual(data["coverage"], entry["coverage"])
        self.assertEqual(data["relationships"], entry["relationships"])

    def test_v2_remains_unchanged(self) -> None:
        entry = {
            "id": "demo",
            "name": "Demo",
            "category": "tool",
            "kind": "tool",
            "domains": ["developer-tools"],
            "summary": "A sufficiently detailed summary used to test backwards-compatible publisher metadata behavior.",
            "tags": ["demo", "developer-tools", "cli"],
            "sources": [
                {"title": "Official", "url": "https://example.com", "type": "official"},
                {"title": "Repository", "url": "https://github.com/example/demo", "type": "repository"},
            ],
        }
        data = yaml.safe_load(render_metadata_v3(entry, "2026-08-31", 2))
        self.assertEqual(data["schema_version"], 2)
        self.assertNotIn("coverage", data)
        self.assertNotIn("relationships", data)


if __name__ == "__main__":
    unittest.main()
