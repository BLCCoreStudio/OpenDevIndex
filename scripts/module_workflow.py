#!/usr/bin/env python3
"""Keep independently versioned module branches on a minimal, current validation workflow."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates/module-validate.yml"
WORKFLOW_RELATIVE = Path(".github/workflows/validate.yml")


def sync_module_workflow(worktree: Path) -> bool:
    """Replace inherited core workflows with the single module-validation workflow."""
    if not TEMPLATE.is_file():
        raise FileNotFoundError(f"module workflow template not found: {TEMPLATE}")

    desired = TEMPLATE.read_text(encoding="utf-8")
    workflow_dir = worktree / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)

    changed = False
    target = worktree / WORKFLOW_RELATIVE
    for pattern in ("*.yml", "*.yaml"):
        for path in workflow_dir.glob(pattern):
            if path == target:
                continue
            path.unlink()
            changed = True

    current = target.read_text(encoding="utf-8") if target.is_file() else None
    if current != desired:
        target.write_text(desired, encoding="utf-8")
        changed = True

    return changed
