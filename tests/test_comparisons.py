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

from build_comparisons import build, build_module_comparison_index, load_comparison  # noqa: E402


CATALOG = """schema_version: 3
milestone: comparison-test
verified_at: '2026-08-31'
target_modules: 2
expected_categories:
  tool: 2
entries:
- category: tool
  id: alpha
  name: Alpha
  kind: tool
  domains: [developer-tools]
  coverage:
    area: developer-tools
    topics: [developer-experience]
  summary: Alpha is a sufficiently detailed example technology used to verify curated comparison generation.
  homepage: https://example.com/alpha
  repository: https://github.com/example/alpha
  tags: [alpha, developer-tools, comparison-fixture]
  sources:
  - title: Alpha documentation
    url: https://example.com/alpha/docs
    type: documentation
  - title: Alpha repository
    url: https://github.com/example/alpha
    type: repository
  use_cases:
  - Compare Alpha with another technology
  - Exercise deterministic comparison rendering
  - Validate comparison references
  key_points:
  - Alpha has a stable module reference
  - Alpha is intentionally synthetic test data
  - Alpha keeps comparison tests isolated
- category: tool
  id: beta
  name: Beta
  kind: tool
  domains: [developer-tools]
  coverage:
    area: developer-tools
    topics: [developer-experience]
  summary: Beta is a sufficiently detailed example technology used to verify curated comparison generation.
  homepage: https://example.com/beta
  repository: https://github.com/example/beta
  tags: [beta, developer-tools, comparison-fixture]
  sources:
  - title: Beta documentation
    url: https://example.com/beta/docs
    type: documentation
  - title: Beta repository
    url: https://github.com/example/beta
    type: repository
  use_cases:
  - Compare Beta with another technology
  - Exercise deterministic comparison rendering
  - Validate comparison references
  key_points:
  - Beta has a stable module reference
  - Beta is intentionally synthetic test data
  - Beta keeps comparison tests isolated
"""

MATURITY = """schema_version: 1
default_level: overview
levels: [overview, guide, deep-dive]
modules:
  tool/alpha:
    level: deep-dive
    reviewed_at: '2026-08-31'
    note: Comparison test fixture.
  tool/beta:
    level: guide
    reviewed_at: '2026-08-31'
    note: Comparison test fixture.
"""

COMPARISON = """schema_version: 1
id: alpha-vs-beta
title: Alpha vs Beta
summary: A deterministic comparison fixture that verifies dimension coverage, maturity annotations, decision rules, and Markdown generation.
verified_at: '2026-08-31'
modules:
- tool/alpha
- tool/beta
dimensions:
- id: execution-model
  label: Execution model
  values:
    tool/alpha: Alpha executes work using the first synthetic comparison model.
    tool/beta: Beta executes work using the second synthetic comparison model.
- id: deployment-model
  label: Deployment model
  values:
    tool/alpha: Alpha is deployed as the first synthetic fixture.
    tool/beta: Beta is deployed as the second synthetic fixture.
decision_rules:
- condition: The first synthetic behavior is the explicit requirement.
  consider: [tool/alpha]
  reason: Alpha exists in this fixture to verify single-module decision guidance.
notes:
- The comparison is synthetic test data and does not describe real technology behavior.
"""


class ComparisonTests(unittest.TestCase):
    def test_build_generates_json_markdown_and_reverse_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            catalog_dir = root / "catalog"
            comparisons_dir = root / "comparisons"
            output_dir = root / "dist" / "comparisons"
            public_dir = root / "docs" / "comparisons"
            maturity = root / "maturity.yaml"
            catalog_dir.mkdir()
            comparisons_dir.mkdir()
            (catalog_dir / "test.yaml").write_text(CATALOG, encoding="utf-8")
            (comparisons_dir / "alpha-vs-beta.yaml").write_text(COMPARISON, encoding="utf-8")
            maturity.write_text(MATURITY, encoding="utf-8")

            result = build(comparisons_dir, catalog_dir, output_dir, maturity, public_dir)
            self.assertEqual(result["comparison_count"], 1)
            self.assertEqual(result["comparison_ids"], ["alpha-vs-beta"])
            self.assertEqual(result["module_count"], 2)

            payload = json.loads((output_dir / "comparisons.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["comparison_count"], 1)
            record = payload["comparisons"][0]
            self.assertEqual(record["modules"][0]["ref"], "tool/alpha")
            self.assertEqual(record["modules"][0]["maturity"], "deep-dive")
            self.assertEqual(record["modules"][1]["maturity"], "guide")

            reverse = json.loads((output_dir / "module-comparisons.json").read_text(encoding="utf-8"))
            self.assertEqual(reverse["schema_version"], 1)
            self.assertEqual(reverse["module_count"], 2)
            self.assertEqual(reverse["modules"][0]["ref"], "tool/alpha")
            self.assertEqual(reverse["modules"][0]["comparisons"][0]["id"], "alpha-vs-beta")
            self.assertEqual(reverse["modules"][1]["ref"], "tool/beta")

            rendered = (output_dir / "alpha-vs-beta.md").read_text(encoding="utf-8")
            self.assertIn("# Alpha vs Beta", rendered)
            self.assertIn("| Dimension | [Alpha]", rendered)
            self.assertIn("## Decision guide", rendered)
            self.assertIn("/tree/tool/alpha/entry", rendered)
            self.assertEqual(
                rendered,
                (public_dir / "alpha-vs-beta.md").read_text(encoding="utf-8"),
            )

            comparison_index = (output_dir / "index.md").read_text(encoding="utf-8")
            self.assertIn("[Browse comparisons by module](by-module.md)", comparison_index)

            by_module = (output_dir / "by-module.md").read_text(encoding="utf-8")
            self.assertIn("# Comparisons by module", by_module)
            self.assertIn("## [Alpha]", by_module)
            self.assertIn("[Alpha vs Beta](alpha-vs-beta.md)", by_module)
            self.assertEqual(
                by_module,
                (public_dir / "by-module.md").read_text(encoding="utf-8"),
            )

    def test_reverse_index_sorts_modules_and_comparisons(self) -> None:
        records = [
            {
                "id": "zeta-view",
                "title": "Zeta view",
                "summary": "A sufficiently detailed synthetic comparison summary for deterministic ordering checks.",
                "verified_at": "2026-08-31",
                "modules": [
                    {
                        "ref": "tool/beta",
                        "name": "Beta",
                        "url": "https://example.com/beta",
                        "maturity": "guide",
                        "summary": "Beta summary",
                    }
                ],
            },
            {
                "id": "alpha-view",
                "title": "Alpha view",
                "summary": "Another sufficiently detailed synthetic comparison summary for ordering checks.",
                "verified_at": "2026-08-31",
                "modules": [
                    {
                        "ref": "tool/alpha",
                        "name": "Alpha",
                        "url": "https://example.com/alpha",
                        "maturity": "deep-dive",
                        "summary": "Alpha summary",
                    },
                    {
                        "ref": "tool/beta",
                        "name": "Beta",
                        "url": "https://example.com/beta",
                        "maturity": "guide",
                        "summary": "Beta summary",
                    },
                ],
            },
        ]

        reverse = build_module_comparison_index(records)
        self.assertEqual([module["ref"] for module in reverse], ["tool/alpha", "tool/beta"])
        self.assertEqual(
            [item["id"] for item in reverse[1]["comparisons"]],
            ["alpha-view", "zeta-view"],
        )

    def test_dimension_must_cover_every_module(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "broken.yaml"
            path.write_text(
                COMPARISON.replace("id: alpha-vs-beta", "id: broken").replace(
                    "    tool/beta: Beta executes work using the second synthetic comparison model.\n", ""
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "must cover every module"):
                load_comparison(path, {"tool/alpha", "tool/beta"})

    def test_unknown_module_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "alpha-vs-beta.yaml"
            path.write_text(COMPARISON, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unknown module tool/beta"):
                load_comparison(path, {"tool/alpha"})


if __name__ == "__main__":
    unittest.main()
