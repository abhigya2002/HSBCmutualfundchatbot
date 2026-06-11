"""
Phase 6.3 — CLI smoke test for ``POST /chat``.

Run from ``phases/phase-6-api-ui`` (server must be running)::

    python -m phase_6_3.run_chat --query "expense ratio HSBC Gilt Fund Direct Growth"
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from phase_6_1.config_load import load_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 6.3 — POST /chat smoke client.")
    parser.add_argument("--query", "-q", required=True)
    parser.add_argument("--session-id", default="")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    server = dict(config.get("server") or {})
    host = str(server.get("host") or "127.0.0.1")
    port = int(server.get("port") or 8000)
    base = (args.base_url or f"http://{host}:{port}").rstrip("/")

    payload = {"query": args.query.strip()}
    if args.session_id.strip():
        payload["session_id"] = args.session_id.strip()

    req = urllib.request.Request(
        f"{base}/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=float(server.get("request_timeout_seconds") or 30)) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(detail, file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Could not reach {base}/chat: {exc.reason}", file=sys.stderr)
        return 1

    print(json.dumps(body, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
