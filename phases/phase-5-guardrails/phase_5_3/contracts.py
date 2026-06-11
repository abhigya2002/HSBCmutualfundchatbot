"""Data contracts for Phase 5.3 refusal composer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RefusalAnswer:
    """Architecture contract: user-visible refusal with one allowlisted citation."""

    refusal_type: str
    body_text: str
    citation_url: str
    citation_markdown: str
    disclaimer_line: str
    citation_label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def display_text(self) -> str:
        parts = [self.body_text.strip(), self.citation_markdown.strip(), self.disclaimer_line.strip()]
        return "\n\n".join(p for p in parts if p)
