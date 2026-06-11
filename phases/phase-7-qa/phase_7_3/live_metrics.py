"""Live API and source freshness probes for Phase 7.3."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import httpx

from phase_7_3.constants import (
    ALLOWLISTED_CITATION_URLS,
    HEALTH_URL,
    HTTP_HEADERS,
    LATENCY_PROBE_QUERIES,
    LATENCY_PROBE_TIMEOUT,
    PHASE66_REPORT_PATH,
    PHASE72_REPORT_PATH,
    READY_URL,
    CHAT_URL,
    HTTP_TIMEOUT,
)


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_phase72_report() -> dict[str, Any]:
    return load_json(PHASE72_REPORT_PATH)


def load_phase66_report() -> dict[str, Any]:
    return load_json(PHASE66_REPORT_PATH)


def suite_pass_rate(report: dict[str, Any], suite_key: str) -> tuple[int, int, float]:
    suite = (report.get("suites") or {}).get(suite_key) or {}
    passed = int(suite.get("passed") or 0)
    total = int(suite.get("total") or 0)
    rate = (passed / total * 100.0) if total else 0.0
    return passed, total, rate


def overall_score_text(report: dict[str, Any]) -> str:
    overall = report.get("overall") or {}
    passed = int(overall.get("passed") or 0)
    total = int(overall.get("total") or 0)
    pct = overall.get("pass_rate_pct") or (f"{int(round(passed / total * 100))}%" if total else "0%")
    return f"{passed}/{total} ({pct})"


def e2e_score_text(report: dict[str, Any]) -> str:
    passed = int(report.get("passed") or 0)
    total = int(report.get("total") or 0)
    if total:
        pct = report.get("pass_rate")
        if isinstance(pct, str) and pct.endswith("%"):
            pct_str = pct
        else:
            pct_str = f"{int(round(passed / total * 100))}%"
    else:
        pct_str = "0%"
    return f"{passed}/{total} ({pct_str})"


def has_allowlist_violations(report: dict[str, Any]) -> bool:
    checks: list[dict] = []
    for suite in (report.get("suites") or {}).values():
        checks.extend(suite.get("checks") or [])
    for check in checks:
        actual = str(check.get("actual") or "").lower()
        if "citation not allowlisted" in actual:
            return True
    return False


def check_health() -> dict[str, Any]:
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT, headers=HTTP_HEADERS) as client:
            resp = client.get(HEALTH_URL)
            data = resp.json() if resp.content else {}
            ok = resp.status_code == 200 and data.get("status") == "ok"
            return {"ok": ok, "status_code": resp.status_code, "body": data}
    except Exception as exc:
        return {"ok": False, "status_code": 0, "error": str(exc)}


def check_ready() -> dict[str, Any]:
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT, headers=HTTP_HEADERS) as client:
            resp = client.get(READY_URL)
            data = resp.json() if resp.content else {}
            ok = resp.status_code in (200, 503) and isinstance(data.get("ready"), bool)
            return {
                "ok": ok,
                "status_code": resp.status_code,
                "ready": data.get("ready"),
                "checks_count": len(data.get("checks") or []),
            }
    except Exception as exc:
        return {"ok": False, "status_code": 0, "error": str(exc)}


def measure_average_latency() -> dict[str, Any]:
    latencies: list[int] = []
    errors: list[str] = []
    with httpx.Client(timeout=LATENCY_PROBE_TIMEOUT, headers=HTTP_HEADERS) as client:
        for query in LATENCY_PROBE_QUERIES:
            start = time.perf_counter()
            try:
                resp = client.post(CHAT_URL, json={"query": query})
                latency_ms = int((time.perf_counter() - start) * 1000)
                if resp.status_code == 200:
                    latencies.append(latency_ms)
                else:
                    errors.append(f"HTTP {resp.status_code} for {query[:40]}")
            except Exception as exc:
                errors.append(str(exc))
    avg = int(sum(latencies) / len(latencies)) if latencies else 0
    return {
        "average_ms": avg,
        "samples": len(latencies),
        "latencies_ms": latencies,
        "errors": errors,
        "api_reachable": len(latencies) > 0,
    }


def check_source_freshness() -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    reachable = 0
    ok_statuses = frozenset({200, 301, 302, 303, 307, 308})
    with httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=True, headers=HTTP_HEADERS) as client:
        for url in ALLOWLISTED_CITATION_URLS:
            entry: dict[str, Any] = {"url": url, "ok": False, "status_code": 0, "method": "GET"}
            try:
                resp = client.get(url)
                entry["status_code"] = resp.status_code
                entry["ok"] = resp.status_code in ok_statuses
                if entry["ok"]:
                    reachable += 1
            except Exception as exc:
                entry["error"] = str(exc)
            results.append(entry)
    total = len(ALLOWLISTED_CITATION_URLS)
    return {
        "reachable": reachable,
        "total": total,
        "summary": f"{reachable}/{total} URLs reachable",
        "results": results,
    }


def collect_live_metrics() -> dict[str, Any]:
    return {
        "health": check_health(),
        "ready": check_ready(),
        "latency": measure_average_latency(),
        "freshness": check_source_freshness(),
    }
