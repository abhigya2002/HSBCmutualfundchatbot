"""Retrieval hit quality metric (Phase 7.1)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from phase_7_1.allowlist import is_allowlisted, slug_from_url
from phase_7_1.chat_client import ChatClient


def _load_probes(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("probes") or [])


def measure_retrieval_hit_quality(client: ChatClient, probes_path: Path) -> dict[str, Any]:
    probes = _load_probes(probes_path)
    results: list[dict[str, Any]] = []
    hits = 0

    for probe in probes:
        probe_id = str(probe.get("id") or "")
        query = str(probe.get("query") or "")
        expected_slug = str(probe.get("expected_scheme_slug") or "")
        expected_facet = str(probe.get("expected_facet") or "")

        call = client.chat(query)
        row: dict[str, Any] = {
            "probe_id": probe_id,
            "query": query,
            "expected_scheme_slug": expected_slug,
            "expected_facet": expected_facet,
            "latency_ms": call.latency_ms,
            "http_status": call.status_code,
            "error": call.error,
        }

        if not call.ok or call.envelope is None:
            row["hit"] = False
            row["reason"] = call.error or f"http_{call.status_code}"
            results.append(row)
            continue

        env = call.envelope
        assistant = env.get("assistant") or {}
        audit = env.get("audit") or {}
        outcome = str(env.get("outcome_type") or "")
        citation = str(assistant.get("citation_url") or "")
        citation_slug = slug_from_url(citation)
        evidence_id = str(assistant.get("evidence_chunk_id") or audit.get("evidence_chunk_id") or "")
        hybrid_skipped = bool(audit.get("hybrid_skipped"))

        scheme_match = citation_slug == expected_slug
        factual = outcome == "factual"
        has_evidence = bool(evidence_id)
        allowlisted = is_allowlisted(citation)

        hit = factual and scheme_match and allowlisted and has_evidence and not hybrid_skipped
        if hit:
            hits += 1

        row.update(
            {
                "hit": hit,
                "outcome_type": outcome,
                "citation_slug": citation_slug,
                "evidence_chunk_id": evidence_id,
                "hybrid_skipped": hybrid_skipped,
                "validation_passed": bool(env.get("validation_passed")),
                "latency_ms": call.latency_ms,
                "reason": None
                if hit
                else (
                    f"outcome={outcome}, scheme_match={scheme_match}, "
                    f"evidence={has_evidence}, hybrid_skipped={hybrid_skipped}"
                ),
            }
        )
        results.append(row)

    total = len(probes)
    rate = round(hits / total, 4) if total else 0.0
    latencies = [r["latency_ms"] for r in results if r.get("latency_ms")]
    avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else 0.0

    return {
        "metric": "retrieval_hit_quality",
        "description": "Share of labeled factual probes with correct scheme citation and evidence chunk",
        "total_probes": total,
        "hits": hits,
        "misses": total - hits,
        "hit_rate": rate,
        "hit_rate_pct": f"{int(round(rate * 100))}%",
        "avg_latency_ms": avg_latency,
        "probes": results,
    }
