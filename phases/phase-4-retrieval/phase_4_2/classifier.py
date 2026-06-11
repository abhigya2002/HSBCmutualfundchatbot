"""Rule-based intent classifier v1 (Phase 4.2)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from phase_4_2.contracts import IntentAction, IntentLabel, IntentResult, action_for_intent
from phase_4_2.config_load import default_rules_path, load_intent_rules

_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
_WS = re.compile(r"\s+")


@dataclass
class _Signals:
    injection: list[str] = None  # type: ignore[assignment]
    pii: list[str] = None  # type: ignore[assignment]
    non_hsbc_amc: list[str] = None  # type: ignore[assignment]
    hindi: list[str] = None  # type: ignore[assignment]
    off_topic: list[str] = None  # type: ignore[assignment]
    greeting: list[str] = None  # type: ignore[assignment]
    comparison: list[str] = None  # type: ignore[assignment]
    advisory: list[str] = None  # type: ignore[assignment]
    performance: list[str] = None  # type: ignore[assignment]
    projection: list[str] = None  # type: ignore[assignment]
    ambiguous: list[str] = None  # type: ignore[assignment]
    factual_facets: dict[str, list[str]] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        for name in (
            "injection",
            "pii",
            "non_hsbc_amc",
            "hindi",
            "off_topic",
            "greeting",
            "comparison",
            "advisory",
            "performance",
            "projection",
            "ambiguous",
        ):
            if getattr(self, name) is None:
                setattr(self, name, [])
        if self.factual_facets is None:
            self.factual_facets = {}


def normalize_query(query: str) -> str:
    q = query.strip().lower()
    q = q.replace("\u2019", "'").replace("\u2018", "'")
    return _WS.sub(" ", q)


def _devanagari_ratio(text: str) -> float:
    if not text:
        return 0.0
    letters = [c for c in text if c.isalpha() or _DEVANAGARI.match(c)]
    if not letters:
        return 0.0
    dev = sum(1 for c in letters if _DEVANAGARI.match(c))
    return dev / len(letters)


def _match_keywords(text: str, keywords: list[str]) -> list[str]:
    hits: list[str] = []
    for kw in keywords:
        k = kw.lower().strip()
        if not k:
            continue
        if " " in k:
            if k in text:
                hits.append(k)
            continue
        try:
            if re.search(rf"\b{re.escape(k)}\b", text, flags=re.IGNORECASE):
                hits.append(k)
        except re.error:
            continue
    return hits


def _match_patterns(text: str, patterns: list[str]) -> list[str]:
    hits: list[str] = []
    for pat in patterns:
        try:
            if re.search(pat, text, flags=re.IGNORECASE):
                hits.append(pat)
        except re.error:
            continue
    return hits


def _collect_signals(text: str, rules: Mapping[str, Any]) -> _Signals:
    sig = _Signals()
    oos = rules.get("out_of_scope") or {}

    inj = rules.get("prompt_injection") or {}
    sig.injection = _match_keywords(text, list(inj.get("keywords") or []))
    sig.injection.extend(_match_patterns(text, list(inj.get("patterns") or [])))

    sig.pii = _match_patterns(text, list(oos.get("pii_patterns") or []))

    sig.non_hsbc_amc = _match_keywords(text, list(oos.get("non_hsbc_amc_keywords") or []))
    sig.off_topic = _match_keywords(text, list(oos.get("off_topic_keywords") or []))
    sig.greeting = _match_keywords(text, list(oos.get("greeting_keywords") or []))

    if _devanagari_ratio(text) >= 0.25:
        sig.hindi.append("devanagari_ratio>=0.25")

    comp = rules.get("comparison") or {}
    sig.comparison = _match_keywords(text, list(comp.get("keywords") or []))
    sig.comparison.extend(_match_patterns(text, list(comp.get("patterns") or [])))

    adv = rules.get("advisory") or {}
    sig.advisory = _match_keywords(text, list(adv.get("keywords") or []))
    sig.advisory.extend(_match_patterns(text, list(adv.get("patterns") or [])))

    proj = rules.get("performance_projection") or {}
    sig.projection = _match_keywords(text, list(proj.get("keywords") or []))
    sig.projection.extend(_match_patterns(text, list(proj.get("patterns") or [])))

    perf = rules.get("performance_info") or {}
    sig.performance = _match_keywords(text, list(perf.get("keywords") or []))
    sig.performance.extend(_match_patterns(text, list(perf.get("patterns") or [])))

    amb = rules.get("ambiguous") or {}
    sig.ambiguous = _match_keywords(text, list(amb.get("keywords") or []))
    sig.ambiguous.extend(_match_patterns(text, list(amb.get("patterns") or [])))

    facets_cfg = rules.get("factual_facets") or {}
    for code, facet in facets_cfg.items():
        kws = list((facet or {}).get("keywords") or [])
        hits = _match_keywords(text, kws)
        if hits:
            sig.factual_facets[str(code)] = hits

    return sig


def _confidence(level: str, rules: Mapping[str, Any]) -> float:
    conf = rules.get("confidence") or {}
    return float(conf.get(level, 0.75))


def _build_result(
    *,
    intent: IntentLabel,
    action: IntentAction | None,
    confidence: float,
    reasons: list[str],
    policy_code: str = "",
    facet: str = "",
    query_normalized: str = "",
) -> IntentResult:
    act = action or action_for_intent(intent)
    return IntentResult(
        intent=intent.value,
        action=act.value,
        confidence=round(min(max(confidence, 0.0), 1.0), 4),
        reasons=reasons,
        policy_code=policy_code,
        facet=facet,
        query_normalized=query_normalized,
    )


class RuleBasedIntentClassifier:
    """Keyword + regex classifier aligned with Phase 0 query policy matrix."""

    def __init__(self, rules: Mapping[str, Any] | None = None) -> None:
        self.rules = dict(rules or load_intent_rules())
        self._use_llm = bool((self.rules.get("feature_flags") or {}).get("llm_classifier"))

    def classify(self, query: str) -> IntentResult:
        if self._use_llm and os.environ.get("INTENT_LLM_ENABLED", "").strip() == "1":
            from phase_4_2.llm_classifier import classify_with_llm

            return classify_with_llm(query, self.rules, fallback=self._classify_rules)

        return self._classify_rules(query)

    def _classify_rules(self, query: str) -> IntentResult:
        rules = self.rules
        norm = normalize_query(query)
        if not norm:
            return _build_result(
                intent=IntentLabel.OUT_OF_SCOPE,
                action=IntentAction.DISAMBIGUATE,
                confidence=_confidence("low", rules),
                reasons=["empty_query"],
                policy_code="O1",
                query_normalized=norm,
            )

        sig = _collect_signals(norm, rules)
        conf = rules.get("confidence") or {}

        # Safety-first ordering
        if sig.injection:
            inj = rules.get("prompt_injection") or {}
            return _build_result(
                intent=IntentLabel.OUT_OF_SCOPE,
                action=IntentAction.REFUSE,
                confidence=float(conf.get("high", 0.92)),
                reasons=["prompt_injection:" + ",".join(sig.injection[:3])],
                policy_code=str(inj.get("policy_code") or "R5"),
                query_normalized=norm,
            )

        if sig.pii:
            return _build_result(
                intent=IntentLabel.OUT_OF_SCOPE,
                action=IntentAction.REFUSE,
                confidence=float(conf.get("high", 0.92)),
                reasons=["pii_detected"],
                policy_code="R3",
                query_normalized=norm,
            )

        if sig.hindi:
            return _build_result(
                intent=IntentLabel.OUT_OF_SCOPE,
                action=IntentAction.REFUSE,
                confidence=float(conf.get("medium", 0.75)),
                reasons=sig.hindi,
                policy_code="P4-10",
                query_normalized=norm,
            )

        has_hsbc = "hsbc" in norm

        if sig.non_hsbc_amc and not has_hsbc:
            return _build_result(
                intent=IntentLabel.OUT_OF_SCOPE,
                action=IntentAction.REFUSE,
                confidence=float(conf.get("high", 0.92)),
                reasons=["non_hsbc_amc:" + ",".join(sig.non_hsbc_amc[:3])],
                policy_code="R3",
                query_normalized=norm,
            )

        factual_codes = sorted(sig.factual_facets.keys())
        has_factual = bool(factual_codes)
        has_projection = bool(sig.projection)
        has_advisory = bool(sig.advisory) or has_projection
        has_comparison = bool(sig.comparison)
        has_historical_performance = bool(sig.performance) and not has_projection

        # Global comparison/advisory signals win over generic mutual-fund context
        if has_comparison and not has_factual:
            comp = rules.get("comparison") or {}
            return _build_result(
                intent=IntentLabel.COMPARISON,
                action=IntentAction.REFUSE,
                confidence=float(conf.get("high", 0.92)),
                reasons=["comparison:" + ",".join(sig.comparison[:3])],
                policy_code=str(comp.get("policy_code") or "R2"),
                query_normalized=norm,
            )

        if has_advisory and not has_factual:
            adv = rules.get("advisory") or {}
            policy = str((rules.get("performance_projection") or {}).get("policy_code") or adv.get("policy_code") or "R1")
            reason_tag = "projection:" if has_projection and not sig.advisory else "advisory:"
            hits = (sig.projection + sig.advisory)[:3]
            # Route to mixed/performance-info labels so Phase 5 refusal copy avoids "recommendations".
            if has_projection:
                perf = rules.get("performance_projection") or {}
                return _build_result(
                    intent=IntentLabel.PERFORMANCE_INFO,
                    action=IntentAction.REFUSE,
                    confidence=float(conf.get("high", 0.92)),
                    reasons=[reason_tag + ",".join(hits)],
                    policy_code=str(perf.get("policy_code") or "R1"),
                    query_normalized=norm,
                )
            return _build_result(
                intent=IntentLabel.MIXED,
                action=IntentAction.REFUSE,
                confidence=float(conf.get("high", 0.92)),
                reasons=[reason_tag + ",".join(hits)],
                policy_code=str((rules.get("mixed_intent") or {}).get("policy_code") or "R4"),
                query_normalized=norm,
            )

        if has_factual and (has_advisory or has_comparison):
            mixed = rules.get("mixed_intent") or {}
            return _build_result(
                intent=IntentLabel.MIXED,
                action=IntentAction.REFUSE,
                confidence=float(conf.get("high", 0.92)),
                reasons=[
                    "mixed_refusal_first",
                    "facets=" + ",".join(factual_codes),
                    "signals=" + ",".join((sig.advisory + sig.comparison + sig.projection)[:3]),
                ],
                policy_code=str(mixed.get("policy_code") or "R4"),
                facet=factual_codes[0] if len(factual_codes) == 1 else "",
                query_normalized=norm,
            )

        if has_comparison:
            comp = rules.get("comparison") or {}
            return _build_result(
                intent=IntentLabel.COMPARISON,
                action=IntentAction.REFUSE,
                confidence=float(conf.get("high", 0.92)),
                reasons=["comparison:" + ",".join(sig.comparison[:3])],
                policy_code=str(comp.get("policy_code") or "R2"),
                query_normalized=norm,
            )

        if has_advisory:
            adv = rules.get("advisory") or {}
            policy = str((rules.get("performance_projection") or {}).get("policy_code") or adv.get("policy_code") or "R1")
            reason_tag = "projection:" if has_projection and not sig.advisory else "advisory:"
            hits = (sig.projection + sig.advisory)[:3]
            if has_projection:
                perf = rules.get("performance_projection") or {}
                return _build_result(
                    intent=IntentLabel.PERFORMANCE_INFO,
                    action=IntentAction.REFUSE,
                    confidence=float(conf.get("high", 0.92)),
                    reasons=[reason_tag + ",".join(hits)],
                    policy_code=str(perf.get("policy_code") or "R1"),
                    query_normalized=norm,
                )
            return _build_result(
                intent=IntentLabel.MIXED,
                action=IntentAction.REFUSE,
                confidence=float(conf.get("high", 0.92)),
                reasons=[reason_tag + ",".join(hits)],
                policy_code=str((rules.get("mixed_intent") or {}).get("policy_code") or "R4"),
                query_normalized=norm,
            )

        if sig.ambiguous and has_hsbc:
            amb = rules.get("ambiguous") or {}
            return _build_result(
                intent=IntentLabel.OUT_OF_SCOPE,
                action=IntentAction.DISAMBIGUATE,
                confidence=float(conf.get("medium", 0.75)),
                reasons=["ambiguous:" + ",".join(sig.ambiguous[:3])],
                policy_code=str(amb.get("policy_code") or "O1"),
                query_normalized=norm,
            )

        if has_historical_performance and not has_factual:
            perf = rules.get("performance_info") or {}
            return _build_result(
                intent=IntentLabel.PERFORMANCE_INFO,
                action=IntentAction.PERFORMANCE_LIMITED,
                confidence=float(conf.get("medium", 0.75)),
                reasons=["performance:" + ",".join(sig.performance[:3])],
                policy_code=str(perf.get("policy_code") or "P1"),
                query_normalized=norm,
            )

        if has_factual:
            primary = factual_codes[0]
            level = "high" if len(factual_codes) == 1 else "medium"
            return _build_result(
                intent=IntentLabel.FACTUAL,
                action=IntentAction.RETRIEVE,
                confidence=float(conf.get(level, 0.75)),
                reasons=["facet:" + ",".join(factual_codes)],
                policy_code=primary,
                facet=primary,
                query_normalized=norm,
            )

        if has_historical_performance:
            perf = rules.get("performance_info") or {}
            return _build_result(
                intent=IntentLabel.PERFORMANCE_INFO,
                action=IntentAction.PERFORMANCE_LIMITED,
                confidence=float(conf.get("medium", 0.75)),
                reasons=["performance:" + ",".join(sig.performance[:3])],
                policy_code=str(perf.get("policy_code") or "P1"),
                query_normalized=norm,
            )

        if sig.off_topic and not has_hsbc:
            return _build_result(
                intent=IntentLabel.OUT_OF_SCOPE,
                action=IntentAction.REFUSE,
                confidence=float(conf.get("medium", 0.75)),
                reasons=["off_topic"],
                policy_code="O1",
                query_normalized=norm,
            )

        if sig.greeting and len(norm.split()) <= 6 and not has_hsbc:
            return _build_result(
                intent=IntentLabel.OUT_OF_SCOPE,
                action=IntentAction.DISAMBIGUATE,
                confidence=float(conf.get("low", 0.55)),
                reasons=["greeting"],
                policy_code="O1",
                query_normalized=norm,
            )

        if has_hsbc or "mutual fund" in norm or "groww" in norm:
            return _build_result(
                intent=IntentLabel.FACTUAL,
                action=IntentAction.RETRIEVE,
                confidence=float(conf.get("low", 0.55)),
                reasons=["hsbc_or_mf_context_no_facet"],
                policy_code="A0",
                query_normalized=norm,
            )

        return _build_result(
            intent=IntentLabel.OUT_OF_SCOPE,
            action=IntentAction.DISAMBIGUATE,
            confidence=float(conf.get("low", 0.55)),
            reasons=["unclassified_steering"],
            policy_code="O1",
            query_normalized=norm,
        )


def classify_query(query: str, *, rules_path: Path | None = None) -> IntentResult:
    rules = load_intent_rules(rules_path)
    return RuleBasedIntentClassifier(rules).classify(query)
