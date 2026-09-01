from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from module_maturity import load_maturity_manifest, maturity_counts, module_level  # noqa: E402


VALID = """schema_version: 1
default_level: overview
levels: [overview, guide, deep-dive]
modules:
  tool/git:
    level: deep-dive
    reviewed_at: '2026-09-01'
    note: Flagship module.
  tool/example:
    level: guide
    reviewed_at: '2026-08-31'
"""


class ModuleMaturityTests(unittest.TestCase):
    def write(self, content: str) -> Path:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(root, ignore_errors=True))
        path = root / "maturity.yaml"
        path.write_text(content, encoding="utf-8")
        return path

    def test_valid_manifest_and_default(self) -> None:
        manifest = load_maturity_manifest(
            self.write(VALID),
            {"tool/git", "tool/example", "tool/other"},
        )
        self.assertEqual(module_level("tool/git", manifest), "deep-dive")
        self.assertEqual(module_level("tool/example", manifest), "guide")
        self.assertEqual(module_level("tool/other", manifest), "overview")
        self.assertEqual(
            maturity_counts(["tool/git", "tool/example", "tool/other"], manifest),
            {"overview": 1, "guide": 1, "deep-dive": 1},
        )

    def test_unknown_module_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown module tool/example"):
            load_maturity_manifest(self.write(VALID), {"tool/git"})

    def test_invalid_level_fails(self) -> None:
        content = VALID.replace("level: guide", "level: finished")
        with self.assertRaisesRegex(ValueError, "invalid level"):
            load_maturity_manifest(
                self.write(content),
                {"tool/git", "tool/example"},
            )

    def test_future_review_date_fails(self) -> None:
        content = VALID.replace("'2026-09-01'", "'2099-01-01'")
        with self.assertRaisesRegex(ValueError, "cannot be in the future"):
            load_maturity_manifest(
                self.write(content),
                {"tool/git", "tool/example"},
            )


if __name__ == "__main__":
    unittest.main()
