"""Validate and transform one Phase 3.2 chunk bundle for index build."""

from __future__ import annotations

from typing import Any, Mapping

from chunking.contracts import CHUNK_STRATEGY_VERSION
from phase_3_1.paths import Phase2ArtifactPaths
from phase_3_3.context_limit import apply_embedding_context_limits
from phase_3_3.dedupe import dedupe_chunks
from phase_3_3.enrich import enrich_chunk_metadata, load_phase2_dates
from phase_3_3.load_bundles import ChunkBundle
from phase_3_3 import PHASE_3_3_VERSION
from phase_3_3.validate import (
    SchemeValidationResult,
    ValidationError,
    validate_chunk_allowlist,
    validate_required_fields,
)


def process_bundle(
    bundle: ChunkBundle,
    config: Mapping[str, Any],
    phase2: Phase2ArtifactPaths,
    registry_url: str,
) -> SchemeValidationResult:
    scheme = bundle.scheme
    source_url = bundle.source_url or registry_url
    chunks_in = bundle.chunks
    result = SchemeValidationResult(
        scheme=scheme,
        source_url=source_url,
        indexable=False,
        status="pending",
        chunk_count_in=len(chunks_in),
    )

    if not chunks_in:
        result.status = "excluded_empty"
        result.errors.append(
            ValidationError(scheme, None, "zero_chunks", "no chunks to index (P3-08)"),
        )
        return result

    doc_type = str(config.get("doc_type", "groww_scheme_page"))
    compliance_rank = int(config.get("default_compliance_rank", 1))
    date_fallback = load_phase2_dates(phase2, scheme)

    val_cfg = config.get("validation") or {}
    emb_cfg = config.get("embedding") or {}
    dedupe_identical = bool(val_cfg.get("dedupe_identical_text", True))
    near_dup = bool(val_cfg.get("near_dup_enabled", False))
    near_dup_j = float(val_cfg.get("near_dup_min_jaccard", 0.92))
    max_input_tokens = int(emb_cfg.get("max_input_tokens", 8192))
    chars_per_token = float(config.get("chars_per_token_estimate", 4.0))

    enriched: list[dict[str, Any]] = []
    for raw in chunks_in:
        ch = enrich_chunk_metadata(
            dict(raw),
            scheme=scheme,
            source_url=source_url,
            doc_type=doc_type,
            default_compliance_rank=compliance_rank,
            effective_date_fallback=date_fallback,
        )
        result.errors.extend(validate_required_fields(ch, scheme))
        allow_errs, canonical = validate_chunk_allowlist(ch, scheme)
        result.errors.extend(allow_errs)
        if canonical:
            ch["source_url"] = canonical
        enriched.append(ch)

    if result.hard_failures():
        result.status = "failed_validation"
        result.chunks = enriched
        return result

    deduped, dedupe_stats = dedupe_chunks(
        enriched,
        source_url=source_url,
        dedupe_identical=dedupe_identical,
        near_dup_enabled=near_dup,
        near_dup_min_jaccard=near_dup_j,
    )
    result.dedupe_stats = dedupe_stats

    final, ctx_stats = apply_embedding_context_limits(
        deduped,
        max_input_tokens=max_input_tokens,
        chars_per_token=chars_per_token,
    )
    result.context_stats = ctx_stats
    result.chunks = final
    result.chunk_count_out = len(final)

    if not final:
        result.status = "excluded_empty_after_dedupe"
        return result

    result.indexable = True
    result.status = "validated"
    return result


def build_validated_bundle(
    bundle: ChunkBundle,
    result: SchemeValidationResult,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    emb_cfg = config.get("embedding") or {}
    out = dict(bundle.raw)
    out["phase"] = "3.3"
    out["phase_3_3_version"] = PHASE_3_3_VERSION
    out["validation_status"] = result.status
    out["indexable"] = result.indexable
    out["chunk_count_in"] = result.chunk_count_in
    out["chunk_count"] = result.chunk_count_out
    out["dedupe_stats"] = result.dedupe_stats
    out["context_limit_stats"] = result.context_stats
    out["embedding_model_id"] = str(emb_cfg.get("model_id", "placeholder-embedding-v1"))
    out["chunk_strategy_version"] = CHUNK_STRATEGY_VERSION
    out["chunks"] = result.chunks
    return out
