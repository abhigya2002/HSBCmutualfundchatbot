"""
Phase 2.1 — Dry pipeline: validate Phase 1 registry, ensure artifact dirs, enumerate 16 URLs.

No HTTP. Run from ``phases/phase-2-ingestion``::

    python -m phase_2_1.dry_enumerate
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from common.config import default_config_path, load_config, phase2_ingestion_root
from common.logging_setup import setup_ingestion_logging
from common.paths import ArtifactPaths
from common.registry_bridge import validate_registry_or_raise

log = logging.getLogger("phase2_ingestion.phase_2_1.dry")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 2.1 dry enumeration (no fetch).")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help=f"Path to JSON config (default: {default_config_path()})",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="If set, write enumeration manifest JSON to this path.",
    )
    args = parser.parse_args(argv)

    phase2_root = phase2_ingestion_root()
    config = load_config(args.config)
    setup_ingestion_logging(config)

    log.info("Phase 2.1 dry run - workspace: %s", phase2_root)
    log.info("Loading config from %s", args.config or default_config_path())

    paths = ArtifactPaths.from_config(config, phase2_root)
    paths.ensure_dirs()
    log.info(
        "Artifact dirs ready: raw=%s clean=%s metadata=%s extracted=%s",
        paths.raw,
        paths.clean,
        paths.metadata,
        paths.extracted,
    )

    registry = validate_registry_or_raise()
    entries = registry["entries"]
    log.info("Registry validated: %d entries", len(entries))

    manifest_rows: list[dict[str, str]] = []
    for e in sorted(entries, key=lambda x: int(x["id"])):
        slug = str(e["scheme"])
        url = str(e["url"])
        row = {
            "id": str(e["id"]),
            "scheme": slug,
            "url": url,
            "planned_raw": str(paths.planned_raw_path(slug)),
            "planned_clean": str(paths.planned_clean_path(slug)),
            "planned_metadata": str(paths.planned_metadata_path(slug)),
            "planned_extracted_main": str(paths.extracted_main_html_path(slug)),
            "planned_extract_sidecar": str(paths.extract_sidecar_path(slug)),
        }
        manifest_rows.append(row)
        print(f"{e['id']:2}  {slug:50}  {url}")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "phase": "2.1",
            "artifact_root": str(paths.root),
            "entry_count": len(manifest_rows),
            "entries": manifest_rows,
        }
        args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        log.info("Wrote manifest to %s", args.json_out)

    log.info("Dry enumeration complete (%d schemes).", len(manifest_rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
