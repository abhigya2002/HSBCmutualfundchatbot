"""Optional LLM intent labeler (feature-flagged; not required for v1)."""

from __future__ import annotations

from typing import Any, Callable, Mapping

from phase_4_2.contracts import IntentResult


def classify_with_llm(
    query: str,
    rules: Mapping[str, Any],
    *,
    fallback: Callable[[str], IntentResult],
) -> IntentResult:
    """
    Placeholder for an LLM-backed classifier.

    Enable only when ``feature_flags.llm_classifier`` is true **and**
    ``INTENT_LLM_ENABLED=1``. Until wired, delegates to rule-based fallback.
    """
    _ = rules
    return fallback(query)
