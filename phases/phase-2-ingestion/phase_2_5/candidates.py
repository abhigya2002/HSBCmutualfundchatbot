"""
Best-effort candidate FAQ facets from normalized Markdown (Phase 2.5).

These are **hints for indexing / QA**, not verified facts. Only patterns on
in-corpus normalized text; no inference from missing data.
"""

from __future__ import annotations

import re
from typing import Any

_SNIP = 220


def _hit(snippet: str, *, pattern_id: str, value_text: str | None = None) -> dict[str, Any]:
    s = re.sub(r"\s+", " ", snippet.strip())
    if len(s) > _SNIP:
        s = s[: _SNIP - 3] + "..."
    out: dict[str, Any] = {"snippet": s, "pattern": pattern_id}
    if value_text is not None:
        vt = value_text.strip()
        if len(vt) > 80:
            vt = vt[:77] + "..."
        out["value_text"] = vt
    return out


def extract_expense_ratio(text: str) -> dict[str, Any] | None:
    m = re.search(r"(?i)expense\s*ratio\s*([0-9]+(?:\.[0-9]+)?\s*%?)", text)
    if not m:
        return None
    span = max(m.start() - 40, 0), min(m.end() + 40, len(text))
    return _hit(text[span[0] : span[1]], pattern_id="expense_ratio_v1", value_text=m.group(1))


def extract_min_sip(text: str) -> dict[str, Any] | None:
    m = re.search(r"(?i)min\.?\s*for\s*sip\s*(?:₹|Rs\.?|INR\s*)?\s*([0-9][0-9,]*)", text)
    if not m:
        m = re.search(
            r"(?i)minimum\s+sip\s+(?:investment\s+)?(?:is\s+)?(?:set\s+to\s+)?\s*(?:₹|Rs\.?)?\s*([0-9][0-9,]*)",
            text,
        )
    if not m:
        return None
    span = max(m.start() - 30, 0), min(m.end() + 30, len(text))
    return _hit(text[span[0] : span[1]], pattern_id="min_sip_v1", value_text=f"₹{m.group(1)}")


def extract_benchmark(text: str) -> dict[str, Any] | None:
    m = re.search(
        r"(?i)fund\s*benchmark\s*([^\n#|]{3,120}?)(?=\n|##|###|Scheme|\||$)",
        text,
    )
    if not m:
        m = re.search(
            r"(?i)\bbenchmark\b\s*[:\s]*([^\n#|]{3,120}?)(?=\n|##|###|\||$)",
            text,
        )
    if not m:
        return None
    val = m.group(1).strip()
    span = max(m.start() - 20, 0), min(m.end() + 40, len(text))
    return _hit(text[span[0] : span[1]], pattern_id="benchmark_v1", value_text=val)


def extract_exit_load(text: str) -> dict[str, Any] | None:
    m = re.search(r"(?i)exit\s*load[^\n#]{0,160}", text)
    if not m:
        return None
    return _hit(m.group(0), pattern_id="exit_load_v1")


def extract_lock_in(text: str) -> dict[str, Any] | None:
    m = re.search(
        r"(?i)(?:lock[-\s]?in(?:\s*[:\-]|\s+period)?|3\s*y(?:ear)?\s*lock[-\s]?in)[^\n#.]{0,120}",
        text,
    )
    if not m:
        m = re.search(r"(?i)no\s*lock[-\s]?in[^\n]{0,80}", text)
    if not m:
        m = re.search(
            r"(?i)\belss\b[^\n]{0,100}(?:lock|3\s*y(?:ear)?|three\s*y(?:ear)?)",
            text,
        )
    if not m:
        return None
    return _hit(m.group(0), pattern_id="lock_in_v1")


def extract_riskometer(text: str) -> dict[str, Any] | None:
    m = re.search(r"(?i)riskometer[^\n#]{0,100}", text)
    if m:
        return _hit(m.group(0), pattern_id="riskometer_v1")
    m = re.search(r"(?i)rated\s+(very\s+high|high|moderate|low)\s+risk", text)
    if m:
        return _hit(m.group(0), pattern_id="risk_label_v1", value_text=m.group(1) + " risk")
    return None


def extract_statement_tax(text: str) -> dict[str, Any] | None:
    m = re.search(r"(?i)tax\s+implication[^\n#]{0,200}", text)
    if m:
        return _hit(m.group(0), pattern_id="tax_implication_v1")
    m = re.search(
        r"(?i)(?:long[-\s]?term|short[-\s]?term)\s+capital\s+gains[^\n#]{0,120}",
        text,
    )
    if m:
        return _hit(m.group(0), pattern_id="capital_gains_v1")
    m = re.search(r"(?i)stamp\s+duty[^\n#]{0,120}", text)
    if m:
        return _hit(m.group(0), pattern_id="stamp_duty_v1")
    return None


def extract_all_candidates(text: str) -> dict[str, dict[str, Any] | None]:
    return {
        "expense_ratio": extract_expense_ratio(text),
        "exit_load": extract_exit_load(text),
        "min_sip": extract_min_sip(text),
        "lock_in": extract_lock_in(text),
        "riskometer": extract_riskometer(text),
        "benchmark": extract_benchmark(text),
        "statement_tax": extract_statement_tax(text),
    }
