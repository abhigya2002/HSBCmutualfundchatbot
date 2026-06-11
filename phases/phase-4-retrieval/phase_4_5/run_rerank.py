"""
Phase 4.5 — Re-rank hybrid candidates and select citation.

Run from ``phases/phase-4-retrieval``::

    python -m phase_4_5.run_rerank --query "expense ratio HSBC Gilt Fund"
    python -m phase_4_5.run_rerank --benchmark
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
from phase_4_4.hybrid_retriever import HybridRetriever
from phase_4_5 import PHASE_4_5_VERSION
from phase_4_5.evaluate import run_citation_benchmark
from phase_4_5.reranker import Reranker

log = logging.getLogger("phase4_retrieval.phase_4_5.rerank")


def _benchmark_path(config: dict) -> Path:
    rel = Path(str((config.get("handoff_files") or {}).get("retrieval_benchmark") or ""))
    root = phase4_retrieval_root()
    return rel if rel.is_absolute() else (root / rel).resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 4.5 re-rank and citation selection.")
    parser.add_argument("--query", "-q", type=str, default="")
    parser.add_argument("--benchmark", action="store_true")
    parser.add_argument("--skip-intent", action="store_true")
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    setup_logging(config)
    paths = RetrievalArtifactPaths.from_config(config)
    paths.ensure_dirs()

    retriever = HybridRetriever()
    reranker = Reranker()

    if args.benchmark:
        bench_path = _benchmark_path(config)
        if not bench_path.is_file():
            log.error("Benchmark not found: %s", bench_path)
            return 1
        report = run_citation_benchmark(retriever, reranker, bench_path)
        report["phase"] = "4.5"
        report["phase_4_5_version"] = PHASE_4_5_VERSION
        report["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
        report["benchmark_path"] = str(bench_path)
        out = args.json_out or (paths.eval / "phase4_5_citation_benchmark_report.json")
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        log.info(
            "Citation accuracy = %.1f%% (%s/%s) %s",
            report["citation_accuracy"] * 100,
            report["hit_count"],
            report["query_count"],
            "PASSED" if report["passed"] else "FAILED",
        )
        for row in report["results"]:
            if not row["passed"]:
                log.warning("FAIL %s: %s", row["id"], row["query"][:60])
        return 0 if report["passed"] else 1

    if not args.query.strip():
        parser.error("Provide --query or --benchmark")
        return 2

    intent_clf = RuleBasedIntentClassifier(load_intent_rules())
    intent = intent_clf.classify(args.query)
    if not args.skip_intent and intent.skip_retrieval:
        print(json.dumps({"skipped": True, "intent": intent.to_dict()}, indent=2))
        return 0

    resolution = SchemeResolver().resolve(args.query)
    hybrid = retriever.retrieve(args.query, scheme_resolution=resolution)
    response = reranker.rerank(hybrid, intent=intent, scheme_resolution=resolution)

    payload = response.to_dict()
    payload["intent"] = intent.to_dict()
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
