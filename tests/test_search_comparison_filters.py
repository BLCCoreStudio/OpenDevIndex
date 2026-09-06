from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from search_index import search  # noqa: E402


ENTRIES = [
    {
        "ref": "tool/opentofu",
        "slug": "opentofu",
        "name": "OpenTofu",
        "address_category": "tool",
        "kind": "tool",
        "maturity": "deep-dive",
        "domains": ["cloud", "developer-tools", "devops"],
        "coverage_area": "cloud-devops-sre",
        "coverage_topics": ["infrastructure-as-code"],
        "deployment_types": ["cli"],
        "license": "MPL-2.0",
        "summary": "Open-source infrastructure-as-code engine with Terraform-compatible workflows.",
        "tags": ["iac", "terraform", "opentofu"],
        "use_cases": [],
        "key_points": [],
        "comparisons": [
            {
                "id": "terraform-opentofu",
                "title": "Terraform vs OpenTofu",
                "url": "https://example.com/terraform-opentofu",
            }
        ],
        "search_text": "tool opentofu deep-dive cloud developer-tools devops iac terraform terraform-opentofu terraform vs opentofu",
    },
    {
        "ref": "cloud/terraform",
        "slug": "terraform",
        "name": "Terraform",
        "address_category": "cloud",
        "kind": "tool",
        "maturity": "deep-dive",
        "domains": ["cloud", "devops"],
        "coverage_area": "cloud-devops-sre",
        "coverage_topics": ["infrastructure-as-code"],
        "deployment_types": ["cli"],
        "license": "BUSL-1.1",
        "summary": "Infrastructure-as-code engine for provider-driven resource lifecycle management.",
        "tags": ["iac", "terraform"],
        "use_cases": [],
        "key_points": [],
        "comparisons": [
            {
                "id": "terraform-opentofu",
                "title": "Terraform vs OpenTofu",
                "url": "https://example.com/terraform-opentofu",
            }
        ],
        "search_text": "cloud terraform deep-dive cloud devops iac terraform-opentofu terraform vs opentofu",
    },
    {
        "ref": "tool/docker",
        "slug": "docker",
        "name": "Docker",
        "address_category": "tool",
        "kind": "tool",
        "maturity": "deep-dive",
        "domains": ["containers", "devops"],
        "coverage_area": "cloud-devops-sre",
        "coverage_topics": ["containers"],
        "deployment_types": ["cli"],
        "license": "Apache-2.0",
        "summary": "Container development and packaging tool.",
        "tags": ["containers", "docker"],
        "use_cases": [],
        "key_points": [],
        "comparisons": [],
        "search_text": "tool docker deep-dive containers devops",
    },
]


class ComparisonSearchFilterTests(unittest.TestCase):
    def test_has_comparison_returns_only_linked_modules(self) -> None:
        results = search(ENTRIES, "", has_comparison=True)
        self.assertEqual(
            [entry["ref"] for entry in results],
            ["tool/opentofu", "cloud/terraform"],
        )
        self.assertTrue(all(entry["score"] == 1 for entry in results))

    def test_exact_comparison_filter_returns_members(self) -> None:
        results = search(ENTRIES, "", comparison="terraform-opentofu")
        self.assertEqual(
            {entry["ref"] for entry in results},
            {"tool/opentofu", "cloud/terraform"},
        )

    def test_comparison_filter_combines_with_query(self) -> None:
        results = search(ENTRIES, "terraform", comparison="terraform-opentofu")
        self.assertEqual(results[0]["ref"], "cloud/terraform")
        self.assertGreater(results[0]["score"], 1)
        self.assertNotIn("tool/docker", {entry["ref"] for entry in results})

    def test_unknown_comparison_filter_returns_empty(self) -> None:
        self.assertEqual(search(ENTRIES, "", comparison="missing-comparison"), [])

    def test_has_comparison_combines_with_existing_facets(self) -> None:
        results = search(ENTRIES, "", has_comparison=True, domain="developer-tools")
        self.assertEqual([entry["ref"] for entry in results], ["tool/opentofu"])


if __name__ == "__main__":
    unittest.main()
