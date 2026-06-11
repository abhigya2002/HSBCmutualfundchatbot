"""Run all Phase 7.2 test packs and write phase7_2_test_report.json."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import httpx

from phase_7_2.constants import API_BASE, HEALTH_URL
from phase_7_2.test_edge_cases import run_suite as run_edge_suite
from phase_7_2.test_factual import run_suite as run_factual_suite
from phase_7_2.test_refusals import run_suite as run_refusal_suite

REPORT_PATH = Path(__file__).resolve().parent / "phase7_2_test_report.json"


def _print_result(result: dict) -> None:
    status = "PASS" if result["passed"] else "FAIL"
    line = f"[{status}] {result['check_id']} ({result['latency_ms']}ms)"
    if not result["passed"]:
        line += f" — {result['actual']}"
    print(line)


def _summary(name: str, suite: dict) -> str:
    bar = " OK" if suite.get("pass_bar_met") else " BELOW PASS BAR"
    return f"Suite {name}: {suite['passed']}/{suite['total']} ({suite['pass_rate_pct']}){bar}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 7.2 automated test packs")
    parser.add_argument("--api-base", default=API_BASE)
    args = parser.parse_args(argv)

    print(f"Phase 7.2 test packs — API {args.api_base}\n")

    try:
        health = httpx.get(f"{args.api_base.rstrip('/')}/health", timeout=5.0)
        if health.status_code != 200 or health.json().get("status") != "ok":
            print(f"ERROR: API health check failed at {HEALTH_URL}")
            return 1
    except Exception as exc:
        print(f"ERROR: API not reachable at {args.api_base} — {exc}")
        return 1

    print("--- Factual pack ---")
    factual = run_factual_suite(on_result=_print_result)

    print("\n--- Refusal pack ---")
    refusal = run_refusal_suite(on_result=_print_result)

    print("\n--- Edge case pack ---")
    edge = run_edge_suite(on_result=_print_result)

    total = factual["total"] + refusal["total"] + edge["total"]
    passed = factual["passed"] + refusal["passed"] + edge["passed"]
    rate = passed / total if total else 0.0

    report = {
        "phase": "7.2",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "api_base_url": args.api_base,
        "suites": {"factual": factual, "refusal": refusal, "edge_case": edge},
        "overall": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate_pct": f"{int(round(rate * 100))}%",
            "all_pass_bars_met": all(
                s.get("pass_bar_met") for s in (factual, refusal, edge)
            ),
        },
    }

    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("\n" + "=" * 48)
    print(_summary("1 Factual ", factual))
    print(_summary("2 Refusal  ", refusal))
    print(_summary("3 Edge     ", edge))
    print(f"Overall:          {passed}/{total} ({report['overall']['pass_rate_pct']})")
    print("=" * 48)
    print(f"\nReport saved to {REPORT_PATH.as_posix()}")

    return 0 if report["overall"]["all_pass_bars_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
