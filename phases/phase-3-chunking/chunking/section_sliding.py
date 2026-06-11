"""Section-first sliding windows with token budget and tail overlap (Phase 3)."""

from __future__ import annotations

from typing import Any, Mapping

from chunking.contracts import Chunk, ChunkingParams
from chunking.table_units import atomic_char_spans, split_span_by_sentences
from chunking.tokenizer import estimate_tokens


def _looks_like_markdown_table(fragment: str) -> bool:
    lines = [ln for ln in fragment.splitlines() if ln.strip()]
    return len(lines) >= 2 and all("|" in ln for ln in lines)


def _flatten_units_for_section(
    body: str,
    sec: Mapping[str, Any],
    *,
    max_chars: int,
) -> list[tuple[int, int, str, int]]:
    """Absolute (start, end) spans with section title/level; oversized spans split unless table."""
    st = int(sec["start_char"])
    en = int(sec["end_char"])
    title = str(sec.get("title", ""))
    level = int(sec.get("level", 0))
    slice_ = body[st:en]
    out: list[tuple[int, int, str, int]] = []
    for u0, u1 in atomic_char_spans(slice_):
        abs_a, abs_b = st + u0, st + u1
        frag = body[abs_a:abs_b]
        if _looks_like_markdown_table(frag) and len(frag) > max_chars:
            out.append((abs_a, abs_b, title, level))
            continue
        for sa, sb in split_span_by_sentences(body, (abs_a, abs_b), max_chars):
            out.append((sa, sb, title, level))
    return out


def chunk_markdown_section_sliding(
    body: str,
    *,
    clean_document: Mapping[str, Any],
    scheme: str,
    source_url: str,
    doc_type: str,
    effective_date: str | None,
    compliance_rank: int,
    params: ChunkingParams,
    strategy_name: str = "section_sliding_v1",
) -> list[Chunk]:
    """
    Build chunks that respect Phase 2.6 section boundaries *softly* (units never cross
    tables mid-row; paragraphs stay whole unless oversized, then whitespace-split).
    """
    sections: list[Mapping[str, Any]] = list(clean_document.get("sections") or ())
    if not sections:
        sections = [
            {"level": 0, "title": "(document)", "start_char": 0, "end_char": len(body)},
        ]

    body_len = len(body)
    max_chars = max(200, int(params.target_tokens_max * params.chars_per_token))
    min_chars = max(100, int(params.target_tokens_min * params.chars_per_token))
    if body_len > 0:
        min_chars = min(min_chars, body_len)
    overlap_chars = max(40, int(params.overlap_tokens() * params.chars_per_token))
    # P3-01: shrink overlap when the document is shorter than the overlap window.
    if body_len > 0:
        overlap_chars = min(overlap_chars, max(0, body_len // 4))

    units: list[tuple[int, int, str, int]] = []
    for sec in sections:
        units.extend(_flatten_units_for_section(body, sec, max_chars=max_chars))

    if not units and body.strip():
        return [
            Chunk(
                chunk_id=f"{scheme}_c0000",
                text=body,
                start_char=0,
                end_char=body_len,
                source_url=source_url,
                scheme=scheme,
                doc_type=doc_type,
                section_title=str(sections[0].get("title", "(document)")),
                section_level=int(sections[0].get("level", 0)),
                effective_date=effective_date,
                compliance_rank=compliance_rank,
                strategy=strategy_name,
                extra={
                    "estimated_tokens": estimate_tokens(body, chars_per_token=params.chars_per_token),
                    "adaptive_overlap": True,
                },
            )
        ]

    if not units:
        return []

    chunks: list[Chunk] = []
    lo = 0
    chunk_idx = 0
    while lo < len(units):
        total = 0
        hi = lo
        while hi < len(units):
            ua, ub, _, _ = units[hi]
            piece_len = ub - ua
            if total > 0 and total + piece_len > max_chars and total >= min_chars:
                break
            if total == 0 and piece_len > max_chars:
                hi += 1
                total += piece_len
                break
            total += piece_len
            hi += 1
            if total >= max_chars:
                break

        chunk_start = units[lo][0]
        chunk_end = units[hi - 1][1]
        sec_title = units[lo][2]
        sec_level = units[lo][3]
        text = body[chunk_start:chunk_end]

        cid = f"{scheme}_c{chunk_idx:04d}"
        chunks.append(
            Chunk(
                chunk_id=cid,
                text=text,
                start_char=chunk_start,
                end_char=chunk_end,
                source_url=source_url,
                scheme=scheme,
                doc_type=doc_type,
                section_title=sec_title,
                section_level=sec_level,
                effective_date=effective_date,
                compliance_rank=compliance_rank,
                strategy=strategy_name,
                extra={
                    "estimated_tokens": estimate_tokens(text, chars_per_token=params.chars_per_token),
                },
            )
        )
        chunk_idx += 1

        if hi >= len(units):
            break

        target = chunk_end - overlap_chars
        nlo = lo
        while nlo < len(units) and units[nlo][1] <= target:
            nlo += 1
        if nlo <= lo:
            nlo = hi
        lo = nlo

    if not chunks and body.strip():
        chunks.append(
            Chunk(
                chunk_id=f"{scheme}_c0000",
                text=body,
                start_char=0,
                end_char=body_len,
                source_url=source_url,
                scheme=scheme,
                doc_type=doc_type,
                section_title=str(sections[0].get("title", "(document)")),
                section_level=int(sections[0].get("level", 0)),
                effective_date=effective_date,
                compliance_rank=compliance_rank,
                strategy=strategy_name,
                extra={
                    "estimated_tokens": estimate_tokens(body, chars_per_token=params.chars_per_token),
                    "adaptive_overlap": True,
                },
            )
        )

    return chunks
