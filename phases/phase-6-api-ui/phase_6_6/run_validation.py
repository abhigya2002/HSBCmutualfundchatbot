"""
Phase 6.6 — Run E2E + UX validation and write the report artifact.

Run from ``phases/phase-6-api-ui`` (both servers must be live)::

    python -m phase_6_6.run_validation
    python -m phase_6_6.run_validation --api-base http://127.0.0.1:8000 --ui-url http://localhost:3000
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from phase_6_6.check_result import CheckResult
from phase_6_6.e2e_validator import DEFAULT_API_BASE, E2EValidator
from phase_6_6.ux_checklist import DEFAULT_UI_URL, UXChecklist

REPORT_FILENAME = "phase6_e2e_validation_report.json"


def _phase6_root() -> Path:
    return Path(__file__).resolve().parent


def _print_check(result: CheckResult) -> None:
    status = "PASS" if result.passed else "FAIL"
    suffix = f" ({result.latency_ms}ms)" if result.latency_ms else ""
    print(f"[{status}] {result.check_id} — {result.description}{suffix}")
    if not result.passed:
        print(f"         expected: {result.expected}")
        print(f"         actual:   {result.actual}")


def _build_report(checks: list[CheckResult]) -> dict:
    total = len(checks)
    passed = sum(1 for c in checks if c.passed)
    failed = total - passed
    rate = f"{int(round(100 * passed / total))}%" if total else "0%"
    return {
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": rate,
        "checks": [c.to_dict() for c in checks],
    }


def run_validation(*, api_base: str, ui_url: str) -> tuple[dict, list[CheckResult]]:
    checks: list[CheckResult] = []

    def on_check(result: CheckResult) -> None:
        _print_check(result)

    print(f"Phase 6.6 validation — API {api_base} | UI {ui_url}\n")

    with E2EValidator(api_base, on_check=on_check) as e2e:
        checks.extend(e2e.run_all())

    print()
    with UXChecklist(ui_url, on_check=on_check) as ux:
        checks.extend(ux.run_all())

    report = _build_report(checks)
    return report, checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 6.6 E2E + UX validation runner.")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--ui-url", default=DEFAULT_UI_URL)
    parser.add_argument(
        "--report-path",
        default=str(_phase6_root() / REPORT_FILENAME),
        help="Output path for phase6_e2e_validation_report.json",
    )
    args = parser.parse_args(argv)

    report, checks = run_validation(api_base=args.api_base, ui_url=args.ui_url)

    report_path = Path(args.report_path)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print()
    print(f"Phase 6.6 Validation: {report['passed']}/{report['total']} passed ({report['pass_rate']})")
    print(f"Report saved to {report_path.as_posix()}")

    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
