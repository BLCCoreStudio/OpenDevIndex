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

from seed_modules import refresh_protection_reason  # noqa: E402


class PublisherProtectionTests(unittest.TestCase):
    def make_worktree(self, metadata: dict) -> Path:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(root, ignore_errors=True))
        entry = root / "entry"
        entry.mkdir(parents=True)
        (entry / "entry.yaml").write_text(
            yaml.safe_dump(metadata, sort_keys=False),
            encoding="utf-8",
        )
        return root

    def test_deep_dive_tag_protects_module(self) -> None:
        worktree = self.make_worktree({"schema_version": 3, "tags": ["git", "deep-dive"]})
        reason = refresh_protection_reason(worktree, 3)
        self.assertIsNotNone(reason)
        self.assertIn("deep-dive", reason or "")

    def test_schema_downgrade_is_protected(self) -> None:
        worktree = self.make_worktree({"schema_version": 3, "tags": ["git"]})
        self.assertEqual(refresh_protection_reason(worktree, 1), "schema downgrade 3 -> 1")

    def test_equal_schema_overview_can_refresh(self) -> None:
        worktree = self.make_worktree({"schema_version": 3, "tags": ["git"]})
        self.assertIsNone(refresh_protection_reason(worktree, 3))

    def test_missing_metadata_does_not_block_refresh(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(root, ignore_errors=True))
        self.assertIsNone(refresh_protection_reason(root, 3))


if __name__ == "__main__":
    unittest.main()
