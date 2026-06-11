"""
Phase 5.1 — Dry load: validate Phase 4 handoff and guardrails config (no response composition).

Run from ``phases/phase-5-guardrails``::

    python -m phase_5_1.dry_load
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from phase_5_1 import PHASE_5_1_VERSION
from phase_5_1.config_load import default_config_path, load_config, phase5_guardrails_root
from phase_5_1.handoff import build_phase5_handoff_context
from phase_5_1.logging_setup import setup_logging
from phase_5_1.paths import GuardrailsArtifactPaths

log = logging.getLogger("phase5_guardrails.phase_5_1.dry")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 5.1 dry load — Phase 4 handoff + config validation.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    setup_logging(config)

    root = phase5_guardrails_root()
    paths = GuardrailsArtifactPaths.from_config(config, root)
    paths.ensure_dirs()

    log.info("Phase 5.1 dry load — workspace: %s", root)
    log.info("Config: %s", args.config or default_config_path())

    ctx = build_phase5_handoff_context(config)

    errors = [i for i in ctx.issues if i.code.startswith("error_") or i.code.startswith("missing_")]
    warnings = [i for i in ctx.issues if i not in errors]

    manifest = {
        "phase": "5.1",
        "phase_5_1_version": PHASE_5_1_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "handoff_path": str(ctx.handoff_path),
        "index_version": ctx.index_version,
        "embedding_model_id": ctx.embedding_model_id,
        "registry_entry_count": ctx.registry_entry_count,
        "composer": {
            "max_sentences": ctx.composer.max_sentences,
            "citation_format": ctx.composer.citation_format,
            "default_citation_url": ctx.composer.default_citation_url,
            "footer_template": ctx.composer.footer_template,
            "disclaimer_line": ctx.composer.disclaimer_line,
        },
        "prohibited_phrase_counts": {
            "advisory": len(ctx.prohibited.advisory_patterns),
            "comparison": len(ctx.prohibited.comparison_patterns),
            "projection": len(ctx.prohibited.projection_patterns),
            "injection": len(ctx.prohibited.injection_patterns),
            "regex": len(ctx.prohibited.regex_patterns),
        },
        "refusal_types": (ctx.phase5_handoff.get("refusal_contract") or {}).get("refusal_types") or [],
        "evidence_fields_found": (ctx.phase5_handoff.get("evidence_fields_for_phase5") or {}).get("found") or [],
        "ready_for_phase_5_2": len(errors) == 0,
        "errors": [{"code": i.code, "message": i.message} for i in errors],
        "warnings": [{"code": i.code, "message": i.message} for i in warnings],
    }

    out = args.json_out or paths.dry_manifest_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    paths.handoff_validation_path().write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log.info("Wrote %s", out)

    for e in errors:
        log.error("[%s] %s", e.code, e.message)
    for w in warnings:
        log.warning("[%s] %s", w.code, w.message)

    if errors:
        return 1
    log.info("Dry load complete — ready for Phase 5.2.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
