"""Data contracts for Phase 5.5 post-generation validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

AnswerType = Literal["refusal", "factual"]


@dataclass(frozen=True)
class ValidationViolation:
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


@dataclass
class DraftEnvelope:
    """Unified draft view for refusal and factual answers."""

    answer_type: AnswerType
    body_text: str
    citation_url: str
    citation_markdown: str
    disclaimer_line: str
    footer_line: str = ""
    footer_date: str = ""
    evidence_chunk_id: str = ""
    refusal_type: str = ""
    chunk_text: str = ""
    number_grounding_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationResult:
    """Architecture contract: validator output before Phase 6."""

    passed: bool
    violations: list[ValidationViolation]
    repaired: bool
    answer_type: AnswerType
    draft: dict[str, Any]
    display_text: str
    repair_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "violations": [v.to_dict() for v in self.violations],
            "repaired": self.repaired,
            "answer_type": self.answer_type,
            "draft": self.draft,
            "display_text": self.display_text,
            "repair_actions": list(self.repair_actions),
        }


@dataclass(frozen=True)
class AssistantResponse:
    """Final user-visible payload after validation."""

    answer_type: AnswerType
    body_text: str
    citation_url: str
    citation_markdown: str
    footer_line: str
    disclaimer_line: str
    display_text: str
    evidence_chunk_id: str = ""
    footer_date: str = ""
    refusal_type: str = ""
    validation_passed: bool = True
    validation_repaired: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_validation(cls, result: ValidationResult) -> "AssistantResponse":
        draft = result.draft
        parts = [
            str(draft.get("body_text") or "").strip(),
            str(draft.get("citation_markdown") or "").strip(),
        ]
        if result.answer_type == "factual":
            parts.append(str(draft.get("footer_line") or "").strip())
        parts.append(str(draft.get("disclaimer_line") or "").strip())
        display = "\n\n".join(p for p in parts if p)
        return cls(
            answer_type=result.answer_type,
            body_text=str(draft.get("body_text") or ""),
            citation_url=str(draft.get("citation_url") or ""),
            citation_markdown=str(draft.get("citation_markdown") or ""),
            footer_line=str(draft.get("footer_line") or ""),
            disclaimer_line=str(draft.get("disclaimer_line") or ""),
            display_text=display,
            evidence_chunk_id=str(draft.get("evidence_chunk_id") or ""),
            footer_date=str(draft.get("footer_date") or ""),
            refusal_type=str(draft.get("refusal_type") or ""),
            validation_passed=result.passed,
            validation_repaired=result.repaired,
        )
