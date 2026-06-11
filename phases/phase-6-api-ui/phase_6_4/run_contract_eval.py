"""
Phase 6.4 — Contract evaluation CLI.

Run from ``phases/phase-6-api-ui``::

    python -m phase_6_4.run_contract_eval
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from phase_6_1.config_load import load_config
from phase_6_1.logging_setup import setup_logging
from phase_6_1.paths import ApiUiArtifactPaths
from phase_6_4 import PHASE_6_4_VERSION
from phase_6_4.errors import assert_safe_error_payload, error_response
from phase_6_4.handoff_contract import load_handoff_contract, validate_envelope_against_handoff
from phase_6_4.http_policy import ERROR_STATUS_MAP, POLICY_OUTCOME_HTTP_STATUS
from phase_6_4.outcome_contract import REFUSAL_TYPES, validate_outcome_contract

log = logging.getLogger("phase6_api_ui.phase_6_4.eval")


def _sample_envelope(outcome_type: str) -> dict:
    base_assistant = {
        "answer_type": outcome_type,
        "body_text": "Sample body.",
        "citation_url": "https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth",
        "citation_markdown": "[HSBC Gilt Fund](https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth)",
        "footer_line": "Last updated from sources: date unavailable",
        "footer_date": "date unavailable",
        "disclaimer_line": "Facts-only. No investment advice.",
        "display_text": "Sample display.",
        "evidence_chunk_id": "chunk_1",
        "refusal_type": "",
        "validation_passed": True,
        "validation_repaired": False,
    }
    if outcome_type == "refusal":
        base_assistant["answer_type"] = "refusal"
        base_assistant["refusal_type"] = "advisory"
    if outcome_type == "abstention":
        base_assistant["answer_type"] = "abstention"
        base_assistant["body_text"] = "I could not find enough evidence in the allowlisted sources."
    return {
        "outcome_type": outcome_type,
        "query": "sample",
        "session_id": "",
        "retrieval_outcome_type": outcome_type,
        "compliance_decision": "allow_compose",
        "compliance_reasons": [],
        "validation_passed": True,
        "validation_repaired": False,
        "assistant": base_assistant,
        "display_text": base_assistant["display_text"],
        "audit": {},
    }


def run_eval(config_path: Path | None = None) -> dict:
    config = load_config(config_path)
    contract = load_handoff_contract(config)

    checks: list[dict] = []

    sample_err = error_response(code="unsupported_media_type", message="Content-Type must be application/json")
    try:
        assert_safe_error_payload(sample_err)
        checks.append({"id": "api_error_shape", "passed": True})
    except ValueError as exc:
        checks.append({"id": "api_error_shape", "passed": False, "detail": str(exc)})

    checks.append(
        {
            "id": "http_policy_map",
            "passed": ERROR_STATUS_MAP.get("unsupported_media_type") == 415
            and POLICY_OUTCOME_HTTP_STATUS == 200,
        },
    )

    handoff_ok = len(contract.issues) == 0
    checks.append(
        {
            "id": "handoff_loaded",
            "passed": handoff_ok,
            "issues": [{"code": i.code, "message": i.message} for i in contract.issues],
        },
    )

    for outcome in ("factual", "refusal", "abstention"):
        sample = _sample_envelope(outcome)
        env_issues = validate_envelope_against_handoff(sample, contract) if handoff_ok else []
        out_issues = validate_outcome_contract(sample)
        checks.append(
            {
                "id": f"contract_{outcome}",
                "passed": not env_issues and not out_issues,
                "envelope_issues": [{"code": i.code, "message": i.message} for i in env_issues],
                "outcome_issues": out_issues,
            },
        )

    checks.append(
        {
            "id": "refusal_types_documented",
            "passed": REFUSAL_TYPES.issuperset(
                {"advisory", "comparison", "mixed_intent", "out_of_scope", "disambiguate", "performance_info"},
            ),
            "refusal_types": sorted(REFUSAL_TYPES),
        },
    )

    passed = sum(1 for c in checks if c.get("passed"))
    total = len(checks)
    return {
        "phase": "6.4",
        "phase_6_4_version": PHASE_6_4_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "handoff_path": str(contract.handoff_path),
        "envelope_fields": sorted(contract.envelope_fields),
        "assistant_fields": sorted(contract.assistant_fields),
        "passed": passed == total and total > 0,
        "checks_passed": passed,
        "checks_total": total,
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 6.4 contract evaluation.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args(argv)

    setup_logging(load_config(args.config))
    report = run_eval(args.config)

    paths = ApiUiArtifactPaths.from_config(load_config(args.config))
    paths.ensure_dirs()
    out = args.json_out or (paths.eval / "phase6_4_contract_report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log.info(
        "Contract eval %s — %d/%d checks passed — wrote %s",
        "PASSED" if report["passed"] else "FAILED",
        report["checks_passed"],
        report["checks_total"],
        out,
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
