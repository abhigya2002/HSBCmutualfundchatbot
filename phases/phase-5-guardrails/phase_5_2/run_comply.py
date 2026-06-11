"""
Phase 5.2 — Pre-generation compliance CLI.

Run from ``phases/phase-5-guardrails``::

    python -m phase_5_2.run_comply --eval-benchmark
    python -m phase_5_2.run_comply --query "Should I buy HSBC Gilt Fund?"
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase_5_1.config_load import load_config, phase5_guardrails_root
from phase_5_1.logging_setup import setup_logging
from phase_5_1.paths import GuardrailsArtifactPaths
from phase_5_2 import PHASE_5_2_VERSION
from phase_5_2.engine import PreGenerationComplianceEngine, ensure_handoff_ready
from phase_5_2.outcome_adapter import normalize_outcome
from phase_5_2.phase4_bridge import retrieve_outcome

log = logging.getLogger("phase5_guardrails.phase_5_2.comply")


def _benchmark_path() -> Path:
    return phase5_guardrails_root() / "benchmarks" / "compliance_benchmark.json"


def _load_benchmark(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("cases") or [])


def run_benchmark(engine: PreGenerationComplianceEngine, path: Path) -> dict[str, Any]:
    cases = _load_benchmark(path)
    results: list[dict[str, Any]] = []
    passed = 0
    for case in cases:
        outcome = case.get("outcome") or {}
        normalized = normalize_outcome(outcome)
        decision = engine.evaluate_normalized(normalized, original_query=str(case.get("query") or normalized.query))
        ok = (
            decision.decision == case.get("expected_decision")
            and decision.composer_route == case.get("expected_route")
        )
        if case.get("expected_performance_limited") is not None:
            ok = ok and decision.performance_limited == bool(case["expected_performance_limited"])
        if case.get("expect_reason_prefix"):
            ok = ok and any(r.startswith(str(case["expect_reason_prefix"])) for r in decision.reasons)
        if ok:
            passed += 1
        results.append(
            {
                "id": case.get("id"),
                "passed": ok,
                "expected_decision": case.get("expected_decision"),
                "actual_decision": decision.decision,
                "expected_route": case.get("expected_route"),
                "actual_route": decision.composer_route,
                "reasons": decision.reasons,
            },
        )
    total = len(cases)
    return {
        "phase": "5.2",
        "phase_5_2_version": PHASE_5_2_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "benchmark": str(path),
        "passed": passed == total and total > 0,
        "pass_rate": (passed / total) if total else 0.0,
        "cases_passed": passed,
        "cases_total": total,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 5.2 pre-generation compliance engine.")
    parser.add_argument("--query", "-q", type=str, default="", help="Run Phase 4 retrieve + compliance.")
    parser.add_argument("--eval-benchmark", action="store_true", help="Run compliance_benchmark.json.")
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    setup_logging(config)
    paths = GuardrailsArtifactPaths.from_config(config)
    paths.ensure_dirs()

    try:
        ensure_handoff_ready(config)
    except RuntimeError as exc:
        log.error("%s", exc)
        return 1

    engine = PreGenerationComplianceEngine(config=config)

    if args.eval_benchmark:
        bench = _benchmark_path()
        if not bench.is_file():
            log.error("Benchmark missing: %s", bench)
            return 1
        report = run_benchmark(engine, bench)
        out = args.json_out or (paths.eval / "phase5_2_compliance_report.json")
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
    decision = engine.evaluate(outcome)
    payload = {
        "query": args.query.strip(),
        "outcome_type": outcome.outcome_type,
        "compliance": decision.to_dict(),
    }
    text = json.dumps(payload, indent=2)
    if args.json_out:
        args.json_out.write_text(text, encoding="utf-8")
        log.info("Wrote %s", args.json_out)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
