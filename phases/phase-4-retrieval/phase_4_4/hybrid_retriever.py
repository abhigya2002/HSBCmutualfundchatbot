"""Hybrid BM25 + vector retrieval with allowlist filtering (Phase 4.4)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from phase_4_3.contracts import SchemeResolution, SchemeStatus
from phase_4_4.allowlist_filter import canonicalize_source_url, is_allowlisted_source
from phase_4_4.config_load import load_hybrid_config
from phase_4_4.contracts import CandidateScores, HybridRetrievalResult, RetrievalCandidate
from phase_4_4.index_context import HybridIndexContext, load_hybrid_context


@dataclass
class _MergedRow:
    chunk_id: str
    vector_score: float | None = None
    keyword_score: float | None = None
    channels: set[str] = field(default_factory=set)
    source_url: str = ""
    scheme: str = ""
    section_title: str = ""
    text: str = ""
    effective_date: str = ""


def _minmax(values: list[float]) -> dict[int, float]:
    if not values:
        return {}
    lo = min(values)
    hi = max(values)
    if hi <= lo:
        return {i: 1.0 for i in range(len(values))}
    return {i: (v - lo) / (hi - lo) for i, v in enumerate(values)}


def _interim_fused(vector: float | None, keyword: float | None) -> float:
    parts = [s for s in (vector, keyword) if s is not None]
    return max(parts) if parts else 0.0


class HybridRetriever:
    """Union keyword + vector hits by chunk_id; enforce allowlist filter."""

    def __init__(
        self,
        ctx: HybridIndexContext | None = None,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> None:
        self.ctx = ctx or load_hybrid_context()
        self.config = dict(config or load_hybrid_config())

    def retrieve(
        self,
        query: str,
        *,
        scheme_resolution: SchemeResolution | None = None,
        top_k_per_channel: int | None = None,
        fused_pool_size: int | None = None,
    ) -> HybridRetrievalResult:
        cfg = self.config
        k_channel = int(top_k_per_channel or cfg.get("top_k_per_channel") or 5)
        pool_size = int(fused_pool_size or cfg.get("fused_pool_size") or 12)

        scheme_filter, source_url_filter = self._scheme_filters(scheme_resolution)

        vector_index = self.ctx.indexes.vector_index
        keyword_index = self.ctx.indexes.keyword_index
        embedder = self.ctx.embedder

        from phase_3_5.query import is_stopword_only_query

        stopword_only = is_stopword_only_query(query)
        use_keyword = not stopword_only
        keyword_hits = []
        if use_keyword:
            keyword_hits = keyword_index.search(
                query,
                top_k=k_channel,
                scheme=scheme_filter,
                source_url=source_url_filter,
            )

        vector_fallback_only = stopword_only or (
            not keyword_hits and str(cfg.get("keyword_empty_fallback") or "vector") == "vector"
        )

        qvec = embedder.embed_texts([query])[0]
        vector_hits = vector_index.search(
            qvec,
            top_k=k_channel,
            scheme=scheme_filter,
            source_url=source_url_filter,
        )

        merged = self._merge_hits(keyword_hits, vector_hits, vector_index)
        candidates, filtered_count = self._to_candidates(merged, pool_size)

        return HybridRetrievalResult(
            query=query,
            candidates=candidates,
            index_version=self.ctx.handoff.index_version,
            embedding_model_id=self.ctx.handoff.embedding_model_id,
            scheme_filter=scheme_filter,
            source_url_filter=source_url_filter,
            keyword_channel_used=use_keyword and bool(keyword_hits),
            vector_fallback_only=vector_fallback_only and not keyword_hits,
            filtered_off_allowlist=filtered_count,
            candidate_pool_size=len(candidates),
        )

    def _scheme_filters(
        self,
        resolution: SchemeResolution | None,
    ) -> tuple[str | None, str | None]:
        if resolution is None or not resolution.is_resolved:
            return None, None
        min_conf = float(self.config.get("scheme_filter_min_confidence") or 0.82)
        if resolution.confidence < min_conf:
            return None, None
        scheme = resolution.scheme or resolution.resolved_scheme
        url = resolution.citation_url_candidate or resolution.source_url
        if resolution.status == SchemeStatus.RESOLVED.value and scheme:
            return scheme, canonicalize_source_url(url) if url else None
        return None, None

    def _merge_hits(self, keyword_hits, vector_hits, vector_index) -> dict[str, _MergedRow]:
        merged: dict[str, _MergedRow] = {}
        records = getattr(vector_index, "_records", {})

        def ensure(chunk_id: str) -> _MergedRow:
            if chunk_id not in merged:
                rec = records.get(chunk_id) or {}
                merged[chunk_id] = _MergedRow(
                    chunk_id=chunk_id,
                    source_url=str(rec.get("source_url") or ""),
                    scheme=str(rec.get("scheme") or ""),
                    section_title=str(rec.get("section_title") or ""),
                    text=str(rec.get("text") or ""),
                    effective_date=str(rec.get("effective_date") or ""),
                )
            return merged[chunk_id]

        for hit in keyword_hits:
            row = ensure(hit.chunk_id)
            row.keyword_score = float(hit.score)
            row.channels.add("keyword")
            if not row.source_url:
                row.source_url = str(hit.source_url or "")
            if not row.scheme:
                row.scheme = str(hit.scheme or "")
            if not row.section_title:
                row.section_title = str(getattr(hit, "section_title", "") or "")

        for hit in vector_hits:
            row = ensure(hit.chunk_id)
            row.vector_score = float(hit.score)
            row.channels.add("vector")
            if not row.source_url:
                row.source_url = str(hit.source_url or "")
            if not row.scheme:
                row.scheme = str(hit.scheme or "")
            if not row.section_title:
                row.section_title = str(getattr(hit, "section_title", "") or "")
            if not row.text:
                row.text = str(getattr(hit, "text_preview", "") or "")

        return merged

    def _to_candidates(
        self,
        merged: dict[str, _MergedRow],
        pool_size: int,
    ) -> tuple[list[RetrievalCandidate], int]:
        if not merged:
            return [], 0

        rows = list(merged.values())
        filtered_off = 0
        allowlist_on = bool(self.config.get("allowlist_filter", True))

        vec_rows = [r for r in rows if r.vector_score is not None]
        kw_rows = [r for r in rows if r.keyword_score is not None]
        vec_normed = _minmax([float(r.vector_score or 0.0) for r in vec_rows])
        kw_normed = _minmax([float(r.keyword_score or 0.0) for r in kw_rows])
        vec_map = {r.chunk_id: vec_normed[i] for i, r in enumerate(vec_rows)}
        kw_map = {r.chunk_id: kw_normed[i] for i, r in enumerate(kw_rows)}

        scored: list[tuple[float, _MergedRow, float | None, float | None]] = []
        for row in rows:
            url = canonicalize_source_url(row.source_url)
            if allowlist_on and url and not is_allowlisted_source(url):
                filtered_off += 1
                continue

            v_norm = vec_map.get(row.chunk_id)
            k_norm = kw_map.get(row.chunk_id)
            fused = _interim_fused(v_norm, k_norm)
            scored.append((fused, row, row.vector_score, row.keyword_score))

        scored.sort(key=lambda t: (-t[0], t[1].chunk_id))

        candidates: list[RetrievalCandidate] = []
        for fused, row, v_raw, k_raw in scored[:pool_size]:
            text = row.text
            candidates.append(
                RetrievalCandidate(
                    chunk_id=row.chunk_id,
                    text=text,
                    text_preview=text[:240],
                    source_url=canonicalize_source_url(row.source_url),
                    scheme=row.scheme,
                    section_title=row.section_title,
                    effective_date=row.effective_date,
                    scores=CandidateScores(vector=v_raw, keyword=k_raw, fused=round(fused, 6)),
                    channels=tuple(sorted(row.channels)),
                ),
            )
        return candidates, filtered_off


def hybrid_retrieve(
    query: str,
    *,
    scheme_resolution: SchemeResolution | None = None,
) -> HybridRetrievalResult:
    return HybridRetriever().retrieve(query, scheme_resolution=scheme_resolution)
