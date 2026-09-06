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

from build_comparison_coverage import (  # noqa: E402
    END_MARKER,
    START_MARKER,
    annotate_markdown,
    build,
    calculate,
)


MODULE_SEARCH = {
    "schema_version": 3,
    "module_count": 4,
    "comparison_linked_module_count": 2,
    "entries": [
        {
            "ref": "tool/alpha",
            "name": "Alpha",
            "maturity": "deep-dive",
            "comparison_count": 1,
            "comparisons": [{"id": "alpha-beta", "title": "Alpha vs Beta"}],
        },
        {
            "ref": "tool/beta",
            "name": "Beta",
            "maturity": "deep-dive",
            "comparison_count": 0,
            "comparisons": [],
        },
        {
            "ref": "tool/gamma",
            "name": "Gamma",
            "maturity": "overview",
            "comparison_count": 1,
            "comparisons": [{"id": "gamma-delta", "title": "Gamma vs Delta"}],
        },
        {
            "ref": "tool/delta",
            "name": "Delta",
            "maturity": "overview",
            "comparison_count": 0,
            "comparisons": [],
        },
    ],
}

INDEX_MARKDOWN = """# OpenDevIndex — Browse the Index

**Indexed modules:** 4

**Modules in curated comparisons:** 2

See [`docs/comparisons/index.md`](docs/comparisons/index.md) for comparison-first browsing or [`docs/comparisons/by-module.md`](docs/comparisons/by-module.md) for the reverse index.
"""


class ComparisonCoverageTests(unittest.TestCase):
    def test_calculate_counts_only_deep_dives(self) -> None:
        report = calculate(MODULE_SEARCH["entries"])
        self.assertEqual(report["deep_dive_total"], 2)
        self.assertEqual(report["deep_dive_linked"], 1)
        self.assertEqual(report["deep_dive_unlinked"], 1)
        self.assertEqual(report["deep_dive_coverage_percent"], 50.0)
        self.assertEqual(report["linked_deep_dive_refs"], ["tool/alpha"])
        self.assertEqual(report["unlinked_deep_dive_refs"], ["tool/beta"])

    def test_build_writes_reports_and_annotates_discovery_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            module_search = root / "search.json"
            catalog_json = root / "catalog.json"
            output_json = root / "coverage.json"
            output_markdown = root / "coverage.md"
            catalog_markdown = root / "catalog.md"
            public_index = root / "INDEX.md"
            public_markdown = root / "public-coverage.md"

            module_search.write_text(json.dumps(MODULE_SEARCH), encoding="utf-8")
            catalog_json.write_text(json.dumps(MODULE_SEARCH), encoding="utf-8")
            catalog_markdown.write_text(INDEX_MARKDOWN, encoding="utf-8")
            public_index.write_text(INDEX_MARKDOWN, encoding="utf-8")

            report = build(
                module_search,
                output_json,
                output_markdown,
                catalog_json=catalog_json,
                search_json=module_search,
                catalog_markdown=catalog_markdown,
                public_index=public_index,
                public_markdown=public_markdown,
            )

            self.assertEqual(report["deep_dive_coverage_percent"], 50.0)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["unlinked_deep_dive_refs"], ["tool/beta"])
            self.assertIn("`tool/beta`", output_markdown.read_text(encoding="utf-8"))
            self.assertEqual(
                output_markdown.read_text(encoding="utf-8"),
                public_markdown.read_text(encoding="utf-8"),
            )

            for path in (catalog_json, module_search):
                annotated = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(annotated["comparison_coverage"]["deep_dive_linked"], 1)

            for path in (catalog_markdown, public_index):
                text = path.read_text(encoding="utf-8")
                self.assertEqual(text.count(START_MARKER), 1)
                self.assertEqual(text.count(END_MARKER), 1)
                self.assertIn("**Deep-dive comparison coverage:** 1 / 2 (50.00%)", text)
                self.assertIn("`tool/beta`", text)

    def test_markdown_annotation_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "INDEX.md"
            path.write_text(INDEX_MARKDOWN, encoding="utf-8")
            report = calculate(MODULE_SEARCH["entries"])
            annotate_markdown(path, report)
            first = path.read_text(encoding="utf-8")
            annotate_markdown(path, report)
            second = path.read_text(encoding="utf-8")
            self.assertEqual(first, second)
            self.assertEqual(second.count(START_MARKER), 1)

    def test_comparison_count_mismatch_is_rejected(self) -> None:
        broken = json.loads(json.dumps(MODULE_SEARCH["entries"]))
        broken[0]["comparison_count"] = 2
        with self.assertRaisesRegex(ValueError, "comparison_count does not match comparisons"):
            calculate(broken)

    def test_zero_deep_dives_has_zero_percent(self) -> None:
        report = calculate([MODULE_SEARCH["entries"][2], MODULE_SEARCH["entries"][3]])
        self.assertEqual(report["deep_dive_total"], 0)
        self.assertEqual(report["deep_dive_coverage_percent"], 0.0)


if __name__ == "__main__":
    unittest.main()
