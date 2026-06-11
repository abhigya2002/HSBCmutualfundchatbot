"""
Phase 6.1 — Dry load: validate Phase 5 handoff, config, and GenerationService (no HTTP server).

Run from ``phases/phase-6-api-ui``::

    python -m phase_6_1.dry_load
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from phase_6_1 import PHASE_6_1_VERSION
from phase_6_1.config_load import default_config_path, load_config, phase6_api_ui_root
from phase_6_1.env_bridge import probe_groq_status
from phase_6_1.generation_bridge import ensure_phase5_on_path, probe_generation_service
from phase_6_1.handoff import HandoffIssue, build_phase6_handoff_context, workspace_layout_ok
from phase_6_1.logging_setup import setup_logging
from phase_6_1.paths import ApiUiArtifactPaths

log = logging.getLogger("phase6_api_ui.phase_6_1.dry")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 6.1 dry load — Phase 5 handoff + config + GenerationService validation.",
    )
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    setup_logging(config)

    root = phase6_api_ui_root()
    paths = ApiUiArtifactPaths.from_config(config, root)
    paths.ensure_dirs()

    log.info("Phase 6.1 dry load — workspace: %s", root)
    log.info("Config: %s", args.config or default_config_path())

    ctx = build_phase6_handoff_context(config)
    layout_issues = workspace_layout_ok(root)
    ctx.issues.extend(layout_issues)

    ensure_phase5_on_path(config)
    gen_probe = probe_generation_service(config)
    if not gen_probe.instantiated:
        ctx.issues.append(
            HandoffIssue("error_generation_service", gen_probe.error or "instantiation failed"),
        )

    groq = probe_groq_status(phase5_on_path=True)

    errors = [
        i
        for i in ctx.issues
        if i.code.startswith("error_") or i.code.startswith("missing_") or i.code.startswith("invalid_")
    ]
    warnings = [i for i in ctx.issues if i not in errors]

    manifest = {
        "phase": "6.1",
        "phase_6_1_version": PHASE_6_1_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(root),
        "handoff_path": str(ctx.handoff_path),
        "handoff_phase": ctx.phase6_handoff.get("phase"),
        "phase_5_6_version": ctx.phase6_handoff.get("phase_5_6_version"),
        "chat_endpoint_path": ctx.chat_endpoint_path,
        "answer_envelope_fields": ctx.answer_envelope_fields,
        "outcome_types": ctx.outcome_types,
        "server": {
            "host": ctx.server.host,
            "port": ctx.server.port,
            "request_timeout_seconds": ctx.server.request_timeout_seconds,
        },
        "validation_limits": {
            "max_request_body_bytes": ctx.validation.max_request_body_bytes,
            "max_query_length": ctx.validation.max_query_length,
            "max_session_id_length": ctx.validation.max_session_id_length,
            "required_content_type": ctx.validation.required_content_type,
        },
        "cors": {
            "dev_origins": ctx.cors.dev_origins,
            "prod_origins": ctx.cors.prod_origins,
        },
        "logging": {
            "level": ctx.logging.level,
            "redact_pii": ctx.logging.redact_pii,
            "redact_field_names": ctx.logging.redact_field_names,
        },
        "generation_service": {
            "class": gen_probe.service_class,
            "guardrails_root": str(gen_probe.guardrails_root),
            "instantiated": gen_probe.instantiated,
            "error": gen_probe.error,
        },
        "groq_env": {
            "dotenv_path": str(groq.dotenv_path),
            "dotenv_found": groq.dotenv_found,
            "use_groq": groq.use_groq,
            "api_key_configured": groq.api_key_configured,
            "groq_composer_enabled": groq.groq_composer_enabled,
            "note": groq.note,
        },
        "evaluation_summary": ctx.phase6_handoff.get("evaluation_summary") or {},
        "ready_for_phase_6_2": len(errors) == 0 and gen_probe.instantiated,
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

    if errors or not gen_probe.instantiated:
        return 1
    log.info("Dry load complete — ready for Phase 6.2.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
