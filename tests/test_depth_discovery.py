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

from build_depth_discovery import build  # noqa: E402


CATALOG = """schema_version: 3
milestone: test
verified_at: '2026-09-01'
target_modules: 3
expected_categories:
  tool: 3
entries:
- category: tool
  id: alpha
  name: Alpha
  kind: tool
  domains: [developer-tools]
  coverage:
    area: developer-tools
    topics: [developer-experience]
  summary: Alpha deep-dive fixture.
  homepage: https://example.com/alpha
  repository: https://github.com/example/alpha
  tags: [alpha]
  sources:
  - title: Alpha docs
    url: https://example.com/alpha/docs
    type: documentation
  use_cases: [Test deep-dive discovery]
  key_points: [Reviewed deep-dive fixture]
- category: tool
  id: beta
  name: Beta
  kind: tool
  domains: [developer-tools, testing]
  coverage:
    area: developer-tools
    topics: [developer-experience]
  summary: Beta guide fixture.
  homepage: https://example.com/beta
  repository: https://github.com/example/beta
  tags: [beta]
  sources:
  - title: Beta docs
    url: https://example.com/beta/docs
    type: documentation
  use_cases: [Test guide discovery]
  key_points: [Reviewed guide fixture]
- category: tool
  id: gamma
  name: Gamma
  kind: tool
  domains: [developer-tools]
  coverage:
    area: developer-tools
    topics: [developer-experience]
  summary: Gamma overview fixture.
  homepage: https://example.com/gamma
  repository: https://github.com/example/gamma
  tags: [gamma]
  sources:
  - title: Gamma docs
    url: https://example.com/gamma/docs
    type: documentation
  use_cases: [Test overview exclusion]
  key_points: [Overview fixture]
"""

MATURITY = """schema_version: 1
default_level: overview
levels: [overview, guide, deep-dive]
modules:
  tool/alpha:
    level: deep-dive
    reviewed_at: '2026-09-01'
  tool/beta:
    level: guide
    reviewed_at: '2026-08-31'
"""


class DepthDiscoveryTests(unittest.TestCase):
    def test_build_lists_only_reviewed_non_overview_modules(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            catalog_dir = root / "catalog"
            output_dir = root / "dist"
            manifest = root / "maturity.yaml"
            catalog_dir.mkdir()
            (catalog_dir / "test.yaml").write_text(CATALOG, encoding="utf-8")
            manifest.write_text(MATURITY, encoding="utf-8")

            payload = build(catalog_dir, manifest, output_dir)

            self.assertEqual(payload["module_count"], 2)
            self.assertEqual(payload["maturity_counts"], {"deep-dive": 1, "guide": 1})
            self.assertEqual([entry["ref"] for entry in payload["entries"]], ["tool/alpha", "tool/beta"])
            self.assertEqual(payload["entries"][0]["reviewed_at"], "2026-09-01")
            self.assertNotIn("tool/gamma", {entry["ref"] for entry in payload["entries"]})

            rendered = (output_dir / "depth.md").read_text(encoding="utf-8")
            self.assertIn("## Deep dives", rendered)
            self.assertIn("## Guides", rendered)
            self.assertIn("[Alpha]", rendered)
            self.assertIn("[Beta]", rendered)
            self.assertNotIn("Gamma", rendered)

            json_payload = json.loads((output_dir / "depth.json").read_text(encoding="utf-8"))
            self.assertEqual(json_payload, payload)

    def test_build_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            catalog_dir = root / "catalog"
            output_dir = root / "dist"
            manifest = root / "maturity.yaml"
            catalog_dir.mkdir()
            (catalog_dir / "test.yaml").write_text(CATALOG, encoding="utf-8")
            manifest.write_text(MATURITY, encoding="utf-8")

            build(catalog_dir, manifest, output_dir)
            first_json = (output_dir / "depth.json").read_text(encoding="utf-8")
            first_md = (output_dir / "depth.md").read_text(encoding="utf-8")
            build(catalog_dir, manifest, output_dir)
            self.assertEqual((output_dir / "depth.json").read_text(encoding="utf-8"), first_json)
            self.assertEqual((output_dir / "depth.md").read_text(encoding="utf-8"), first_md)


if __name__ == "__main__":
    unittest.main()
