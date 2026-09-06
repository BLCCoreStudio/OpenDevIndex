from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validate_comparison_discovery import load_semantic_cases, validate  # noqa: E402


COMPARISONS = {
    "schema_version": 1,
    "comparison_count": 2,
    "comparisons": [
        {
            "id": "alpha-beta",
            "title": "Alpha vs Beta",
            "summary": "Synthetic Alpha and Beta comparison fixture.",
            "verified_at": "2026-09-06",
            "modules": [
                {"ref": "tool/alpha", "name": "Alpha"},
                {"ref": "tool/beta", "name": "Beta"},
            ],
        },
        {
            "id": "alpha-gamma",
            "title": "Alpha vs Gamma",
            "summary": "Synthetic Alpha and Gamma comparison fixture.",
            "verified_at": "2026-09-06",
            "modules": [
                {"ref": "tool/alpha", "name": "Alpha"},
                {"ref": "tool/gamma", "name": "Gamma"},
            ],
        },
    ],
}

REVERSE = {
    "schema_version": 1,
    "module_count": 3,
    "modules": [
        {
            "ref": "tool/alpha",
            "comparisons": [
                {"id": "alpha-beta", "title": "Alpha vs Beta"},
                {"id": "alpha-gamma", "title": "Alpha vs Gamma"},
            ],
        },
        {
            "ref": "tool/beta",
            "comparisons": [{"id": "alpha-beta", "title": "Alpha vs Beta"}],
        },
        {
            "ref": "tool/gamma",
            "comparisons": [{"id": "alpha-gamma", "title": "Alpha vs Gamma"}],
        },
    ],
}

COMPARISON_SEARCH = {
    "schema_version": 1,
    "comparison_count": 2,
    "entries": [
        {
            "id": "alpha-beta",
            "title": "Alpha vs Beta",
            "summary": "Synthetic Alpha and Beta comparison fixture.",
            "module_refs": ["tool/alpha", "tool/beta"],
            "module_names": ["Alpha", "Beta"],
            "dimension_ids": ["beta-boundary"],
            "dimension_labels": ["Beta boundary"],
            "search_text": "alpha beta alpha-beta alpha vs beta beta boundary",
        },
        {
            "id": "alpha-gamma",
            "title": "Alpha vs Gamma",
            "summary": "Synthetic Alpha and Gamma comparison fixture.",
            "module_refs": ["tool/alpha", "tool/gamma"],
            "module_names": ["Alpha", "Gamma"],
            "dimension_ids": ["gamma-boundary"],
            "dimension_labels": ["Gamma boundary"],
            "search_text": "alpha gamma alpha-gamma alpha vs gamma gamma boundary",
        },
    ],
}

MODULE_SEARCH = {
    "schema_version": 3,
    "module_count": 3,
    "comparison_linked_module_count": 3,
    "entries": [
        {
            "ref": "tool/alpha",
            "name": "Alpha",
            "comparison_count": 2,
            "comparisons": [
                {"id": "alpha-beta", "title": "Alpha vs Beta"},
                {"id": "alpha-gamma", "title": "Alpha vs Gamma"},
            ],
            "search_text": "alpha alpha-beta alpha-gamma",
        },
        {
            "ref": "tool/beta",
            "name": "Beta",
            "comparison_count": 1,
            "comparisons": [{"id": "alpha-beta", "title": "Alpha vs Beta"}],
            "search_text": "beta alpha-beta",
        },
        {
            "ref": "tool/gamma",
            "name": "Gamma",
            "comparison_count": 1,
            "comparisons": [{"id": "alpha-gamma", "title": "Alpha vs Gamma"}],
            "search_text": "gamma alpha-gamma",
        },
    ],
}

CASES = {
    "schema_version": 1,
    "cases": [
        {"comparison": "alpha-beta", "query": "beta boundary"},
        {"comparison": "alpha-gamma", "query": "gamma boundary"},
    ],
}


class ComparisonDiscoveryValidatorTests(unittest.TestCase):
    def _write_fixture(self, root: Path, name: str, payload: dict, *, yaml_file: bool = False) -> Path:
        path = root / name
        if yaml_file:
            path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _validate(self, root: Path, *, reverse: dict | None = None, cases: dict | None = None) -> dict:
        return validate(
            self._write_fixture(root, "comparisons.json", COMPARISONS),
            self._write_fixture(root, "module-comparisons.json", reverse or REVERSE),
            self._write_fixture(root, "comparison-search.json", COMPARISON_SEARCH),
            self._write_fixture(root, "module-search.json", MODULE_SEARCH),
            self._write_fixture(root, "cases.yaml", cases or CASES, yaml_file=True),
        )

    def test_validates_symmetric_multi_comparison_graph(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = self._validate(Path(temp))
            self.assertEqual(result["comparison_count"], 2)
            self.assertEqual(result["linked_module_count"], 3)
            self.assertEqual(result["multi_comparison_module_count"], 1)
            self.assertEqual(result["semantic_case_count"], 2)

    def test_reverse_index_order_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            broken = json.loads(json.dumps(REVERSE))
            broken["modules"][0]["comparisons"].reverse()
            with self.assertRaisesRegex(ValueError, "reverse-index ordering/membership drift"):
                self._validate(Path(temp), reverse=broken)

    def test_every_comparison_requires_semantic_case(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            broken_cases = {
                "schema_version": 1,
                "cases": [{"comparison": "alpha-beta", "query": "beta boundary"}],
            }
            with self.assertRaisesRegex(ValueError, "every comparison needs at least one semantic search case"):
                self._validate(Path(temp), cases=broken_cases)

    def test_semantic_rank_regression_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            broken_cases = json.loads(json.dumps(CASES))
            broken_cases["cases"][0]["query"] = "gamma boundary"
            with self.assertRaisesRegex(ValueError, "semantic search failed"):
                self._validate(Path(temp), cases=broken_cases)

    def test_unknown_comparison_in_registry_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "cases.yaml"
            path.write_text(
                yaml.safe_dump(
                    {
                        "schema_version": 1,
                        "cases": [
                            {"comparison": "missing", "query": "missing query"},
                            {"comparison": "alpha-beta", "query": "beta boundary"},
                            {"comparison": "alpha-gamma", "query": "gamma boundary"},
                        ],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "unknown comparison"):
                load_semantic_cases(path, {"alpha-beta", "alpha-gamma"})


if __name__ == "__main__":
    unittest.main()
