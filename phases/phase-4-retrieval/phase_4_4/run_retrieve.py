"""
Phase 4.4 — Hybrid retrieval CLI.

Run from ``phases/phase-4-retrieval``::

    python -m phase_4_4.run_retrieve --query "expense ratio HSBC Gilt Fund"
    python -m phase_4_4.run_retrieve --benchmark
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
from phase_4_2.classifier import RuleBasedIntentClassifier
from phase_4_2.config_load import load_intent_rules
from phase_4_3.resolver import SchemeResolver
from phase_4_4 import PHASE_4_4_VERSION
from phase_4_4.evaluate import run_hybrid_benchmark
from phase_4_4.hybrid_retriever import HybridRetriever

log = logging.getLogger("phase4_retrieval.phase_4_4.retrieve")


def _benchmark_path(config: dict) -> Path:
    rel = Path(str((config.get("handoff_files") or {}).get("retrieval_benchmark") or ""))
    root = phase4_retrieval_root()
    return rel if rel.is_absolute() else (root / rel).resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 4.4 hybrid retrieval.")
    parser.add_argument("--query", "-q", type=str, default="")
    parser.add_argument("--benchmark", action="store_true")
    parser.add_argument("--scheme", type=str, default="", help="Force scheme filter slug.")
    parser.add_argument("--skip-intent", action="store_true", help="Do not run Phase 4.2 gate.")
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--k", type=int, default=5, help="Benchmark recall@k.")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    setup_logging(config)
    paths = RetrievalArtifactPaths.from_config(config)
    paths.ensure_dirs()

    retriever = HybridRetriever()

    if args.benchmark:
        bench_path = _benchmark_path(config)
        if not bench_path.is_file():
            log.error("Benchmark not found: %s", bench_path)
            return 1
        report = run_hybrid_benchmark(retriever, bench_path, k=args.k)
        report["phase"] = "4.4"
        report["phase_4_4_version"] = PHASE_4_4_VERSION
        report["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
        report["benchmark_path"] = str(bench_path)
        out = args.json_out or (paths.eval / "phase4_4_hybrid_benchmark_report.json")
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        log.info(
            "Recall@%s = %.1f%% (%s/%s) %s",
            report["k"],
            report["recall_at_k"] * 100,
            report["hit_count"],
            report["query_count"],
            "PASSED" if report["passed"] else "FAILED",
        )
        for row in report["per_query"]:
            if not row["hit"]:
                log.warning("MISS %s: %s", row["benchmark_id"], row["query"][:60])
        return 0 if report["passed"] else 1

    if not args.query.strip():
        parser.error("Provide --query or --benchmark")
        return 2

    if not args.skip_intent:
        intent = RuleBasedIntentClassifier(load_intent_rules()).classify(args.query)
        if intent.skip_retrieval:
            payload = {
                "skipped": True,
                "reason": "intent_gate",
                "intent": intent.to_dict(),
            }
            print(json.dumps(payload, indent=2))
            return 0

    from phase_4_3.contracts import SchemeResolution, SchemeStatus

    if args.scheme.strip():
        scheme = args.scheme.strip()
        resolution = SchemeResolution(
            scheme=scheme,
            source_url="",
            confidence=1.0,
            status=SchemeStatus.RESOLVED.value,
        )
    else:
        resolution = SchemeResolver().resolve(args.query)

    result = retriever.retrieve(args.query, scheme_resolution=resolution)
    payload = result.to_dict()
    payload["scheme_resolution"] = resolution.to_dict()

    text = json.dumps(payload, indent=2)
    if args.json_out:
        args.json_out.write_text(text, encoding="utf-8")
        log.info("Wrote %s", args.json_out)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
