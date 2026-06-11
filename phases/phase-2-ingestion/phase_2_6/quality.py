"""Aggregate parsing / normalization success for Phase 2.6 quality report."""

from __future__ import annotations

from typing import Any, Mapping


def parse_success(row: Mapping[str, Any]) -> bool:
    """
    Corpus-level success for the >=95% gate: extract usable, clean body present,
    normalize not failed when recorded.
    """
    ex = str(row.get("extract_status") or "")
    if ex in ("parse_error", "empty_shell"):
        return False
    if ex not in ("ok", "partial"):
        return False
    if row.get("missing_clean_markdown"):
        return False
    if not int(row.get("clean_md_bytes") or 0):
        return False
    ns = row.get("normalize_status")
    if ns is not None and str(ns) in ("empty", "failed"):
        return False
    if row.get("doc_metadata_error") == "missing_clean_markdown":
        return False
    return True


def bump(counter: dict[str, int], key: str) -> None:
    counter[key] = counter.get(key, 0) + 1


def aggregate(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    extract_counts: dict[str, int] = {}
    normalize_counts: dict[str, int] = {}
    ok = 0
    total_raw = 0
    total_clean = 0
    for r in rows:
        bump(extract_counts, str(r.get("extract_status") or "unknown"))
        ns = r.get("normalize_status")
        bump(normalize_counts, str(ns) if ns is not None else "unknown")
        if parse_success(r):
            ok += 1
        total_raw += int(r.get("raw_html_bytes") or 0)
        total_clean += int(r.get("clean_md_bytes") or 0)

    n = len(rows) or 1
    return {
        "entry_count": len(rows),
        "parse_success_count": ok,
        "parse_success_rate": round(ok / n, 4),
        "extract_status_counts": extract_counts,
        "normalize_status_counts": normalize_counts,
        "total_raw_html_bytes": total_raw,
        "total_clean_markdown_bytes": total_clean,
    }
