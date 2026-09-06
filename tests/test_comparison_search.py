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

from build_comparison_search import build  # noqa: E402
from search_comparisons import load_index, search  # noqa: E402


COMPARISONS = {
    "schema_version": 1,
    "comparison_count": 2,
    "comparisons": [
        {
            "schema_version": 1,
            "id": "relational-databases",
            "title": "PostgreSQL vs MySQL vs SQLite",
            "summary": "A deployment- and architecture-first comparison of three relational database engines.",
            "verified_at": "2026-09-06",
            "modules": [
                {
                    "ref": "database/postgresql",
                    "name": "PostgreSQL",
                    "summary": "Client/server relational database with MVCC and WAL.",
                },
                {
                    "ref": "database/mysql",
                    "name": "MySQL",
                    "summary": "Client/server relational database centered on InnoDB.",
                },
                {
                    "ref": "database/sqlite",
                    "name": "SQLite",
                    "summary": "Embedded relational database with pager and single-writer behavior.",
                },
            ],
            "dimensions": [
                {
                    "id": "concurrency-model",
                    "label": "Concurrency model",
                    "values": {
                        "database/postgresql": "Many writers can progress concurrently when they do not conflict.",
                        "database/mysql": "Many InnoDB writers can progress on different records.",
                        "database/sqlite": "Only one write transaction can modify a database file at a time.",
                    },
                },
                {
                    "id": "durability-journal",
                    "label": "Durability and journal model",
                    "values": {
                        "database/postgresql": "Uses write-ahead logging and checkpoints.",
                        "database/mysql": "Uses InnoDB redo and binary logs for different purposes.",
                        "database/sqlite": "Uses rollback journals or WAL with checkpoints.",
                    },
                },
            ],
            "decision_rules": [
                {
                    "condition": "The application needs embedded local storage without a database server.",
                    "consider": ["database/sqlite"],
                    "reason": "SQLite removes the network server boundary.",
                }
            ],
            "notes": ["This fixture compares database deployment and concurrency boundaries."],
        },
        {
            "schema_version": 1,
            "id": "terraform-opentofu",
            "title": "Terraform vs OpenTofu",
            "summary": "A compatibility- and lifecycle-first infrastructure-as-code comparison.",
            "verified_at": "2026-09-06",
            "modules": [
                {
                    "ref": "cloud/terraform",
                    "name": "Terraform",
                    "summary": "Infrastructure-as-code engine with provider-driven resource lifecycle management.",
                },
                {
                    "ref": "tool/opentofu",
                    "name": "OpenTofu",
                    "summary": "Open-source Terraform-compatible infrastructure-as-code engine.",
                },
            ],
            "dimensions": [
                {
                    "id": "state-plan-security",
                    "label": "State and plan security",
                    "values": {
                        "cloud/terraform": "Protect state backends and plan artifacts operationally.",
                        "tool/opentofu": "Adds native application-level state and plan encryption.",
                    },
                },
                {
                    "id": "core-license",
                    "label": "Core license",
                    "values": {
                        "cloud/terraform": "Terraform Core uses BUSL-1.1.",
                        "tool/opentofu": "OpenTofu Core uses MPL-2.0.",
                    },
                },
            ],
            "decision_rules": [
                {
                    "condition": "Native state and plan encryption is required.",
                    "consider": ["tool/opentofu"],
                    "reason": "OpenTofu includes native encryption with configurable key providers.",
                }
            ],
            "notes": ["Provider compatibility should be pinned and tested rather than assumed forever."],
        },
    ],
}


class ComparisonSearchTests(unittest.TestCase):
    def test_build_and_search_comparison_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            input_path = root / "comparisons.json"
            output_path = root / "search.json"
            input_path.write_text(json.dumps(COMPARISONS), encoding="utf-8")

            payload = build(input_path, output_path)
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["comparison_count"], 2)
            self.assertTrue(output_path.is_file())

            entries = load_index(output_path)
            encryption = search(entries, "state encryption")
            self.assertEqual(encryption[0]["id"], "terraform-opentofu")
            self.assertGreater(encryption[0]["score"], 0)

            wal = search(entries, "wal checkpoints")
            self.assertEqual(wal[0]["id"], "relational-databases")

            module = search(entries, "", module="database/sqlite")
            self.assertEqual([entry["id"] for entry in module], ["relational-databases"])

    def test_generated_record_has_compact_discovery_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            input_path = root / "comparisons.json"
            output_path = root / "search.json"
            input_path.write_text(json.dumps(COMPARISONS), encoding="utf-8")
            build(input_path, output_path)

            entries = load_index(output_path)
            terraform = next(item for item in entries if item["id"] == "terraform-opentofu")
            self.assertEqual(terraform["module_refs"], ["cloud/terraform", "tool/opentofu"])
            self.assertEqual(terraform["module_names"], ["Terraform", "OpenTofu"])
            self.assertEqual(terraform["dimension_count"], 2)
            self.assertEqual(terraform["decision_rule_count"], 1)
            self.assertIn("state-plan-security", terraform["dimension_ids"])
            self.assertIn("state and plan security", terraform["search_text"])
            self.assertTrue(terraform["url"].endswith("docs/comparisons/terraform-opentofu.md"))

    def test_exact_title_and_id_rank_strongly(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            input_path = root / "comparisons.json"
            output_path = root / "search.json"
            input_path.write_text(json.dumps(COMPARISONS), encoding="utf-8")
            build(input_path, output_path)
            entries = load_index(output_path)

            by_id = search(entries, "terraform-opentofu")
            self.assertEqual(by_id[0]["id"], "terraform-opentofu")
            self.assertGreaterEqual(by_id[0]["score"], 150)

            by_title = search(entries, "PostgreSQL vs MySQL vs SQLite")
            self.assertEqual(by_title[0]["id"], "relational-databases")
            self.assertGreaterEqual(by_title[0]["score"], 140)

    def test_module_filter_combines_with_query(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            input_path = root / "comparisons.json"
            output_path = root / "search.json"
            input_path.write_text(json.dumps(COMPARISONS), encoding="utf-8")
            build(input_path, output_path)
            entries = load_index(output_path)

            self.assertEqual(
                search(entries, "encryption", module="database/sqlite"),
                [],
            )
            results = search(entries, "encryption", module="tool/opentofu")
            self.assertEqual(results[0]["id"], "terraform-opentofu")

    def test_invalid_payload_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            input_path = root / "comparisons.json"
            output_path = root / "search.json"
            broken = json.loads(json.dumps(COMPARISONS))
            broken["comparisons"][0]["dimensions"][0]["values"]["database/sqlite"] = None
            input_path.write_text(json.dumps(broken), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "contains an invalid value"):
                build(input_path, output_path)


if __name__ == "__main__":
    unittest.main()
