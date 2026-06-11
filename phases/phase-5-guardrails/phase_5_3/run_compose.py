"""
Phase 5.3 — Refusal composer CLI.

Run from ``phases/phase-5-guardrails``::

    python -m phase_5_3.run_compose --eval-benchmark
    python -m phase_5_3.run_compose --refusal-type advisory
    python -m phase_5_3.run_compose --query "Should I buy HSBC Gilt Fund?"
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
from phase_5_1.handoff import load_composer_defaults
from phase_5_1.logging_setup import setup_logging
from phase_5_1.paths import GuardrailsArtifactPaths
from phase_5_1.registry_bridge import is_allowlisted_url
from phase_5_2.engine import PreGenerationComplianceEngine
from phase_5_2.phase4_bridge import retrieve_outcome
from phase_5_3 import PHASE_5_3_VERSION, REFUSAL_TYPES
from phase_5_3.citation import count_markdown_links
from phase_5_3.composer import RefusalComposer
from phase_5_3.refusal_adapter import NormalizedRefusal

log = logging.getLogger("phase5_guardrails.phase_5_3.run")


def _benchmark_path() -> Path:
    return phase5_guardrails_root() / "benchmarks" / "refusal_composer_benchmark.json"


def _load_benchmark(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("cases") or [])


def _validate_answer(answer_dict: dict[str, Any], case: dict[str, Any]) -> tuple[bool, list[str]]:
    issues: list[str] = []
    body = str(answer_dict.get("body_text") or "")
    citation_url = str(answer_dict.get("citation_url") or "")
    citation_md = str(answer_dict.get("citation_markdown") or "")
    disclaimer = str(answer_dict.get("disclaimer_line") or "")

    if not body.strip():
        issues.append("empty_body")
    if not is_allowlisted_url(citation_url):
        issues.append("citation_not_allowlisted")
    if count_markdown_links(citation_md) != 1:
        issues.append("citation_link_count")
    if count_markdown_links(body) > 0:
        issues.append("body_contains_link")
    if "Facts-only" not in disclaimer:
        issues.append("missing_disclaimer")

    expected_type = case.get("refusal_type")
    if expected_type and answer_dict.get("refusal_type") != expected_type:
        issues.append("refusal_type_mismatch")

    expected_url = case.get("expected_citation_url")
    if expected_url and citation_url != expected_url:
        issues.append("citation_url_mismatch")

    return len(issues) == 0, issues


def run_benchmark(composer: RefusalComposer, path: Path) -> dict[str, Any]:
    cases = _load_benchmark(path)
    results: list[dict[str, Any]] = []
    passed = 0
    for case in cases:
        refusal = NormalizedRefusal(
            refusal_type=str(case.get("refusal_type") or ""),
            message_hint=str(case.get("message_hint") or "internal hint"),
            citation_url=str(case.get("citation_url") or ""),
        )
        answer = composer.compose_normalized(refusal)
        answer_dict = answer.to_dict()
        ok, issues = _validate_answer(answer_dict, case)
        if ok:
            passed += 1
        results.append(
            {
                "id": case.get("id"),
                "refusal_type": case.get("refusal_type"),
                "passed": ok,
                "issues": issues,
                "citation_url": answer.citation_url,
            },
        )
    total = len(cases)
    return {
        "phase": "5.3",
        "phase_5_3_version": PHASE_5_3_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "benchmark": str(path),
        "passed": passed == total and total > 0,
        "pass_rate": (passed / total) if total else 0.0,
        "cases_passed": passed,
        "cases_total": total,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 5.3 refusal response composer.")
    parser.add_argument("--query", "-q", type=str, default="", help="Retrieve + compose refusal if applicable.")
    parser.add_argument("--refusal-type", type=str, default="", choices=[*REFUSAL_TYPES])
    parser.add_argument("--citation-url", type=str, default="", help="Optional citation URL for --refusal-type.")
    parser.add_argument("--eval-benchmark", action="store_true")
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    setup_logging(config)
    paths = GuardrailsArtifactPaths.from_config(config)
    paths.ensure_dirs()

    composer = RefusalComposer(config=config)
    composer_defaults, _ = load_composer_defaults(config)

    if args.eval_benchmark:
        bench = _benchmark_path()
        if not bench.is_file():
            log.error("Benchmark missing: %s", bench)
            return 1
        report = run_benchmark(composer, bench)
        out = args.json_out or (paths.eval / "phase5_3_refusal_composer_report.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        log.info(
            "Benchmark %s — %d/%d passed",
            "PASSED" if report["passed"] else "FAILED",
            report["cases_passed"],
            report["cases_total"],
        )
        return 0 if report["passed"] else 1

    if args.refusal_type:
        refusal = NormalizedRefusal(
            refusal_type=args.refusal_type,
            message_hint="cli",
            citation_url=args.citation_url or (composer_defaults.default_citation_url if composer_defaults else ""),
        )
        answer = composer.compose_normalized(refusal)
        payload = answer.to_dict()
        text = json.dumps(payload, indent=2)
        if args.json_out:
            args.json_out.write_text(text, encoding="utf-8")
            log.info("Wrote %s", args.json_out)
        else:
            print(text)
        return 0

    if not args.query.strip():
        parser.error("Provide --query, --refusal-type, or --eval-benchmark")
        return 2

    outcome = retrieve_outcome(args.query.strip())
    compliance = PreGenerationComplianceEngine(config=config).evaluate(outcome)
    if compliance.decision != "refuse" or outcome.refusal is None:
        payload = {
            "query": args.query.strip(),
            "outcome_type": outcome.outcome_type,
            "compliance_decision": compliance.decision,
            "message": "Query did not produce a refusal path.",
        }
        print(json.dumps(payload, indent=2))
        return 0

    answer = composer.compose(outcome.refusal)
    payload = {
        "query": args.query.strip(),
        "compliance": compliance.to_dict(),
        "refusal_answer": answer.to_dict(),
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
