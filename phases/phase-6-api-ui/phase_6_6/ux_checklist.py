"""UX validation checklist for Next.js frontend (Phase 6.6)."""

from __future__ import annotations

import time
from typing import Callable

import httpx

from phase_6_6.check_result import CheckResult

DEFAULT_UI_URL = "http://localhost:3000"

SAMPLE_QUESTIONS: tuple[str, ...] = (
    "What is the expense ratio of HSBC Small Cap Fund?",
    "What is the exit load of HSBC Midcap Fund?",
    "What is the minimum SIP for HSBC Gilt Fund?",
)


def _make_result(
    check_id: str,
    description: str,
    *,
    expected: str,
    passed: bool,
    actual: str,
    latency_ms: int,
) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        description=description,
        query=None,
        expected=expected,
        actual=actual,
        passed=passed,
        latency_ms=latency_ms,
    )


class UXChecklist:
    """Static HTML checks against the Phase 6.5 Next.js UI."""

    def __init__(
        self,
        ui_url: str = DEFAULT_UI_URL,
        *,
        on_check: Callable[[CheckResult], None] | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.ui_url = ui_url.rstrip("/")
        self.on_check = on_check
        self.timeout_seconds = timeout_seconds
        self._client = httpx.Client(timeout=timeout_seconds)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> UXChecklist:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def run_all(self) -> list[CheckResult]:
        start = time.perf_counter()
        try:
            resp = self._client.get(self.ui_url)
            latency = int((time.perf_counter() - start) * 1000)
            html = resp.text
            status = resp.status_code
        except Exception as exc:
            latency = int((time.perf_counter() - start) * 1000)
            fail = _make_result(
                "UX-01",
                "Frontend page returns HTTP 200",
                expected="HTTP 200",
                passed=False,
                actual=f"request failed: {exc}",
                latency_ms=latency,
            )
            self._emit(fail)
            return [fail]

        results: list[CheckResult] = []
        results.append(
            self._emit(
                _make_result(
                    "UX-01",
                    "Frontend page returns HTTP 200",
                    expected="HTTP 200",
                    passed=status == 200,
                    actual=f"status={status}",
                    latency_ms=latency,
                )
            )
        )

        content_checks: tuple[tuple[str, str, str], ...] = (
            ("UX-02", "Page contains assistant title", "HSBC Mutual Fund Assistant"),
            ("UX-03", "Page contains facts-only disclaimer", "Facts-only"),
            ("UX-04", "Page contains investment advice disclaimer", "No investment advice"),
        )
        for check_id, description, needle in content_checks:
            found = needle in html
            results.append(
                self._emit(
                    _make_result(
                        check_id,
                        description,
                        expected=f"HTML contains {needle!r}",
                        passed=found,
                        actual="found" if found else "not found",
                        latency_ms=0,
                    )
                )
            )

        for idx, question in enumerate(SAMPLE_QUESTIONS, start=1):
            found = question in html
            results.append(
                self._emit(
                    _make_result(
                        f"UX-{4 + idx:02d}",
                        f"Sample question {idx} visible on welcome screen",
                        expected=f"HTML contains sample question",
                        passed=found,
                        actual=f"found={found}, question={question!r}",
                        latency_ms=0,
                    )
                )
            )

        return results

    def _emit(self, result: CheckResult) -> CheckResult:
        if self.on_check:
            self.on_check(result)
        return result
