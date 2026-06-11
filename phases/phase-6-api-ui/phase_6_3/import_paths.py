"""Insert project-root and cross-phase paths so ``phase_5_*`` imports resolve."""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]


def ensure_project_import_paths() -> Path:
    """Make Phase 4/5 packages importable from ``phase-6-api-ui``."""
    root = str(_PROJECT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)

    for rel in (
        "phases/phase-5-guardrails",
        "phases/phase-4-retrieval",
    ):
        path = str(_PROJECT_ROOT / rel)
        if path not in sys.path:
            sys.path.insert(0, path)

    return _PROJECT_ROOT


ensure_project_import_paths()
