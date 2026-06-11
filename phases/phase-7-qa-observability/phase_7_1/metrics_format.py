"""Format compliance rate metric (Phase 7.1)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from phase_7_1.chat_client import ChatClient
from phase_7_1.format_checks import assess_format_compliance


def _load_queries(retrieval_path: Path, refusal_path: Path) -> list[dict[str, str]]:
    queries: list[dict[str, str]] = []
    for path, source in ((retrieval_path, "retrieval_probe"), (refusal_path, "refusal_probe")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for probe in data.get("probes") or []:
            queries.append(
                {
                    "probe_id": str(probe.get("id") or ""),
                    "query": str(probe.get("query") or ""),
                    "source": source,
                }
            )
    return queries


def measure_format_compliance_rate(
    client: ChatClient,
    *,
    retrieval_probes_path: Path,
    refusal_probes_path: Path,
) -> dict[str, Any]:
    queries = _load_queries(retrieval_probes_path, refusal_probes_path)
    results: list[dict[str, Any]] = []
    compliant_count = 0
    factual_total = 0
    factual_compliant = 0
    total_allowlist_violations = 0

    for item in queries:
        call = client.chat(item["query"])
        row: dict[str, Any] = {
            "probe_id": item["probe_id"],
            "query": item["query"],
            "source": item["source"],
            "latency_ms": call.latency_ms,
            "http_status": call.status_code,
            "error": call.error,
        }

        if not call.ok or call.envelope is None:
            row["compliant"] = False
            row["reason"] = call.error or f"http_{call.status_code}"
            results.append(row)
            continue

        assessment = assess_format_compliance(call.envelope)
        row.update(assessment)
        row["latency_ms"] = call.latency_ms
        row["validation_passed"] = bool(call.envelope.get("validation_passed"))

        if assessment["outcome_type"] == "factual":
            factual_total += 1
            if assessment["compliant"]:
                factual_compliant += 1

        if assessment["compliant"]:
            compliant_count += 1
        total_allowlist_violations += int(assessment.get("allowlist_violations") or 0)
        results.append(row)

    total = len(queries)
    overall_rate = round(compliant_count / total, 4) if total else 0.0
    factual_rate = round(factual_compliant / factual_total, 4) if factual_total else 0.0

    return {
        "metric": "format_compliance_rate",
        "description": "Share of responses meeting format rules (<=3 sentences, one allowlisted citation, footer, validation_passed)",
        "total_responses": total,
        "compliant_responses": compliant_count,
        "overall_compliance_rate": overall_rate,
        "overall_compliance_rate_pct": f"{int(round(overall_rate * 100))}%",
        "factual_responses": factual_total,
        "factual_compliant": factual_compliant,
        "factual_compliance_rate": factual_rate,
        "factual_compliance_rate_pct": f"{int(round(factual_rate * 100))}%",
        "allowlist_violations_total": total_allowlist_violations,
        "responses": results,
    }
