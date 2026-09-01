from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from module_workflow import TEMPLATE, sync_module_workflow  # noqa: E402


class ModuleWorkflowTests(unittest.TestCase):
    def test_sync_replaces_inherited_core_workflows(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "validate.yml").write_text("old validator\n", encoding="utf-8")
            (workflows / "index.yml").write_text("core index workflow\n", encoding="utf-8")
            (workflows / "publish.yaml").write_text("core publisher\n", encoding="utf-8")

            self.assertTrue(sync_module_workflow(root))
            self.assertEqual(
                (workflows / "validate.yml").read_text(encoding="utf-8"),
                TEMPLATE.read_text(encoding="utf-8"),
            )
            self.assertFalse((workflows / "index.yml").exists())
            self.assertFalse((workflows / "publish.yaml").exists())

            self.assertFalse(sync_module_workflow(root))

    def test_sync_creates_workflow_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertTrue(sync_module_workflow(root))
            self.assertTrue((root / ".github/workflows/validate.yml").is_file())


if __name__ == "__main__":
    unittest.main()
