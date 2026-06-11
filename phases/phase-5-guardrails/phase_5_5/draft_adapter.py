"""Normalize refusal/factual drafts for validation."""

from __future__ import annotations

from typing import Any, Literal

from phase_5_3.contracts import RefusalAnswer
from phase_5_4.contracts import FactualAnswer
from phase_5_5.contracts import DraftEnvelope


def normalize_draft(answer: Any, *, answer_type: Literal["refusal", "factual"] | None = None) -> DraftEnvelope:
    if isinstance(answer, RefusalAnswer):
        return DraftEnvelope(
            answer_type="refusal",
            body_text=answer.body_text,
            citation_url=answer.citation_url,
            citation_markdown=answer.citation_markdown,
            disclaimer_line=answer.disclaimer_line,
            refusal_type=answer.refusal_type,
        )
    if isinstance(answer, FactualAnswer):
        return DraftEnvelope(
            answer_type="factual",
            body_text=answer.body_text,
            citation_url=answer.citation_url,
            citation_markdown=answer.citation_markdown,
            disclaimer_line=answer.disclaimer_line,
            footer_line=answer.footer_line,
            footer_date=answer.footer_date,
            evidence_chunk_id=answer.evidence_chunk_id,
            number_grounding_flags=list(answer.number_grounding_flags),
        )
    if isinstance(answer, DraftEnvelope):
        return answer
    if isinstance(answer, dict):
        atype = answer_type or str(answer.get("answer_type") or "refusal")
        if atype not in ("refusal", "factual"):
            atype = "refusal" if answer.get("refusal_type") else "factual"
        return DraftEnvelope(
            answer_type=atype,  # type: ignore[arg-type]
            body_text=str(answer.get("body_text") or ""),
            citation_url=str(answer.get("citation_url") or ""),
            citation_markdown=str(answer.get("citation_markdown") or ""),
            disclaimer_line=str(answer.get("disclaimer_line") or ""),
            footer_line=str(answer.get("footer_line") or ""),
            footer_date=str(answer.get("footer_date") or ""),
            evidence_chunk_id=str(answer.get("evidence_chunk_id") or ""),
            refusal_type=str(answer.get("refusal_type") or ""),
            chunk_text=str(answer.get("chunk_text") or ""),
            number_grounding_flags=list(answer.get("number_grounding_flags") or []),
        )
    raise TypeError(f"Unsupported draft type: {type(answer)!r}")


def envelope_to_dict(envelope: DraftEnvelope) -> dict[str, Any]:
    data = envelope.to_dict()
    data["answer_type"] = envelope.answer_type
    return data
