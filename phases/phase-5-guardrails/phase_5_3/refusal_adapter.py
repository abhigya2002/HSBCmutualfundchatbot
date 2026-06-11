"""Normalize Phase 4 RefusalResponse for the Phase 5.3 composer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NormalizedRefusal:
    refusal_type: str
    message_hint: str
    citation_url: str
    intent: str = ""
    policy_code: str = ""


def normalize_refusal(refusal: Any) -> NormalizedRefusal:
    if hasattr(refusal, "refusal_type"):
        return NormalizedRefusal(
            refusal_type=str(refusal.refusal_type or ""),
            message_hint=str(getattr(refusal, "message_hint", "") or ""),
            citation_url=str(getattr(refusal, "citation_url", "") or ""),
            intent=str(getattr(refusal, "intent", "") or ""),
            policy_code=str(getattr(refusal, "policy_code", "") or ""),
        )
    if isinstance(refusal, dict):
        return NormalizedRefusal(
            refusal_type=str(refusal.get("refusal_type") or ""),
            message_hint=str(refusal.get("message_hint") or ""),
            citation_url=str(refusal.get("citation_url") or ""),
            intent=str(refusal.get("intent") or ""),
            policy_code=str(refusal.get("policy_code") or ""),
        )
    raise TypeError(f"Expected RefusalResponse or dict, got {type(refusal)!r}")
