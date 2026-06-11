"""Chunk one scheme via ``section_sliding_v1``."""

from __future__ import annotations

from typing import Any, Mapping

from chunking.contracts import Chunk, ChunkingParams
from chunking.section_sliding import chunk_markdown_section_sliding
from phase_3_2.load import SchemeChunkInput, effective_date_from_metadata


def chunk_scheme(
    inp: SchemeChunkInput,
    config: Mapping[str, Any],
    params: ChunkingParams,
) -> list[Chunk]:
    strategy = str(config.get("default_strategy", "section_sliding_v1"))
    doc_type = str(config.get("doc_type", "groww_scheme_page"))
    compliance_rank = int(config.get("default_compliance_rank", 1))
    effective_date = effective_date_from_metadata(inp.doc_metadata, inp.clean_document)

    if strategy != "section_sliding_v1":
        raise ValueError(f"Unsupported chunk strategy: {strategy!r}")

    return chunk_markdown_section_sliding(
        inp.body,
        clean_document=inp.clean_document,
        scheme=inp.scheme,
        source_url=inp.source_url,
        doc_type=doc_type,
        effective_date=effective_date,
        compliance_rank=compliance_rank,
        params=params,
        strategy_name=strategy,
    )
