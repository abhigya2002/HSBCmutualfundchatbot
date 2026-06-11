"""Data contracts for Phase 5.4 factual composer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class FactualAnswer:
    """Architecture contract: evidence-grounded factual draft for Phase 5.5 validation."""

    body_text: str
    citation_url: str
    citation_markdown: str
    footer_line: str
    footer_date: str
    evidence_chunk_id: str
    scheme: str = ""
    section_title: str = ""
    performance_limited: bool = False
    disclaimer_line: str = ""
    number_grounding_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def display_text(self) -> str:
        parts = [
            self.body_text.strip(),
            self.citation_markdown.strip(),
            self.footer_line.strip(),
            self.disclaimer_line.strip(),
        ]
        return "\n\n".join(p for p in parts if p)
