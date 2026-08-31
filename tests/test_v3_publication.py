from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from seed_modules import render_metadata, render_readme  # noqa: E402
from validate_catalog import validate  # noqa: E402


class V3PublicationTests(unittest.TestCase):
    def make_catalog(self, relationship_type: str = "related-to") -> dict:
        return {
            "schema_version": 3,
            "milestone": "test-v3",
            "verified_at": "2026-08-31",
            "target_modules": 1,
            "expected_categories": {"architecture": 1},
            "entries": [
                {
                    "category": "architecture",
                    "id": "example-isa",
                    "name": "Example ISA",
                    "summary": (
                        "A representative instruction-set architecture entry used to verify "
                        "taxonomy-v3 catalog and knowledge-graph publication behavior."
                    ),
                    "homepage": "https://riscv.org/",
                    "repository": "https://github.com/riscv/riscv-isa-manual",
                    "tags": ["architecture", "hardware", "systems"],
                    "kind": "architecture",
                    "domains": ["computer-architecture", "hardware", "systems"],
                    "deployment_types": ["hardware"],
                    "relationships": [
                        {
                            "type": relationship_type,
                            "target": "hardware/example-cpu",
                            "note": "Exercises typed graph-edge preservation during publication.",
                        }
                    ],
                    "sources": [
                        {
                            "title": "RISC-V International",
                            "url": "https://riscv.org/",
                            "type": "official",
                        },
                        {
                            "title": "RISC-V ISA manual repository",
                            "url": "https://github.com/riscv/riscv-isa-manual",
                            "type": "repository",
                        },
                    ],
                    "use_cases": [
                        "Describe an instruction-set architecture in a structured technology index",
                        "Connect hardware implementations to the architecture they implement",
                        "Support discovery and graph navigation across systems and hardware topics",
                    ],
                    "key_points": [
                        "Taxonomy v3 catalogs can represent architecture modules directly",
                        "Typed relationships provide explicit machine-readable graph edges",
                        "Publication must preserve graph metadata rather than dropping relationships",
                    ],
                }
            ],
        }

    def write_catalog(self, data: dict) -> Path:
        handle = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8")
        with handle:
            yaml.safe_dump(data, handle, sort_keys=False)
        self.addCleanup(Path(handle.name).unlink, missing_ok=True)
        return Path(handle.name)

    def test_v3_catalog_with_relationships_validates(self) -> None:
        path = self.write_catalog(self.make_catalog())
        self.assertEqual(validate(path), [])

    def test_v3_catalog_rejects_unknown_relationship_type(self) -> None:
        path = self.write_catalog(self.make_catalog("not-a-real-edge"))
        errors = validate(path)
        self.assertTrue(any("unsupported type" in error for error in errors), errors)

    def test_publisher_preserves_relationships_in_metadata_and_readme(self) -> None:
        entry = self.make_catalog()["entries"][0]
        entry["module_ref"] = "architecture/example-isa"
        entry["verified_at"] = "2026-08-31"
        metadata = yaml.safe_load(render_metadata(entry, "2026-08-31", 3))
        self.assertEqual(metadata["schema_version"], 3)
        self.assertEqual(metadata["relationships"], entry["relationships"])

        readme = render_readme(entry)
        self.assertIn("## Relationships", readme)
        self.assertIn("`related-to`", readme)
        self.assertIn("`hardware/example-cpu`", readme)


if __name__ == "__main__":
    unittest.main()
