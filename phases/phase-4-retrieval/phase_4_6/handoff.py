"""Phase 5 handoff document generation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from phase_4_1.config_load import phase4_retrieval_root
from phase_4_6 import PHASE_4_6_VERSION
from phase_4_6.contracts import RetrieveOutcome


def build_phase5_handoff(
    *,
    index_version: str,
    embedding_model_id: str,
    eval_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "phase": "4.6",
        "phase_4_6_version": PHASE_4_6_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "version_pins": {
            "index_version": index_version,
            "embedding_model_id": embedding_model_id,
        },
        "api_surface": {
            "retrieve": "RetrievalService.retrieve(RetrievalRequest) -> RetrieveOutcome",
            "outcome_types": ["retrieval", "refusal"],
        },
        "evidence_fields_for_phase5": {
            "found": [
                "chunk_id",
                "chunk_text",
                "citation_url",
                "section_title",
                "effective_date",
                "scheme",
                "scores.final_score",
                "ranked_candidates",
            ],
            "not_found_in_sources": [
                "citation_url",
                "not_found_reason",
                "scheme_resolution",
            ],
        },
        "refusal_contract": {
            "fields": ["refusal_type", "message_hint", "citation_url", "intent", "policy_code"],
            "refusal_types": [
                "advisory",
                "comparison",
                "mixed_intent",
                "out_of_scope",
                "disambiguate",
                "performance_info",
            ],
            "citation_rule": "exactly one URL from 16-url allowlist or configured default",
        },
        "performance_limited_flag": {
            "field": "performance_limited",
            "when": "intent.action == performance_limited",
            "phase5_note": "Ground answers in retrieved text only; no return projections.",
        },
        "evaluation_summary": dict(eval_summary or {}),
    }


def write_phase5_handoff(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def default_handoff_path() -> Path:
    return phase4_retrieval_root() / "artifacts" / "service" / "phase5_retrieval_handoff.json"
