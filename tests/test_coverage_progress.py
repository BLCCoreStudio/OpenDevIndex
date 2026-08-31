from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from coverage_progress import build_progress, render_markdown  # noqa: E402


CATALOG = """schema_version: 3
milestone: test
verified_at: '2026-08-31'
target_modules: 1
expected_categories:
  tool: 1
entries:
- category: tool
  id: coverage-demo
  name: Coverage Demo
  kind: tool
  domains: [developer-tools]
  coverage:
    area: developer-tools
    topics: [developer-experience]
  summary: Example developer tool used to verify Technology Universe progress calculations in repository tests.
  homepage: https://example.com/
  repository: https://github.com/example/example
  tags: [developer-tools, example, cli]
  sources:
  - {title: Example documentation, url: https://example.com/docs, type: documentation}
  - {title: Example repository, url: https://github.com/example/example, type: repository}
  use_cases:
  - Verify mapped coverage progress calculations
  - Exercise area-level allocation reporting
  - Exercise topic-level allocation reporting
  key_points:
  - Counts only explicit schema v3 coverage mappings
  - Keeps planned targets separate from published modules
  - Uses the canonical topic allocation as denominator
"""


class CoverageProgressTests(unittest.TestCase):
    def test_progress_counts_only_explicit_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            catalog_dir = Path(temp) / "catalog"
            catalog_dir.mkdir()
            (catalog_dir / "test.yaml").write_text(CATALOG, encoding="utf-8")

            progress = build_progress(catalog_dir)
            self.assertEqual(progress["catalog_modules"], 1)
            self.assertEqual(progress["mapped_modules"], 1)
            self.assertEqual(progress["unmapped_modules"], 0)
            self.assertEqual(progress["target_modules"], 10000)

            developer_tools = next(row for row in progress["areas"] if row["area"] == "developer-tools")
            self.assertEqual(developer_tools["mapped"], 1)
            self.assertEqual(developer_tools["target"], 450)

            topic = next(row for row in progress["topics"] if row["topic"] == "developer-tools/developer-experience")
            self.assertEqual(topic["mapped"], 1)
            self.assertEqual(topic["target"], 37)

            markdown = render_markdown(progress)
            self.assertIn("Coverage-mapped modules: **1**", markdown)
            self.assertIn("developer-tools/developer-experience", markdown)


if __name__ == "__main__":
    unittest.main()
