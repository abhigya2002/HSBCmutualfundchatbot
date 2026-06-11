"""End-to-end retrieval pipeline: 4.2 → 4.3 → 4.4 → 4.5."""

from __future__ import annotations

from typing import Any, Mapping

from phase_4_1.config_load import load_config
from phase_4_2.audit_log import log_intent_result
from phase_4_2.classifier import RuleBasedIntentClassifier
from phase_4_2.config_load import load_intent_rules
from phase_4_2.contracts import IntentAction, IntentResult
from phase_4_3.audit_log import log_scheme_resolution
from phase_4_3.resolver import SchemeResolver
from phase_4_4.hybrid_retriever import HybridRetriever
from phase_4_5.reranker import Reranker
from phase_4_6.contracts import RetrievalRequest, RetrieveOutcome
from phase_4_6.refusal import build_refusal_response


class RetrievalService:
    """Compose Phase 4.2–4.5; skip hybrid retrieval on refusal intents."""

    def __init__(
        self,
        *,
        config: Mapping[str, Any] | None = None,
        intent_classifier: RuleBasedIntentClassifier | None = None,
        scheme_resolver: SchemeResolver | None = None,
        hybrid_retriever: HybridRetriever | None = None,
        reranker: Reranker | None = None,
    ) -> None:
        self.config = dict(config or load_config())
        self._intent_rules = load_intent_rules()
        self.intent_classifier = intent_classifier or RuleBasedIntentClassifier(self._intent_rules)
        self.scheme_resolver = scheme_resolver or SchemeResolver()
        self.hybrid_retriever = hybrid_retriever or HybridRetriever()
        self.reranker = reranker or Reranker()
        self._service_cfg = dict(self.config.get("service") or {})

    def retrieve(self, request: RetrievalRequest | str) -> RetrieveOutcome:
        req = request if isinstance(request, RetrievalRequest) else RetrievalRequest(query=str(request))
        query = req.query.strip()
        if not query:
            intent = IntentResult(
                intent="out-of-scope",
                action=IntentAction.DISAMBIGUATE.value,
                confidence=1.0,
                reasons=["empty_query"],
                policy_code="O1",
            )
            resolution = self.scheme_resolver.resolve("")
            refusal = build_refusal_response(intent, resolution, self._intent_rules)
            return RetrieveOutcome(
                outcome_type="refusal",
                query=query,
                intent=intent,
                scheme_resolution=resolution,
                refusal=refusal,
                hybrid_skipped=True,
            )

        intent = self.intent_classifier.classify(query)
        log_intent_result(intent, query=query, session_id=req.session_id or None)

        resolution = self.scheme_resolver.resolve(query)
        log_scheme_resolution(resolution, query=query)

        index_version = ""
        embedding_model_id = ""
        try:
            index_version = self.hybrid_retriever.ctx.handoff.index_version
            embedding_model_id = self.hybrid_retriever.ctx.handoff.embedding_model_id
        except Exception:
            pass

        if intent.skip_retrieval:
            refusal = build_refusal_response(intent, resolution, self._intent_rules)
            return RetrieveOutcome(
                outcome_type="refusal",
                query=query,
                intent=intent,
                scheme_resolution=resolution,
                refusal=refusal,
                hybrid_skipped=True,
                index_version=index_version,
                embedding_model_id=embedding_model_id,
            )

        performance_limited = intent.action == IntentAction.PERFORMANCE_LIMITED.value

        hybrid = self.hybrid_retriever.retrieve(query, scheme_resolution=resolution)
        retrieval = self.reranker.rerank(hybrid, intent=intent, scheme_resolution=resolution)

        return RetrieveOutcome(
            outcome_type="retrieval",
            query=query,
            intent=intent,
            scheme_resolution=resolution,
            retrieval=retrieval,
            performance_limited=performance_limited,
            hybrid_skipped=False,
            index_version=retrieval.index_version or index_version,
            embedding_model_id=retrieval.embedding_model_id or embedding_model_id,
        )


def retrieve(query: str, *, session_id: str = "") -> RetrieveOutcome:
    return RetrievalService().retrieve(RetrievalRequest(query=query, session_id=session_id))
