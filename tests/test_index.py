from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_index import build  # noqa: E402
from search_index import load_index, search  # noqa: E402


CATALOG = """schema_version: 1
milestone: test
verified_at: '2026-08-31'
target_modules: 1
expected_categories:
  tool: 1
entries:
- category: tool
  id: example-tool
  name: Example Tool
  summary: Example developer tool used to verify deterministic OpenDevIndex search artifact generation.
  homepage: https://example.com/
  repository: https://github.com/example/example
  tags:
  - developer-tools
  - example
  sources:
  - title: Example documentation
    url: https://example.com/docs
    type: documentation
  use_cases:
  - Demonstrate deterministic index generation
  - Exercise the local search ranking implementation
  key_points:
  - Provides a compact fixture for repository tests
  - Keeps index tests independent from the production catalog
"""


class IndexTests(unittest.TestCase):
    def test_build_and_search(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            catalog_dir = root / "catalog"
            output_dir = root / "dist"
            catalog_dir.mkdir()
            (catalog_dir / "test.yaml").write_text(CATALOG, encoding="utf-8")

            result = build(catalog_dir, output_dir)
            self.assertEqual(result["module_count"], 1)
            self.assertTrue((output_dir / "catalog.json").is_file())
            self.assertTrue((output_dir / "search.json").is_file())
            self.assertTrue((output_dir / "catalog.md").is_file())

            entries = load_index(output_dir / "search.json")
            matches = search(entries, "example developer", None, 10)
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]["ref"], "tool/example-tool")
            self.assertGreater(matches[0]["score"], 0)

            payload = json.loads((output_dir / "catalog.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["module_count"], 1)
            self.assertEqual(payload["category_counts"], {"tool": 1})

    def test_search_category_filter(self) -> None:
        entries = [
            {
                "ref": "tool/demo",
                "slug": "demo",
                "name": "Demo",
                "category": "tool",
                "summary": "A demo tool for testing search behavior.",
                "tags": ["demo", "tool"],
                "use_cases": [],
                "key_points": [],
                "search_text": "tool demo demo tool testing search behavior",
            }
        ]
        self.assertEqual(search(entries, "demo", "security", 5), [])
        self.assertEqual(search(entries, "demo", "tool", 5)[0]["ref"], "tool/demo")


if __name__ == "__main__":
    unittest.main()
