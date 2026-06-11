"""Offline evaluation for Phase 4.6 retrieval service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from phase_4_1.config_load import phase4_retrieval_root
from phase_4_4.allowlist_filter import is_allowlisted_source
from phase_4_6.contracts import RetrievalRequest
from phase_4_6.service import RetrievalService


def _normalize_url(url: str) -> str:
    u = url.strip().rstrip("/").lower()
    if u.startswith("https://www."):
        u = "https://" + u[12:]
    return u


def _citation_from_outcome(outcome) -> str:
    if outcome.outcome_type == "refusal" and outcome.refusal:
        return outcome.refusal.citation_url
    if outcome.retrieval:
        return outcome.retrieval.citation_url
    return ""


def evaluate_factual_benchmark(
    service: RetrievalService,
    bench_path: Path,
    *,
    k: int = 5,
) -> dict[str, Any]:
    data = json.loads(bench_path.read_text(encoding="utf-8"))
    rows = data.get("queries") or []
    results = []
    citation_hits = 0
    scheme_hits = 0
    allowlist_violations = 0

    for row in rows:
        q = str(row.get("query") or "")
        expected_url = str(row.get("expected_source_url") or "")
        expected_scheme = str(row.get("scheme") or "")
        outcome = service.retrieve(RetrievalRequest(query=q))
        citation = _citation_from_outcome(outcome)
        if citation and not is_allowlisted_source(citation):
            allowlist_violations += 1

        url_ok = _normalize_url(citation) == _normalize_url(expected_url)
        scheme_ok = False
        status = outcome.retrieval.status if outcome.retrieval else None
        if outcome.retrieval and outcome.retrieval.status == "found":
            scheme_ok = outcome.retrieval.scheme == expected_scheme
            if url_ok:
                citation_hits += 1
            if scheme_ok:
                scheme_hits += 1

        results.append(
            {
                "id": row.get("id"),
                "query": q,
                "outcome_type": outcome.outcome_type,
                "status": status,
                "citation_url": citation,
                "expected_source_url": expected_url,
                "citation_match": url_ok,
                "scheme_match": scheme_ok,
                "hybrid_skipped": outcome.hybrid_skipped,
            },
        )

    total = len(results)
    return {
        "benchmark": "factual_retrieval",
        "path": str(bench_path),
        "query_count": total,
        "citation_accuracy": round(citation_hits / total, 4) if total else 0.0,
        "scheme_match_rate": round(scheme_hits / total, 4) if total else 0.0,
        "allowlist_violations": allowlist_violations,
        "k": k,
        "results": results,
    }


def evaluate_adversarial_benchmark(
    service: RetrievalService,
    bench_path: Path,
) -> dict[str, Any]:
    data = json.loads(bench_path.read_text(encoding="utf-8"))
    cases = data.get("cases") or []
    results = []
    passed = 0
    allowlist_violations = 0

    for case in cases:
        q = str(case.get("query") or "")
        expected_outcome = str(case.get("expected_outcome") or "")
        outcome = service.retrieve(RetrievalRequest(query=q))
        citation = _citation_from_outcome(outcome)
        if citation and not is_allowlisted_source(citation):
            allowlist_violations += 1

        ok = outcome.outcome_type == expected_outcome
        if expected_outcome == "refusal":
            ok = ok and outcome.hybrid_skipped
            expected_type = str(case.get("expected_refusal_type") or "")
            if expected_type and outcome.refusal:
                ok = ok and outcome.refusal.refusal_type == expected_type
        else:
            if case.get("expected_performance_limited"):
                ok = ok and outcome.performance_limited
            expected_scheme = str(case.get("expected_scheme") or "")
            if expected_scheme and outcome.retrieval:
                ok = ok and (
                    outcome.retrieval.scheme == expected_scheme
                    or outcome.scheme_resolution.scheme == expected_scheme
                )
            expected_url = str(case.get("expected_citation_url") or "")
            if expected_url:
                ok = ok and _normalize_url(citation) == _normalize_url(expected_url)
            if case.get("allow_not_found") and outcome.retrieval:
                ok = ok and outcome.retrieval.status in ("found", "not_found_in_sources")

        if ok:
            passed += 1
        results.append(
            {
                "id": case.get("id"),
                "edge_case": case.get("edge_case"),
                "query": q,
                "expected_outcome": expected_outcome,
                "got_outcome": outcome.outcome_type,
                "hybrid_skipped": outcome.hybrid_skipped,
                "refusal_type": outcome.refusal.refusal_type if outcome.refusal else None,
                "citation_url": citation,
                "performance_limited": outcome.performance_limited,
                "passed": ok,
            },
        )

    total = len(cases)
    return {
        "benchmark": "adversarial",
        "path": str(bench_path),
        "query_count": total,
        "passed": passed,
        "pass_rate": round(passed / total, 4) if total else 0.0,
        "allowlist_violations": allowlist_violations,
        "refusal_hybrid_skipped_rate": round(
            sum(1 for r in results if r["expected_outcome"] == "refusal" and r["hybrid_skipped"])
            / max(1, sum(1 for c in cases if c.get("expected_outcome") == "refusal")),
            4,
        ),
        "results": results,
    }


def run_full_evaluation(
    service: RetrievalService,
    *,
    factual_path: Path | None = None,
    adversarial_path: Path | None = None,
    thresholds: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = phase4_retrieval_root()
    factual = factual_path or (
        root / "../phase-3-indexing/benchmarks/retrieval_benchmark.json"
    ).resolve()
    adversarial = adversarial_path or (root / "benchmarks/adversarial_benchmark.json").resolve()
    thr = thresholds or {}

    factual_report = evaluate_factual_benchmark(service, factual) if factual.is_file() else {}
    adv_report = evaluate_adversarial_benchmark(service, adversarial) if adversarial.is_file() else {}

    citation_thr = float(thr.get("citation_accuracy_threshold") or 0.9)
    adversarial_thr = float(thr.get("adversarial_pass_rate_threshold") or 0.9)

    citation_ok = factual_report.get("citation_accuracy", 0) >= citation_thr
    adversarial_ok = adv_report.get("pass_rate", 0) >= adversarial_thr
    allowlist_ok = (
        factual_report.get("allowlist_violations", 0) == 0
        and adv_report.get("allowlist_violations", 0) == 0
    )

    return {
        "passed": citation_ok and adversarial_ok and allowlist_ok,
        "thresholds": {
            "citation_accuracy": citation_thr,
            "adversarial_pass_rate": adversarial_thr,
        },
        "factual": factual_report,
        "adversarial": adv_report,
        "allowlist_clean": allowlist_ok,
    }
