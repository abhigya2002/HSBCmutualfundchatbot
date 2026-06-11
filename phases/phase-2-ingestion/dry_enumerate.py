"""
Backward-compatible launcher for Phase 2.1.

Prefer: ``python -m phase_2_1.dry_enumerate`` (from ``phases/phase-2-ingestion``).
"""

from __future__ import annotations

import sys

from phase_2_1.dry_enumerate import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
