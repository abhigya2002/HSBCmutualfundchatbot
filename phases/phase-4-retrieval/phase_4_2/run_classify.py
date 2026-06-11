"""
Phase 4.2 — Classify query intent (CLI + benchmark eval).

Run from ``phases/phase-4-retrieval``::

    python -m phase_4_2.run_classify --query "expense ratio HSBC Gilt Fund"
    python -m phase_4_2.run_classify --benchmark
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
from phase_4_2 import PHASE_4_2_VERSION
from phase_4_2.audit_log import append_intent_log_line, log_intent_result
from phase_4_2.classifier import RuleBasedIntentClassifier
from phase_4_2.config_load import default_rules_path, load_intent_rules

log = logging.getLogger("phase4_retrieval.phase_4_2.classify")


def _benchmark_path(config: dict) -> Path:
    rel = Path(
        str(
            (config.get("handoff_files") or {}).get("intent_benchmark")
            or "benchmarks/intent_benchmark.json",
        ),
    )
    root = phase4_retrieval_root()
    return rel if rel.is_absolute() else (root / rel).resolve()


def run_benchmark(classifier: RuleBasedIntentClassifier, bench_path: Path) -> dict:
    data = json.loads(bench_path.read_text(encoding="utf-8"))
    cases = data.get("cases") or []
    results = []
    passed = 0
    for case in cases:
        q = str(case.get("query") or "")
        expected_intent = str(case.get("expected_intent") or "")
        expected_action = str(case.get("expected_action") or "")
        got = classifier.classify(q)
        ok = got.intent == expected_intent and got.action == expected_action
        if ok:
            passed += 1
        results.append(
            {
                "id": case.get("id"),
                "query": q,
                "expected_intent": expected_intent,
                "expected_action": expected_action,
                "got_intent": got.intent,
                "got_action": got.action,
                "policy_code": got.policy_code,
                "confidence": got.confidence,
                "passed": ok,
            },
        )
    total = len(cases)
    return {
        "phase": "4.2",
        "phase_4_2_version": PHASE_4_2_VERSION,
        "benchmark_path": str(bench_path),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "passed": passed,
        "accuracy": round(passed / total, 4) if total else 0.0,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 4.2 intent classification.")
    parser.add_argument("--query", "-q", type=str, default="", help="Single query to classify.")
    parser.add_argument("--benchmark", action="store_true", help="Run intent benchmark suite.")
    parser.add_argument("--rules", type=Path, default=None, help="Path to intent.rules.json")
    parser.add_argument("--json-out", type=Path, default=None, help="Write JSON result or report.")
    parser.add_argument("--log-file", type=Path, default=None, help="Append intent audit lines.")
    parser.add_argument("--config", type=Path, default=None, help="Retrieval config (for paths).")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    setup_logging(config)
    rules = load_intent_rules(args.rules)
    classifier = RuleBasedIntentClassifier(rules)

    paths = RetrievalArtifactPaths.from_config(config)
    paths.ensure_dirs()

    if args.benchmark:
        bench_path = _benchmark_path(config)
        if not bench_path.is_file():
            log.error("Benchmark not found: %s", bench_path)
            return 1
        report = run_benchmark(classifier, bench_path)
        out = args.json_out or (paths.eval / "phase4_2_intent_benchmark_report.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        log.info("Benchmark %s/%s passed (%.1f%%)", report["passed"], report["total"], report["accuracy"] * 100)
        for row in report["results"]:
            if not row["passed"]:
                log.warning("FAIL %s: expected %s/%s got %s/%s", row["id"], row["expected_intent"], row["expected_action"], row["got_intent"], row["got_action"])
        return 0 if report["passed"] == report["total"] else 1

    if not args.query.strip():
        parser.error("Provide --query or --benchmark")
        return 2

    result = classifier.classify(args.query)
    log_intent_result(result, query=args.query)
    if args.log_file:
        append_intent_log_line(args.log_file, result, query=args.query)

    payload = result.to_dict()
    text = json.dumps(payload, indent=2)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
        log.info("Wrote %s", args.json_out)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
