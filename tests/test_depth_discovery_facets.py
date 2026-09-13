from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_depth_discovery import discovery_counts, render_markdown  # noqa: E402


RECORDS = [
    {
        "ref": "tool/alpha",
        "name": "Alpha",
        "kind": "tool",
        "domains": ["developer-tools", "testing"],
        "maturity": "deep-dive",
        "reviewed_at": "2026-09-01",
        "summary": "Alpha summary.",
        "url": "https://github.com/BLCCoreStudio/OpenDevIndex/tree/tool/alpha/entry",
    },
    {
        "ref": "framework/beta",
        "name": "Beta",
        "kind": "framework",
        "domains": ["developer-tools"],
        "maturity": "guide",
        "reviewed_at": "2026-08-31",
        "summary": "Beta summary.",
        "url": "https://github.com/BLCCoreStudio/OpenDevIndex/tree/framework/beta/entry",
    },
]


class DepthDiscoveryFacetTests(unittest.TestCase):
    def test_counts_include_kind_and_domain_facets(self) -> None:
        maturity, kinds, domains = discovery_counts(RECORDS)

        self.assertEqual(maturity, {"deep-dive": 1, "guide": 1})
        self.assertEqual(kinds, {"tool": 1, "framework": 1})
        self.assertEqual(domains, {"developer-tools": 2, "testing": 1})

    def test_markdown_facets_link_to_matching_modules(self) -> None:
        rendered = render_markdown(RECORDS)

        self.assertIn("## Reviewed depth by kind", rendered)
        self.assertIn("## Reviewed depth by domain", rendered)
        self.assertIn("| `tool` | 1 | [Alpha](https://github.com/BLCCoreStudio/OpenDevIndex/tree/tool/alpha/entry) |", rendered)
        self.assertIn("| `framework` | 1 | [Beta](https://github.com/BLCCoreStudio/OpenDevIndex/tree/framework/beta/entry) |", rendered)
        self.assertIn(
            "| `developer-tools` | 2 | [Alpha](https://github.com/BLCCoreStudio/OpenDevIndex/tree/tool/alpha/entry), [Beta](https://github.com/BLCCoreStudio/OpenDevIndex/tree/framework/beta/entry) |",
            rendered,
        )
        self.assertIn("**[Deep dives](#deep-dives):** 1", rendered)
        self.assertIn("**[Guides](#guides):** 1", rendered)


if __name__ == "__main__":
    unittest.main()
