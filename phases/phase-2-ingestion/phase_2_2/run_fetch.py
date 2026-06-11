"""
Phase 2.2 — Fetch all allowlisted Groww scheme pages and write raw HTML + crawl JSON.

Run from ``phases/phase-2-ingestion``::

    python -m phase_2_2.run_fetch
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from common.config import default_config_path, load_config, phase2_ingestion_root
from common.logging_setup import setup_ingestion_logging
from common.paths import ArtifactPaths
from common.registry_bridge import validate_registry_or_raise

from phase_2_2.fetcher import fetch_allowlisted_url
from phase_2_2.raw_store import persist_fetch

log = logging.getLogger("phase2_ingestion.phase_2_2")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 2.2 — fetch allowlisted corpus URLs.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Write fetch_report.json (default: <artifact_root>/fetch_report.json)",
    )
    args = parser.parse_args(argv)

    phase2_root = phase2_ingestion_root()
    config = load_config(args.config)
    setup_ingestion_logging(config)

    paths = ArtifactPaths.from_config(config, phase2_root)
    paths.ensure_dirs()

    registry = validate_registry_or_raise()
    rows: list[dict[str, object]] = []
    ok_count = 0
    for entry in sorted(registry["entries"], key=lambda e: int(e["id"])):
        slug = str(entry["scheme"])
        url = str(entry["url"])
        log.info("Fetching %s", url)
        fr = fetch_allowlisted_url(url, config)
        crawl = persist_fetch(paths, slug, url, fr)
        rows.append(crawl)
        if crawl.get("fetch_status") in ("ok", "challenge_suspect"):
            ok_count += 1

    report_path = args.report or (paths.root / "fetch_report.json")
    summary = {
        "phase": "2.2",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "entry_count": len(rows),
        "ok_html_count": ok_count,
        "entries": rows,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log.info("Wrote fetch report: %s", report_path)
    failed = sum(1 for r in rows if r.get("fetch_status") == "failed")
    print(json.dumps({"ok_or_challenge_count": ok_count, "failed": failed, "total": len(rows), "report": str(report_path)}, indent=2))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
