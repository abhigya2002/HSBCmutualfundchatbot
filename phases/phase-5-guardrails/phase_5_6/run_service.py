"""
Phase 5.6 — Generation service CLI.

Run from ``phases/phase-5-guardrails``::

    python -m phase_5_6.run_service --query "expense ratio HSBC Gilt Fund Direct Growth"
    python -m phase_5_6.run_service --eval-full
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from phase_5_1.config_load import load_config, phase5_guardrails_root
from phase_5_1.logging_setup import setup_logging
from phase_5_1.paths import GuardrailsArtifactPaths
from phase_5_6 import PHASE_5_6_VERSION
from phase_5_6.contracts import GenerationRequest
from phase_5_6.evaluate import run_full_evaluation
from phase_5_6.handoff import build_phase6_handoff, default_handoff_path, write_phase6_handoff
from phase_5_6.service import GenerationService

log = logging.getLogger("phase5_guardrails.phase_5_6.service")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 5.6 end-to-end generation service.")
    parser.add_argument("--query", "-q", type=str, default="")
    parser.add_argument("--session-id", type=str, default="")
    parser.add_argument("--eval-full", action="store_true", help="Run red-team + factual generation evaluation.")
    parser.add_argument("--write-handoff", action="store_true", help="Write Phase 6 handoff JSON.")
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    setup_logging(config)
    paths = GuardrailsArtifactPaths.from_config(config)
    paths.ensure_dirs()

    try:
        service = GenerationService(config=config)
    except RuntimeError as exc:
        log.error("Service init failed: %s", exc)
        return 1

    if args.eval_full:
        report = run_full_evaluation(service, config=config)
        report["phase"] = "5.6"
        report["phase_5_6_version"] = PHASE_5_6_VERSION
        report["generated_at_utc"] = datetime.now(timezone.utc).isoformat()

        out = args.json_out or (paths.eval / "phase5_6_full_evaluation_report.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        log.info(
            "Eval %s — compliance=%.1f%% redteam=%.1f%% allowlist_clean=%s",
            "PASSED" if report["passed"] else "FAILED",
            report["metrics"]["compliance_pass_rate"] * 100,
            report["metrics"]["redteam_pass_rate"] * 100,
            report.get("allowlist_clean"),
        )

        svc_cfg = config.get("service") or {}
        if args.write_handoff or svc_cfg.get("write_handoff_on_eval", True):
            handoff = build_phase6_handoff(
                eval_summary={
                    "passed": report["passed"],
                    "compliance_pass_rate": report["metrics"]["compliance_pass_rate"],
                    "redteam_pass_rate": report["metrics"]["redteam_pass_rate"],
                    "allowlist_violation_count": report["metrics"]["allowlist_violation_count"],
                },
            )
            handoff_path = default_handoff_path()
            write_phase6_handoff(handoff_path, handoff)
            log.info("Wrote Phase 6 handoff %s", handoff_path)

        return 0 if report["passed"] else 1

    if not args.query.strip():
        parser.error("Provide --query or --eval-full")
        return 2

    envelope = service.answer(GenerationRequest(query=args.query.strip(), session_id=args.session_id))
    payload = envelope.to_dict()
    text = json.dumps(payload, indent=2)
    if args.json_out:
        args.json_out.write_text(text, encoding="utf-8")
        log.info("Wrote %s", args.json_out)
    else:
        print(text)
    return 0 if envelope.validation_passed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
