from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from taxonomy import enrich_entry, load_taxonomy, supported_address_categories  # noqa: E402


class TaxonomyTests(unittest.TestCase):
    def test_tensorflow_legacy_address_maps_to_framework(self) -> None:
        entry = {
            "category": "ai",
            "id": "tensorflow",
            "name": "TensorFlow",
            "summary": "A machine-learning framework used to train and deploy computational models.",
            "tags": ["machine-learning", "deep-learning", "python"],
        }
        enriched = enrich_entry(entry)
        self.assertEqual(enriched["module_ref"], "ai/tensorflow")
        self.assertEqual(enriched["kind"], "framework")
        self.assertIn("ai", enriched["domains"])
        self.assertIn("machine-learning", enriched["domains"])

    def test_explicit_v2_facets_take_precedence(self) -> None:
        entry = {
            "category": "platform",
            "id": "example",
            "name": "Example",
            "summary": "An example platform used only to verify explicit taxonomy facet precedence in unit tests.",
            "tags": ["api", "testing", "developer-tools"],
            "kind": "service",
            "domains": ["api", "testing"],
        }
        enriched = enrich_entry(entry)
        self.assertEqual(enriched["kind"], "service")
        self.assertEqual(enriched["domains"], ["api", "developer-tools", "testing"])

    def test_new_address_namespaces_are_supported(self) -> None:
        categories = supported_address_categories(load_taxonomy())
        for category in ("library", "runtime", "platform", "standard", "toolchain"):
            self.assertIn(category, categories)


if __name__ == "__main__":
    unittest.main()
