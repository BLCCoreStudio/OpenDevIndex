from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from seed_modules import render_history  # noqa: E402


ENTRY = {
    "module_ref": "tool/example-tool",
    "kind": "tool",
    "domains": ["developer-tools", "testing"],
}
VERIFIED_AT = "2026-09-06"
MILESTONE = "v0.test"


class SeedHistoryTests(unittest.TestCase):
    def test_repeated_identical_refresh_is_byte_for_byte_idempotent(self) -> None:
        first = render_history(ENTRY, VERIFIED_AT, MILESTONE)
        second = render_history(ENTRY, VERIFIED_AT, MILESTONE, first)
        third = render_history(ENTRY, VERIFIED_AT, MILESTONE, second)

        self.assertEqual(second, first)
        self.assertEqual(third, first)

    def test_distinct_older_history_is_preserved_once(self) -> None:
        previous = """# History

## 2026-08-31 — v0.1

- Created the initial source-backed module.
"""
        rendered = render_history(ENTRY, VERIFIED_AT, MILESTONE, previous)

        self.assertEqual(rendered.count("## 2026-09-06 — v0.test"), 1)
        self.assertEqual(rendered.count("## 2026-08-31 — v0.1"), 1)
        self.assertEqual(rendered.count("## Earlier history"), 1)
        self.assertIn("Created the initial source-backed module.", rendered)

    def test_legacy_duplicate_refresh_wrappers_are_collapsed(self) -> None:
        older = """# History

## 2026-08-31 — v0.1

- Created the initial source-backed module.
"""
        canonical = render_history(ENTRY, VERIFIED_AT, MILESTONE, older)
        canonical_body = canonical.removeprefix("# History\n\n").strip()
        duplicate = render_history(ENTRY, VERIFIED_AT, MILESTONE)
        duplicate_body = duplicate.removeprefix("# History\n\n").strip()

        legacy_corruption = (
            "# History\n\n"
            + duplicate_body
            + "\n\n## Earlier history\n\n"
            + duplicate_body
            + "\n\n## Earlier history\n\n"
            + canonical_body
            + "\n"
        )

        repaired = render_history(ENTRY, VERIFIED_AT, MILESTONE, legacy_corruption)
        self.assertEqual(repaired, canonical)
        self.assertEqual(repaired.count("## 2026-09-06 — v0.test"), 1)

    def test_different_refresh_event_is_not_deduplicated(self) -> None:
        previous = render_history(ENTRY, "2026-09-05", "v0.previous")
        rendered = render_history(ENTRY, VERIFIED_AT, MILESTONE, previous)

        self.assertEqual(rendered.count("## 2026-09-06 — v0.test"), 1)
        self.assertEqual(rendered.count("## 2026-09-05 — v0.previous"), 1)


if __name__ == "__main__":
    unittest.main()
