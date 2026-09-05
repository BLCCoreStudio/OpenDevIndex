from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validate_entry import is_non_module_ref, validate  # noqa: E402


class ValidateEntryRefTests(unittest.TestCase):
    def test_core_refs_are_not_treated_as_modules(self) -> None:
        for ref in (
            "main",
            "feat/search-facets",
            "fix/catalog-validation",
            "docs/editorial-policy",
            "chore/dependencies",
            "ci/validation",
            "refactor/index-builder",
            "release/v1.0",
        ):
            with self.subTest(ref=ref):
                self.assertTrue(is_non_module_ref(ref))
                self.assertEqual(validate(ref), [])

    def test_dependabot_refs_are_not_treated_as_modules(self) -> None:
        for ref in (
            "dependabot/github_actions/actions/upload-artifact-7.0.1",
            "dependabot/pip/pyyaml-6.0.3",
        ):
            with self.subTest(ref=ref):
                self.assertTrue(is_non_module_ref(ref))
                self.assertEqual(validate(ref), [])

    def test_real_module_refs_still_enter_module_validation(self) -> None:
        self.assertFalse(is_non_module_ref("tool/example-tool"))
        with tempfile.TemporaryDirectory() as temp:
            errors = validate("tool/example-tool", Path(temp))
        self.assertIn("Missing required file: entry/README.md", errors)
        self.assertIn("Missing required file: entry/entry.yaml", errors)

    def test_unknown_slash_prefix_is_not_silently_skipped(self) -> None:
        self.assertFalse(is_non_module_ref("feature/example"))
        with tempfile.TemporaryDirectory() as temp:
            errors = validate("feature/example", Path(temp))
        self.assertIn("Unsupported category prefix: feature", errors)


if __name__ == "__main__":
    unittest.main()
