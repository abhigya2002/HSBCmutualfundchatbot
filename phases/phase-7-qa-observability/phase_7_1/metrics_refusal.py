"""Refusal accuracy metric (Phase 7.1)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from phase_7_1.allowlist import is_allowlisted
from phase_7_1.chat_client import ChatClient


def _load_probes(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("probes") or [])


def measure_refusal_accuracy(client: ChatClient, probes_path: Path) -> dict[str, Any]:
    probes = _load_probes(probes_path)
    results: list[dict[str, Any]] = []
    correct = 0

    for probe in probes:
        probe_id = str(probe.get("id") or "")
        query = str(probe.get("query") or "")
        expected = [str(x) for x in (probe.get("expected_outcomes") or ["refusal"])]

        call = client.chat(query)
        row: dict[str, Any] = {
            "probe_id": probe_id,
            "query": query,
            "expected_outcomes": expected,
            "latency_ms": call.latency_ms,
            "http_status": call.status_code,
            "error": call.error,
        }

        if not call.ok or call.envelope is None:
            row["correct"] = False
            row["reason"] = call.error or f"http_{call.status_code}"
            results.append(row)
            continue

        env = call.envelope
        outcome = str(env.get("outcome_type") or "")
        assistant = env.get("assistant") or {}
        citation = str(assistant.get("citation_url") or "")
        citation_ok = is_allowlisted(citation) if citation else False

        outcome_ok = outcome in expected
        correct_row = outcome_ok and citation_ok
        if correct_row:
            correct += 1

        row.update(
            {
                "correct": correct_row,
                "outcome_type": outcome,
                "citation_url": citation,
                "citation_allowlisted": citation_ok,
                "validation_passed": bool(env.get("validation_passed")),
                "reason": None if correct_row else f"outcome={outcome}, citation_ok={citation_ok}",
            }
        )
        results.append(row)

    total = len(probes)
    rate = round(correct / total, 4) if total else 0.0
    latencies = [r["latency_ms"] for r in results if r.get("latency_ms")]

    return {
        "metric": "refusal_accuracy",
        "description": "Share of advisory/comparison/projection probes that return expected refusal outcome with allowlisted citation",
        "total_probes": total,
        "correct": correct,
        "incorrect": total - correct,
        "accuracy_rate": rate,
        "accuracy_rate_pct": f"{int(round(rate * 100))}%",
        "avg_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0.0,
        "probes": results,
    }
