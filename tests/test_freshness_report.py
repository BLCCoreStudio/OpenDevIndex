from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from freshness_report import parse_verified_at, stale_entries  # noqa: E402


class FreshnessReportTests(unittest.TestCase):
    def test_reports_only_entries_older_than_cutoff(self) -> None:
        entries = [
            {
                "ref": "tool/old",
                "name": "Old Tool",
                "verified_at": "2025-01-01",
                "maturity": "guide",
                "url": "https://example.com/old",
            },
            {
                "ref": "tool/boundary",
                "name": "Boundary Tool",
                "verified_at": "2025-09-06",
                "maturity": "overview",
            },
            {
                "ref": "tool/fresh",
                "name": "Fresh Tool",
                "verified_at": "2026-08-01",
                "maturity": "deep-dive",
            },
        ]

        results = stale_entries(entries, as_of=date(2026, 9, 6), max_age_days=365)

        self.assertEqual([entry["ref"] for entry in results], ["tool/old"])
        self.assertEqual(results[0]["age_days"], 613)
        self.assertEqual(results[0]["maturity"], "guide")

    def test_orders_oldest_entries_first(self) -> None:
        entries = [
            {"ref": "tool/newer", "name": "Newer", "verified_at": "2024-06-01"},
            {"ref": "tool/older", "name": "Older", "verified_at": "2023-01-01"},
        ]

        results = stale_entries(entries, as_of=date(2026, 9, 6), max_age_days=30)

        self.assertEqual([entry["ref"] for entry in results], ["tool/older", "tool/newer"])

    def test_accepts_iso_datetime_values(self) -> None:
        self.assertEqual(
            parse_verified_at("2026-09-06T13:45:00Z"),
            date(2026, 9, 6),
        )

    def test_rejects_missing_or_invalid_dates(self) -> None:
        for value in (None, "", "not-a-date"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_verified_at(value)

    def test_rejects_future_verification_dates(self) -> None:
        with self.assertRaisesRegex(ValueError, "after as-of date"):
            stale_entries(
                [{"ref": "tool/future", "name": "Future", "verified_at": "2026-09-07"}],
                as_of=date(2026, 9, 6),
                max_age_days=365,
            )

    def test_rejects_negative_freshness_window(self) -> None:
        with self.assertRaisesRegex(ValueError, "zero or greater"):
            stale_entries([], as_of=date(2026, 9, 6), max_age_days=-1)


if __name__ == "__main__":
    unittest.main()
