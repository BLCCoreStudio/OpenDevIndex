from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from taxonomy import (  # noqa: E402
    enrich_entry,
    load_taxonomy,
    supported_address_categories,
    supported_relationship_types,
)


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

    def test_explicit_facets_take_precedence(self) -> None:
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

    def test_v3_address_namespaces_are_supported(self) -> None:
        categories = supported_address_categories(load_taxonomy())
        for category in (
            "library", "runtime", "platform", "standard", "toolchain",
            "hardware", "architecture", "algorithm", "model", "format",
            "device", "dataset", "technique",
        ):
            self.assertIn(category, categories)

    def test_v3_relationship_types_are_supported(self) -> None:
        relationships = supported_relationship_types(load_taxonomy())
        for relationship in (
            "depends-on", "implements", "alternative-to", "successor-of",
            "built-with", "compatible-with", "related-to",
        ):
            self.assertIn(relationship, relationships)

    def test_relationship_validation_happens_during_enrichment(self) -> None:
        entry = {
            "category": "hardware",
            "id": "example-cpu",
            "name": "Example CPU",
            "summary": "An example processor used to exercise hardware taxonomy and graph relationships in tests.",
            "tags": ["hardware", "systems", "architecture"],
            "relationships": [
                {"type": "implements", "target": "architecture/example-isa"},
                {"type": "related-to", "target": "concept/example-computing"},
            ],
        }
        enriched = enrich_entry(entry)
        self.assertEqual(enriched["kind"], "hardware")
        self.assertIn("hardware", enriched["domains"])


if __name__ == "__main__":
    unittest.main()
