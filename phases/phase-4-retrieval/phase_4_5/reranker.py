"""Re-rank hybrid candidates and pick one citation (Phase 4.5)."""

from __future__ import annotations

from typing import Any, Mapping

from phase_4_2.contracts import IntentResult
from phase_4_3.contracts import SchemeResolution
from phase_4_4.contracts import HybridRetrievalResult, RetrievalCandidate
from phase_4_5.citation import pick_citation_url
from phase_4_5.config_load import load_rerank_config
from phase_4_5.contracts import RankedCandidate, RerankScoreBreakdown, RetrievalResponse
from phase_4_5.signals import facet_match_score, freshness_sort_key, lexical_overlap, scheme_match_boost


def _minmax(values: list[float]) -> list[float]:
    if not values:
        return []
    lo = min(values)
    hi = max(values)
    if hi <= lo:
        return [1.0] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


class Reranker:
    """Weighted fusion + interpretable boosts; deterministic tie-breaks."""

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        self.config = dict(config or load_rerank_config())

    def rerank(
        self,
        hybrid: HybridRetrievalResult,
        *,
        intent: IntentResult | None = None,
        scheme_resolution: SchemeResolution | None = None,
    ) -> RetrievalResponse:
        candidates = list(hybrid.candidates)
        if not candidates:
            citation, prec = pick_citation_url(
                chunk=None,
                resolution=scheme_resolution,
                config=self.config,
            )
            return RetrievalResponse(
                status="not_found_in_sources",
                query=hybrid.query,
                chunk_id="",
                chunk_text="",
                citation_url=citation,
                section_title="",
                effective_date="",
                scheme=scheme_resolution.scheme if scheme_resolution else "",
                index_version=hybrid.index_version,
                embedding_model_id=hybrid.embedding_model_id,
                rank=0,
                scores=RerankScoreBreakdown(),
                ranked_candidates=[],
                citation_precedence=prec,
                not_found_reason="no_candidates",
            )

        channel_w = self.config.get("channel_weights") or {}
        signal_w = self.config.get("signal_weights") or {}
        w_v = float(channel_w.get("vector") or 0.45)
        w_k = float(channel_w.get("keyword") or 0.45)
        w_facet = float(signal_w.get("facet_match") or 0.25)
        w_lex = float(signal_w.get("lexical_overlap") or 0.15)
        w_scheme = float(signal_w.get("scheme_match") or 0.15)
        min_conf = float(self.config.get("scheme_match_min_confidence") or 0.82)

        vec_raw = [float(c.scores.vector or 0.0) for c in candidates]
        kw_raw = [float(c.scores.keyword or 0.0) for c in candidates]
        has_vec = any(c.scores.vector is not None for c in candidates)
        has_kw = any(c.scores.keyword is not None for c in candidates)

        vec_norm = _minmax(vec_raw) if has_vec else [0.0] * len(candidates)
        kw_norm = _minmax(kw_raw) if has_kw else [0.0] * len(candidates)

        scored: list[tuple[float, float, str, RetrievalCandidate, RerankScoreBreakdown]] = []
        for i, cand in enumerate(candidates):
            v_n = vec_norm[i] if cand.scores.vector is not None else 0.0
            k_n = kw_norm[i] if cand.scores.keyword is not None else 0.0
            channel_fused = w_v * v_n + w_k * k_n
            facet = facet_match_score(hybrid.query, cand.text, intent=intent)
            lex = lexical_overlap(hybrid.query, cand.text)
            scheme = scheme_match_boost(
                cand,
                scheme_resolution,
                min_confidence=min_conf,
            )
            final = channel_fused + w_facet * facet + w_lex * lex + w_scheme * scheme
            breakdown = RerankScoreBreakdown(
                vector_norm=round(v_n, 6),
                keyword_norm=round(k_n, 6),
                channel_fused=round(channel_fused, 6),
                facet_match=round(facet, 6),
                lexical_overlap=round(lex, 6),
                scheme_match=round(scheme, 6),
                final_score=round(final, 6),
            )
            fresh = freshness_sort_key(cand.effective_date)
            scored.append((final, fresh, cand.chunk_id, cand, breakdown))

        epsilon = float((self.config.get("tie_break") or {}).get("score_epsilon") or 0.0001)
        scored.sort(key=lambda t: (-round(t[0] / epsilon) * epsilon, -t[1], t[2]))

        ranked: list[RankedCandidate] = []
        for rank, (_, _, _, cand, breakdown) in enumerate(scored, start=1):
            ranked.append(
                RankedCandidate(
                    chunk_id=cand.chunk_id,
                    chunk_text=cand.text,
                    source_url=cand.source_url,
                    scheme=cand.scheme,
                    section_title=cand.section_title,
                    effective_date=cand.effective_date,
                    rank=rank,
                    scores=breakdown,
                    channels=cand.channels,
                ),
            )

        top = ranked[0]
        min_score = float(self.config.get("min_final_score") or 0.28)
        if top.scores.final_score < min_score:
            citation, prec = pick_citation_url(
                chunk=None,
                resolution=scheme_resolution,
                config=self.config,
            )
            return RetrievalResponse(
                status="not_found_in_sources",
                query=hybrid.query,
                chunk_id="",
                chunk_text="",
                citation_url=citation,
                section_title="",
                effective_date="",
                scheme=scheme_resolution.scheme if scheme_resolution else "",
                index_version=hybrid.index_version,
                embedding_model_id=hybrid.embedding_model_id,
                rank=0,
                scores=top.scores,
                ranked_candidates=ranked,
                citation_precedence=prec,
                not_found_reason="below_threshold",
            )

        top_cand = scored[0][3]
        citation, prec = pick_citation_url(
            chunk=top_cand,
            resolution=scheme_resolution,
            config=self.config,
        )
        return RetrievalResponse(
            status="found",
            query=hybrid.query,
            chunk_id=top.chunk_id,
            chunk_text=top.chunk_text,
            citation_url=citation,
            section_title=top.section_title,
            effective_date=top.effective_date,
            scheme=top.scheme,
            index_version=hybrid.index_version,
            embedding_model_id=hybrid.embedding_model_id,
            rank=1,
            scores=top.scores,
            ranked_candidates=ranked,
            citation_precedence=prec,
        )


def rerank_hybrid(
    hybrid: HybridRetrievalResult,
    *,
    intent: IntentResult | None = None,
    scheme_resolution: SchemeResolution | None = None,
) -> RetrievalResponse:
    return Reranker().rerank(hybrid, intent=intent, scheme_resolution=scheme_resolution)
