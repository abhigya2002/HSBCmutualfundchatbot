"""
Phase 5.4 — Factual composer CLI.

Run from ``phases/phase-5-guardrails``::

    python -m phase_5_4.run_compose --eval-benchmark
    python -m phase_5_4.run_compose --query "expense ratio HSBC Gilt Fund Direct Growth"
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
from phase_5_1.registry_bridge import is_allowlisted_url
from phase_5_2.engine import PreGenerationComplianceEngine
from phase_5_2.phase4_bridge import retrieve_outcome
from phase_5_3.citation import count_markdown_links
from phase_5_3.composer import sentence_count
from phase_5_4 import PHASE_5_4_VERSION
from phase_5_4.composer import FactualComposer
from phase_5_4.retrieval_adapter import normalize_retrieval

log = logging.getLogger("phase5_guardrails.phase_5_4.run")


def _benchmark_path() -> Path:
    return phase5_guardrails_root() / "benchmarks" / "factual_composer_benchmark.json"


def _load_benchmark(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("cases") or [])


def _validate_answer(answer_dict: dict[str, Any], case: dict[str, Any]) -> tuple[bool, list[str]]:
    issues: list[str] = []
    body = str(answer_dict.get("body_text") or "")
    citation_url = str(answer_dict.get("citation_url") or "")
    citation_md = str(answer_dict.get("citation_markdown") or "")
    footer = str(answer_dict.get("footer_line") or "")
    disclaimer = str(answer_dict.get("disclaimer_line") or "")

    if not body.strip():
        issues.append("empty_body")
    if sentence_count(body) > 3:
        issues.append("sentence_budget_exceeded")
    if not is_allowlisted_url(citation_url):
        issues.append("citation_not_allowlisted")
    if count_markdown_links(citation_md) != 1:
        issues.append("citation_link_count")
    if count_markdown_links(body) > 0:
        issues.append("body_contains_link")
    if "Last updated from sources:" not in footer:
        issues.append("missing_footer")
    if "Facts-only" not in disclaimer:
        issues.append("missing_disclaimer")
    if not answer_dict.get("evidence_chunk_id"):
        issues.append("missing_chunk_id")

    expected_url = case.get("expected_citation_url")
    if expected_url and citation_url != expected_url:
        issues.append("citation_url_mismatch")

    for token in case.get("expect_body_contains") or []:
        if token not in body:
            issues.append(f"missing_body_token:{token}")

    for token in case.get("expect_footer_contains") or []:
        if token not in footer and token not in str(answer_dict.get("footer_date") or ""):
            issues.append(f"missing_footer_token:{token}")

    flags = list(answer_dict.get("number_grounding_flags") or [])
    if flags and case.get("require_clean_numbers"):
        issues.append("number_grounding_flags")

    return len(issues) == 0, issues


def run_benchmark(composer: FactualComposer, path: Path) -> dict[str, Any]:
    cases = _load_benchmark(path)
    results: list[dict[str, Any]] = []
    passed = 0
    for case in cases:
        retrieval = normalize_retrieval(case.get("retrieval") or {})
        answer = composer.compose_normalized(
            retrieval,
            performance_limited=bool(case.get("performance_limited")),
        )
        answer_dict = answer.to_dict()
        ok, issues = _validate_answer(answer_dict, case)
        if ok:
            passed += 1
        results.append(
            {
                "id": case.get("id"),
                "passed": ok,
                "issues": issues,
                "body_text": answer.body_text,
                "citation_url": answer.citation_url,
            },
        )
    total = len(cases)
    return {
        "phase": "5.4",
        "phase_5_4_version": PHASE_5_4_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "benchmark": str(path),
        "passed": passed == total and total > 0,
        "pass_rate": (passed / total) if total else 0.0,
        "cases_passed": passed,
        "cases_total": total,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 5.4 factual response composer.")
    parser.add_argument("--query", "-q", type=str, default="", help="Retrieve + compose factual answer.")
    parser.add_argument("--eval-benchmark", action="store_true")
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    setup_logging(config)
    paths = GuardrailsArtifactPaths.from_config(config)
    paths.ensure_dirs()

    composer = FactualComposer(config=config)

    if args.eval_benchmark:
        bench = _benchmark_path()
        if not bench.is_file():
            log.error("Benchmark missing: %s", bench)
            return 1
        report = run_benchmark(composer, bench)
        out = args.json_out or (paths.eval / "phase5_4_factual_composer_report.json")
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
    if compliance.decision != "allow_compose" or outcome.retrieval is None:
        payload = {
            "query": args.query.strip(),
            "outcome_type": outcome.outcome_type,
            "compliance_decision": compliance.decision,
            "message": "Query did not produce a factual compose path.",
        }
        print(json.dumps(payload, indent=2))
        return 0

    answer = composer.compose_from_compliance(compliance, outcome.retrieval)
    payload = {
        "query": args.query.strip(),
        "compliance": compliance.to_dict(),
        "factual_answer": answer.to_dict(),
        "display_text": answer.display_text,
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
