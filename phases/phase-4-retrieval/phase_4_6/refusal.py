"""Build refusal responses for gated intents."""

from __future__ import annotations

from typing import Any, Mapping

from phase_4_2.contracts import IntentAction, IntentResult
from phase_4_3.contracts import SchemeResolution
from phase_4_4.allowlist_filter import canonicalize_source_url, is_allowlisted_source
from phase_4_6.contracts import RefusalResponse


def _default_url(config: Mapping[str, Any]) -> str:
    return str(
        config.get("default_citation_url")
        or "https://groww.in/mutual-funds/hsbc-multi-cap-fund-direct-growth",
    )


def refusal_citation_url(
    intent: IntentResult,
    resolution: SchemeResolution,
    config: Mapping[str, Any],
) -> str:
    url = ""
    if resolution.is_resolved and resolution.citation_url_candidate:
        url = resolution.citation_url_candidate
    elif resolution.source_url:
        url = resolution.source_url
    if url:
        canon = canonicalize_source_url(url)
        if is_allowlisted_source(canon):
            return canon
    return canonicalize_source_url(_default_url(config))


def refusal_type_from_intent(intent: IntentResult) -> str:
    if intent.action == IntentAction.DISAMBIGUATE.value:
        return "disambiguate"
    mapping = {
        "advisory": "advisory",
        "comparison": "comparison",
        "mixed": "mixed_intent",
        "out-of-scope": "out_of_scope",
        "performance-info": "performance_info",
    }
    return mapping.get(intent.intent, intent.intent or "unknown")


def message_hint_for_refusal(refusal_type: str) -> str:
    hints = {
        "advisory": "I provide facts-only answers from official sources and cannot give investment advice.",
        "comparison": "I cannot compare funds or recommend which is better.",
        "mixed_intent": "Your question includes advice-seeking wording; I can only answer factual questions from our HSBC corpus.",
        "out_of_scope": "That question is outside the HSBC schemes covered by this assistant.",
        "disambiguate": "Please ask a factual question about one of the HSBC schemes on Groww.",
        "performance_info": "I can point to factual performance data on the official page but cannot project returns.",
    }
    return hints.get(refusal_type, "I can only answer factual questions from allowlisted official sources.")


def build_refusal_response(
    intent: IntentResult,
    resolution: SchemeResolution,
    config: Mapping[str, Any],
) -> RefusalResponse:
    rtype = refusal_type_from_intent(intent)
    return RefusalResponse(
        refusal_type=rtype,
        message_hint=message_hint_for_refusal(rtype),
        citation_url=refusal_citation_url(intent, resolution, config),
        intent=intent.intent,
        policy_code=intent.policy_code,
        scheme_resolution_status=resolution.status,
    )
