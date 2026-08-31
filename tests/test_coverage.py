from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validate_coverage import validate  # noqa: E402


class CoverageTests(unittest.TestCase):
    def test_technology_universe_v1_is_valid(self) -> None:
        path = ROOT / "coverage/technology-universe-v1.yaml"
        self.assertEqual(validate(path), [])


if __name__ == "__main__":
    unittest.main()
