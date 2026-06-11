"""
Phase 4.6 — End-to-end retrieval service CLI.

Run from ``phases/phase-4-retrieval``::

    python -m phase_4_6.run_service --query "expense ratio HSBC Gilt Fund"
    python -m phase_4_6.run_service --eval-full
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from phase_4_1.config_load import load_config, phase4_retrieval_root
from phase_4_1.logging_setup import setup_logging
from phase_4_1.paths import RetrievalArtifactPaths
from phase_4_6 import PHASE_4_6_VERSION
from phase_4_6.contracts import RetrievalRequest
from phase_4_6.evaluate import run_full_evaluation
from phase_4_6.handoff import build_phase5_handoff, default_handoff_path, write_phase5_handoff
from phase_4_6.service import RetrievalService

log = logging.getLogger("phase4_retrieval.phase_4_6.service")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 4.6 end-to-end retrieval service.")
    parser.add_argument("--query", "-q", type=str, default="")
    parser.add_argument("--session-id", type=str, default="")
    parser.add_argument("--eval-full", action="store_true", help="Run factual + adversarial evaluation.")
    parser.add_argument("--write-handoff", action="store_true", help="Write Phase 5 handoff JSON.")
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    setup_logging(config)
    paths = RetrievalArtifactPaths.from_config(config)
    paths.ensure_dirs()

    service = RetrievalService(config=config)

    if args.eval_full:
        svc_cfg = config.get("service") or {}
        report = run_full_evaluation(service, thresholds=svc_cfg)
        report["phase"] = "4.6"
        report["phase_4_6_version"] = PHASE_4_6_VERSION
        report["generated_at_utc"] = datetime.now(timezone.utc).isoformat()

        out = args.json_out or (paths.eval / "phase4_6_full_evaluation_report.json")
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        log.info(
            "Eval %s — citation=%.1f%% adversarial=%.1f%% allowlist_clean=%s",
            "PASSED" if report["passed"] else "FAILED",
            (report.get("factual") or {}).get("citation_accuracy", 0) * 100,
            (report.get("adversarial") or {}).get("pass_rate", 0) * 100,
            report.get("allowlist_clean"),
        )

        if args.write_handoff or svc_cfg.get("write_handoff_on_eval", True):
            idx_ver = ""
            emb_id = ""
            try:
                idx_ver = service.hybrid_retriever.ctx.handoff.index_version
                emb_id = service.hybrid_retriever.ctx.handoff.embedding_model_id
            except Exception:
                pass
            handoff = build_phase5_handoff(
                index_version=idx_ver,
                embedding_model_id=emb_id,
                eval_summary={
                    "passed": report["passed"],
                    "citation_accuracy": (report.get("factual") or {}).get("citation_accuracy"),
                    "adversarial_pass_rate": (report.get("adversarial") or {}).get("pass_rate"),
                },
            )
            handoff_path = default_handoff_path()
            write_phase5_handoff(handoff_path, handoff)
            log.info("Wrote Phase 5 handoff %s", handoff_path)

        return 0 if report["passed"] else 1

    if not args.query.strip():
        parser.error("Provide --query or --eval-full")
        return 2

    outcome = service.retrieve(RetrievalRequest(query=args.query, session_id=args.session_id))
    payload = outcome.to_dict()
    text = json.dumps(payload, indent=2)
    if args.json_out:
        args.json_out.write_text(text, encoding="utf-8")
        log.info("Wrote %s", args.json_out)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
