"""
Phase 5.5 — Post-generation validator CLI.

Run from ``phases/phase-5-guardrails``::

    python -m phase_5_5.run_validate --eval-benchmark
    python -m phase_5_5.run_validate --query "expense ratio HSBC Gilt Fund Direct Growth"
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from phase_5_1.config_load import load_config, phase5_guardrails_root
from phase_5_1.logging_setup import setup_logging
from phase_5_1.paths import GuardrailsArtifactPaths
from phase_5_2.engine import PreGenerationComplianceEngine
from phase_5_2.phase4_bridge import retrieve_outcome
from phase_5_3.composer import RefusalComposer
from phase_5_4.composer import FactualComposer
from phase_5_5 import PHASE_5_5_VERSION
from phase_5_5.validator import PostGenerationValidator

log = logging.getLogger("phase5_guardrails.phase_5_5.run")


def _benchmark_path() -> Path:
    return phase5_guardrails_root() / "benchmarks" / "validation_benchmark.json"


def _load_benchmark(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("cases") or [])


def _evaluate_case(validator: PostGenerationValidator, case: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    draft = case.get("draft") or {}
    if case.get("repair"):
        result = validator.validate_and_repair(draft)
    else:
        result = validator.validate(draft)

    ok = result.passed == bool(case.get("expect_pass", True))
    if case.get("expect_repaired") is not None and result.repaired != bool(case["expect_repaired"]):
        ok = False
    if case.get("expect_answer_type") and result.answer_type != case["expect_answer_type"]:
        ok = False

    citation_url = str(result.draft.get("citation_url") or "")
    if case.get("expect_citation_host"):
        host = urlparse(citation_url).netloc
        if host != case["expect_citation_host"]:
            ok = False

    footer_line = str(result.draft.get("footer_line") or "")
    for token in case.get("expect_footer_contains") or []:
        if token not in footer_line and token not in str(result.draft.get("footer_date") or ""):
            ok = False

    detail = {
        "id": case.get("id"),
        "passed": ok,
        "validation_passed": result.passed,
        "repaired": result.repaired,
        "violations": [v.to_dict() for v in result.violations],
        "repair_actions": result.repair_actions,
        "answer_type": result.answer_type,
    }
    return ok, detail


def run_benchmark(validator: PostGenerationValidator, path: Path) -> dict[str, Any]:
    cases = _load_benchmark(path)
    results: list[dict[str, Any]] = []
    passed = 0
    for case in cases:
        ok, detail = _evaluate_case(validator, case)
        if ok:
            passed += 1
        results.append(detail)
    total = len(cases)
    return {
        "phase": "5.5",
        "phase_5_5_version": PHASE_5_5_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "benchmark": str(path),
        "passed": passed == total and total > 0,
        "pass_rate": (passed / total) if total else 0.0,
        "cases_passed": passed,
        "cases_total": total,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 5.5 post-generation validator.")
    parser.add_argument("--query", "-q", type=str, default="", help="Retrieve, compose, validate end-to-end.")
    parser.add_argument("--eval-benchmark", action="store_true")
    parser.add_argument("--repair", action="store_true", help="With --query, run validate_and_repair.")
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    setup_logging(config)
    paths = GuardrailsArtifactPaths.from_config(config)
    paths.ensure_dirs()

    validator = PostGenerationValidator(config=config)

    if args.eval_benchmark:
        bench = _benchmark_path()
        if not bench.is_file():
            log.error("Benchmark missing: %s", bench)
            return 1
        report = run_benchmark(validator, bench)
        out = args.json_out or (paths.eval / "phase5_5_validation_report.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        log.info(
            "Benchmark %s — %d/%d passed",
            "PASSED" if report["passed"] else "FAILED",
            report["cases_passed"],
            report["cases_total"],
        )
        return 0 if report["passed"] else 1

    if not args.query.strip():
        parser.error("Provide --query or --eval-benchmark")
        return 2

    outcome = retrieve_outcome(args.query.strip())
    compliance = PreGenerationComplianceEngine(config=config).evaluate(outcome)

    if compliance.decision == "refuse" and outcome.refusal is not None:
        draft = RefusalComposer(config=config).compose_from_compliance(compliance, outcome.refusal)
    elif compliance.decision == "allow_compose" and outcome.retrieval is not None:
        draft = FactualComposer(config=config).compose_from_compliance(compliance, outcome.retrieval)
    else:
        payload = {
            "query": args.query.strip(),
            "compliance_decision": compliance.decision,
            "message": "No composable draft for validation.",
        }
        print(json.dumps(payload, indent=2))
        return 0

    result = validator.validate_and_repair(draft) if args.repair else validator.validate(draft)
    assistant = validator.to_assistant_response(result)
    payload = {
        "query": args.query.strip(),
        "compliance": compliance.to_dict(),
        "validation": result.to_dict(),
        "assistant_response": assistant.to_dict(),
    }
    text = json.dumps(payload, indent=2)
    if args.json_out:
        args.json_out.write_text(text, encoding="utf-8")
        log.info("Wrote %s", args.json_out)
    else:
        print(text)
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
