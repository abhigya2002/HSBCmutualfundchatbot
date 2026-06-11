"""
Phase 6.2 — Run the API server (health + validation only; chat in 6.3).

Run from ``phases/phase-6-api-ui``::

    python -m phase_6_2.run_server
    python -m phase_6_2.run_server --host 0.0.0.0 --port 8080
"""

from __future__ import annotations

import argparse
import logging
import sys

from phase_6_1.config_load import load_config
from phase_6_2.app import create_app
from phase_6_2.route_log import log_registered_routes

log = logging.getLogger("phase6_api_ui.phase_6_2.run")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 6.2 API server.")
    parser.add_argument("--host", type=str, default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--config", type=str, default=None)
    args = parser.parse_args(argv)

    config = load_config()
    if args.config:
        from pathlib import Path

        config = load_config(Path(args.config))

    server = dict(config.get("server") or {})
    host = args.host or str(server.get("host") or "127.0.0.1")
    port = args.port or int(server.get("port") or 8000)

    try:
        import uvicorn
    except ImportError:
        log.error("uvicorn is not installed — pip install -r requirements.txt")
        return 1

    app = create_app(config)
    log_registered_routes(app)
    log.info("Starting Phase 6.2 API on http://%s:%s", host, port)
    log.info("Health check: http://%s:%s/health", host, port)
    uvicorn.run(app, host=host, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
