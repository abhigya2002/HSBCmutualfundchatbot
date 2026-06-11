"""Factual query pack — 30 queries (Phase 7.2)."""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import httpx

from phase_7_2.constants import (
    CHAT_URL,
    MAX_LATENCY_MS,
    REQUEST_TIMEOUT,
    is_allowlisted,
    sentence_count,
)

PASS_BAR = 0.90

QUERIES: tuple[tuple[str, str, str], ...] = (
    ("FACTUAL-01", "expense_ratio", "What is the expense ratio of HSBC Small Cap Fund?"),
    ("FACTUAL-02", "expense_ratio", "What is the expense ratio of HSBC Midcap Fund?"),
    ("FACTUAL-03", "expense_ratio", "What is the TER of HSBC Gilt Fund?"),
    ("FACTUAL-04", "expense_ratio", "How much does HSBC Value Fund charge annually?"),
    ("FACTUAL-05", "expense_ratio", "What is the annual fee for HSBC Focused Fund?"),
    ("FACTUAL-06", "exit_load", "What is the exit load of HSBC Small Cap Fund?"),
    ("FACTUAL-07", "exit_load", "What is the exit load of HSBC Infrastructure Fund?"),
    ("FACTUAL-08", "exit_load", "Is there any exit charge on HSBC Gilt Fund?"),
    ("FACTUAL-09", "exit_load", "What happens if I redeem HSBC Midcap Fund early?"),
    ("FACTUAL-10", "exit_load", "What is the redemption fee for HSBC Value Fund?"),
    ("FACTUAL-11", "minimum_sip", "What is the minimum SIP for HSBC Gilt Fund?"),
    ("FACTUAL-12", "minimum_sip", "What is the minimum investment in HSBC Small Cap?"),
    ("FACTUAL-13", "minimum_sip", "How much do I need to start SIP in HSBC Midcap?"),
    ("FACTUAL-14", "minimum_sip", "What is the minimum monthly SIP for HSBC ELSS?"),
    ("FACTUAL-15", "minimum_sip", "Minimum SIP amount for HSBC Large and Mid Cap Fund?"),
    ("FACTUAL-16", "lock_in", "What is the lock-in period for HSBC ELSS fund?"),
    ("FACTUAL-17", "lock_in", "How long is the lock-in for HSBC tax saver fund?"),
    ("FACTUAL-18", "lock_in", "Can I withdraw from HSBC ELSS before 3 years?"),
    ("FACTUAL-19", "riskometer", "What is the risk level of HSBC Small Cap Fund?"),
    ("FACTUAL-20", "riskometer", "What is the riskometer of HSBC Gilt Fund?"),
    ("FACTUAL-21", "riskometer", "Is HSBC Infrastructure Fund high risk?"),
    ("FACTUAL-22", "benchmark", "What is the benchmark of HSBC Midcap Fund?"),
    ("FACTUAL-23", "benchmark", "Which index does HSBC Small Cap Fund track?"),
    ("FACTUAL-24", "benchmark", "What is the benchmark index for HSBC Gilt Fund?"),
    ("FACTUAL-25", "process", "How do I download my HSBC mutual fund statement?"),
    ("FACTUAL-26", "process", "How to get capital gains report for HSBC fund?"),
    ("FACTUAL-27", "process", "How to check my HSBC mutual fund portfolio?"),
    ("FACTUAL-28", "expense_ratio", "What is the expense ratio of HSBC Dynamic Bond Fund?"),
    ("FACTUAL-29", "exit_load", "What is the exit load of HSBC Consumption Fund?"),
    ("FACTUAL-30", "minimum_sip", "What is the minimum SIP for HSBC Multi Cap Fund?"),
)


def run_case(client: httpx.Client, check_id: str, category: str, query: str) -> dict:
    start = time.perf_counter()
    try:
        response = client.post(CHAT_URL, json={"query": query}, timeout=REQUEST_TIMEOUT)
        latency_ms = int((time.perf_counter() - start) * 1000)
        data = response.json()
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            "check_id": check_id,
            "category": category,
            "query": query,
            "passed": False,
            "latency_ms": latency_ms,
            "actual": f"request failed: {exc}",
        }

    assistant = data.get("assistant") or {}
    outcome = str(data.get("outcome_type") or "")
    body_text = str(assistant.get("body_text") or "").strip()
    citation = str(assistant.get("citation_url") or "").strip()
    footer_line = str(assistant.get("footer_line") or "")
    sentences = sentence_count(body_text)

    issues: list[str] = []
    if response.status_code != 200:
        issues.append(f"HTTP {response.status_code}")
    if outcome != "factual":
        issues.append(f"expected factual, got {outcome!r}")
    if not body_text:
        issues.append("empty body_text")
    if sentences > 3:
        issues.append(f"{sentences} sentences (>3)")
    if not is_allowlisted(citation):
        issues.append(f"citation not allowlisted: {citation!r}")
    if "Last updated from sources:" not in footer_line:
        issues.append("footer_line missing 'Last updated from sources:'")
    if latency_ms >= MAX_LATENCY_MS:
        issues.append(f"latency {latency_ms}ms >= {MAX_LATENCY_MS}ms")

    passed = not issues
    actual = f"outcome={outcome!r}, sentences={sentences}, citation={citation!r}, latency_ms={latency_ms}"
    if issues:
        actual += f"; {'; '.join(issues)}"

    return {
        "check_id": check_id,
        "category": category,
        "query": query,
        "passed": passed,
        "latency_ms": latency_ms,
        "actual": actual,
    }


def run_suite(*, on_result=None) -> dict:
    results: list[dict] = []
    with httpx.Client() as client:
        for check_id, category, query in QUERIES:
            result = run_case(client, check_id, category, query)
            results.append(result)
            if on_result:
                on_result(result)

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    rate = passed / total if total else 0.0

    return {
        "suite": "factual",
        "pass_bar": PASS_BAR,
        "pass_bar_met": rate >= PASS_BAR,
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate_pct": f"{int(round(rate * 100))}%",
        "checks": results,
    }


if __name__ == "__main__":
    def _print(r: dict) -> None:
        status = "PASS" if r["passed"] else "FAIL"
        line = f"[{status}] {r['check_id']} ({r['latency_ms']}ms)"
        if not r["passed"]:
            line += f" — {r['actual']}"
        print(line)

    suite = run_suite(on_result=_print)
    print(f"\nFactual: {suite['passed']}/{suite['total']} ({suite['pass_rate_pct']})")
