from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validate_relationships import validate_relationship_targets  # noqa: E402


class RelationshipTargetExistenceTests(unittest.TestCase):
    def write_catalog(self, root: Path, name: str, body: str) -> Path:
        path = root / name
        path.write_text(body, encoding="utf-8")
        return path

    def test_target_in_another_catalog_resolves(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tools = self.write_catalog(
                root,
                "tools.yaml",
                """schema_version: 3
entries:
  - category: tool
    id: demo
    relationships:
      - type: integrates-with
        target: cloud/example
""",
            )
            cloud = self.write_catalog(
                root,
                "cloud.yaml",
                """schema_version: 3
entries:
  - category: cloud
    id: example
""",
            )
            self.assertEqual(validate_relationship_targets([tools, cloud]), [])

    def test_missing_target_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tools = self.write_catalog(
                root,
                "tools.yaml",
                """schema_version: 3
entries:
  - category: tool
    id: demo
    relationships:
      - type: integrates-with
        target: cloud/missing
""",
            )
            errors = validate_relationship_targets([tools])
            self.assertTrue(any("does not exist in the supplied catalogs" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
