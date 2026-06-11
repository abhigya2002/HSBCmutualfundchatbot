"""
Phase 4.3 — Resolve scheme from user query.

Run from ``phases/phase-4-retrieval``::

    python -m phase_4_3.run_resolve --query "expense ratio HSBC Gilt Fund"
    python -m phase_4_3.run_resolve --benchmark
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
from phase_4_3 import PHASE_4_3_VERSION
from phase_4_3.audit_log import append_scheme_log_line, log_scheme_resolution
from phase_4_3.config_load import default_aliases_path, load_scheme_aliases
from phase_4_3.resolver import SchemeResolver

log = logging.getLogger("phase4_retrieval.phase_4_3.resolve")


def _benchmark_path(config: dict) -> Path:
    rel = Path(
        str(
            (config.get("handoff_files") or {}).get("scheme_benchmark")
            or "benchmarks/scheme_benchmark.json",
        ),
    )
    root = phase4_retrieval_root()
    return rel if rel.is_absolute() else (root / rel).resolve()


def run_benchmark(resolver: SchemeResolver, bench_path: Path) -> dict:
    data = json.loads(bench_path.read_text(encoding="utf-8"))
    cases = data.get("cases") or []
    results = []
    passed = 0
    for case in cases:
        q = str(case.get("query") or "")
        got = resolver.resolve(q)
        expected_status = str(case.get("expected_status") or "")
        expected_scheme = str(case.get("expected_scheme") or "")
        expected_url = str(case.get("expected_source_url") or "")

        ok = got.status == expected_status
        if expected_scheme:
            ok = ok and got.scheme == expected_scheme
        if expected_url:
            ok = ok and got.citation_url_candidate == expected_url

        if ok:
            passed += 1
        results.append(
            {
                "id": case.get("id"),
                "query": q,
                "expected_status": expected_status,
                "expected_scheme": expected_scheme,
                "got_status": got.status,
                "got_scheme": got.scheme,
                "got_url": got.citation_url_candidate,
                "confidence": got.confidence,
                "passed": ok,
            },
        )
    total = len(cases)
    return {
        "phase": "4.3",
        "phase_4_3_version": PHASE_4_3_VERSION,
        "benchmark_path": str(bench_path),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "passed": passed,
        "accuracy": round(passed / total, 4) if total else 0.0,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 4.3 scheme resolution.")
    parser.add_argument("--query", "-q", type=str, default="")
    parser.add_argument("--benchmark", action="store_true")
    parser.add_argument("--aliases", type=Path, default=None)
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--log-file", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    setup_logging(config)
    aliases = load_scheme_aliases(args.aliases)
    resolver = SchemeResolver(aliases_config=aliases)

    paths = RetrievalArtifactPaths.from_config(config)
    paths.ensure_dirs()

    if args.benchmark:
        bench_path = _benchmark_path(config)
        if not bench_path.is_file():
            log.error("Benchmark not found: %s", bench_path)
            return 1
        report = run_benchmark(resolver, bench_path)
        out = args.json_out or (paths.eval / "phase4_3_scheme_benchmark_report.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        log.info("Benchmark %s/%s passed (%.1f%%)", report["passed"], report["total"], report["accuracy"] * 100)
        for row in report["results"]:
            if not row["passed"]:
                log.warning(
                    "FAIL %s: expected %s/%s got %s/%s",
                    row["id"],
                    row["expected_status"],
                    row["expected_scheme"],
                    row["got_status"],
                    row["got_scheme"],
                )
        return 0 if report["passed"] == report["total"] else 1

    if not args.query.strip():
        parser.error("Provide --query or --benchmark")
        return 2

    result = resolver.resolve(args.query)
    log_scheme_resolution(result, query=args.query)
    if args.log_file:
        append_scheme_log_line(args.log_file, result, query=args.query)

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
