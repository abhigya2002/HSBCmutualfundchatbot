"""Optional bridge to Phase 4.6 retrieval service for integration tests."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


def phase4_retrieval_root() -> Path:
    return Path(__file__).resolve().parents[2] / "phase-4-retrieval"


def ensure_phase4_on_path() -> Path:
    root = phase4_retrieval_root()
    s = str(root.resolve())
    if s not in sys.path:
        sys.path.insert(0, s)
    return root


def retrieve_outcome(query: str, *, session_id: str = "") -> Any:
    ensure_phase4_on_path()
    from phase_4_6.service import retrieve

    return retrieve(query, session_id=session_id)
