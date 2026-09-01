from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from seed_modules_v3 import render_metadata_v3, render_readme_v3  # noqa: E402


class SeedModulesV3Tests(unittest.TestCase):
    def make_entry(self) -> dict:
        return {
            "id": "demo",
            "name": "Demo",
            "category": "tool",
            "module_ref": "tool/demo",
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
            "use_cases": [
                "Exercise schema v3 publication behavior in unit tests",
                "Verify human-readable knowledge graph rendering",
                "Protect relationship metadata from publication regressions",
            ],
            "key_points": [
                "Schema v3 preserves coverage metadata",
                "Schema v3 preserves typed graph relationships",
                "Human-readable module pages expose relationship data",
            ],
            "sources": [
                {"title": "Official", "url": "https://example.com", "type": "official"},
                {"title": "Repository", "url": "https://github.com/example/demo", "type": "repository"},
            ],
            "verified_at": "2026-08-31",
        }

    def test_v3_preserves_coverage_and_relationships(self) -> None:
        entry = self.make_entry()
        data = yaml.safe_load(render_metadata_v3(entry, "2026-08-31", 3))
        self.assertEqual(data["schema_version"], 3)
        self.assertEqual(data["coverage"], entry["coverage"])
        self.assertEqual(data["relationships"], entry["relationships"])

    def test_v3_readme_renders_knowledge_graph(self) -> None:
        rendered = render_readme_v3(self.make_entry())
        self.assertIn("## Knowledge graph", rendered)
        self.assertIn("`related-to` → `concept/example-concept`", rendered)
        self.assertIn("Example edge.", rendered)

    def test_v3_rejects_unknown_relationship_type(self) -> None:
        entry = self.make_entry()
        entry["relationships"][0]["type"] = "not-a-real-edge"
        with self.assertRaisesRegex(ValueError, "unsupported type"):
            render_metadata_v3(entry, "2026-08-31", 3)

    def test_v3_rejects_duplicate_relationships(self) -> None:
        entry = self.make_entry()
        entry["relationships"].append(dict(entry["relationships"][0]))
        with self.assertRaisesRegex(ValueError, "duplicates"):
            render_metadata_v3(entry, "2026-08-31", 3)

    def test_v3_rejects_self_relationship(self) -> None:
        entry = self.make_entry()
        entry["relationships"][0]["target"] = "tool/demo"
        with self.assertRaisesRegex(ValueError, "cannot target the module itself"):
            render_metadata_v3(entry, "2026-08-31", 3)

    def test_v2_remains_unchanged(self) -> None:
        entry = self.make_entry()
        data = yaml.safe_load(render_metadata_v3(entry, "2026-08-31", 2))
        self.assertEqual(data["schema_version"], 2)
        self.assertNotIn("coverage", data)
        self.assertNotIn("relationships", data)


if __name__ == "__main__":
    unittest.main()
