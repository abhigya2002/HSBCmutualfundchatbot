"""Log FastAPI registered routes at startup (Phase 6.2)."""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("phase6_api_ui.phase_6_2.routes")


def log_registered_routes(app: Any) -> None:
    """Print every route path and HTTP method to the terminal log."""
    log.info("Registered routes:")
    for route in app.routes:
        path = getattr(route, "path", None)
        if path is None:
            continue
        methods = getattr(route, "methods", None)
        if methods:
            visible = sorted(m for m in methods if m not in {"HEAD", "OPTIONS"})
            method_str = ",".join(visible) if visible else "GET"
        else:
            method_str = "MOUNT"
        name = getattr(route, "name", "")
        log.info("  %-8s %s%s", method_str, path, f"  ({name})" if name else "")
