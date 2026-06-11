"""Backend E2E checks against live Phase 6 API (Phase 6.6)."""

from __future__ import annotations

import json
import re
import time
from typing import Any, Callable

import httpx

from phase_6_6.allowlist import is_allowlisted
from phase_6_6.check_result import CheckResult

DEFAULT_API_BASE = "http://127.0.0.1:8000"

FACTUAL_QUERIES: tuple[str, ...] = (
    "What is the expense ratio of HSBC Small Cap Fund?",
    "What is the exit load of HSBC Midcap Fund?",
    "What is the minimum SIP for HSBC Gilt Fund?",
    "What is the lock-in period for HSBC ELSS fund?",
    "What is the riskometer of HSBC Large and Mid Cap Fund?",
)

REFUSAL_QUERIES: tuple[str, ...] = (
    "Should I invest in HSBC Small Cap Fund?",
    "Which HSBC fund is better for me?",
    "Will HSBC Midcap Fund give good returns?",
)

COMPARISON_QUERY = "Compare HSBC Small Cap and HSBC Midcap Fund"
EMPTY_QUERY = ""
PII_QUERY = "My PAN is ABCDE1234F, which fund should I buy?"

PII_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bABCDE1234F\b", re.IGNORECASE),
    re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),
    re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
)


def _sentence_count(text: str) -> int:
    cleaned = (text or "").strip()
    if not cleaned:
        return 0
    parts = re.split(r"[.!?]+", cleaned)
    return len([p for p in parts if p.strip()])


def _contains_pii(payload: dict[str, Any] | None, *, include_query: bool = False) -> bool:
    if not payload:
        return False
    parts: list[str] = []
    if include_query:
        parts.append(str(payload.get("query") or ""))
    assistant = payload.get("assistant") or {}
    parts.append(json.dumps(assistant, ensure_ascii=False))
    parts.append(str(payload.get("display_text") or ""))
    blob = " ".join(parts)
    return any(p.search(blob) for p in PII_PATTERNS)


def _make_result(
    check_id: str,
    description: str,
    *,
    query: str | None,
    expected: str,
    passed: bool,
    actual: str,
    latency_ms: int,
) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        description=description,
        query=query,
        expected=expected,
        actual=actual,
        passed=passed,
        latency_ms=latency_ms,
    )


class E2EValidator:
    """Run live HTTP checks against ``/health``, ``/ready``, and ``/chat``."""

    def __init__(
        self,
        api_base: str = DEFAULT_API_BASE,
        *,
        on_check: Callable[[CheckResult], None] | None = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        self.api_base = api_base.rstrip("/")
        self.on_check = on_check
        self.timeout_seconds = timeout_seconds
        self._client = httpx.Client(base_url=self.api_base, timeout=timeout_seconds)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> E2EValidator:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def run_all(self) -> list[CheckResult]:
        results: list[CheckResult] = []
        results.append(self.check_health())
        results.append(self.check_ready())
        for idx, query in enumerate(FACTUAL_QUERIES, start=1):
            results.append(self.check_factual_query(query, check_num=idx))
        for idx, query in enumerate(REFUSAL_QUERIES, start=1):
            results.append(self.check_refusal_query(query, check_num=idx))
        results.append(self.check_comparison_refusal())
        results.append(self.check_empty_query())
        results.append(self.check_pii_query())
        return results

    def _emit(self, result: CheckResult) -> CheckResult:
        if self.on_check:
            self.on_check(result)
        return result

    def check_health(self) -> CheckResult:
        start = time.perf_counter()
        try:
            resp = self._client.get("/health")
            latency = int((time.perf_counter() - start) * 1000)
            data = resp.json()
            passed = resp.status_code == 200 and data.get("status") == "ok"
            actual = f"status={resp.status_code}, body={data!r}"
        except Exception as exc:
            latency = int((time.perf_counter() - start) * 1000)
            passed = False
            actual = f"request failed: {exc}"
        return self._emit(
            _make_result(
                "E2E-01",
                "/health returns ok",
                query=None,
                expected='HTTP 200 with {"status": "ok"}',
                passed=passed,
                actual=actual,
                latency_ms=latency,
            )
        )

    def check_ready(self) -> CheckResult:
        start = time.perf_counter()
        try:
            resp = self._client.get("/ready")
            latency = int((time.perf_counter() - start) * 1000)
            data = resp.json()
            has_ready = isinstance(data.get("ready"), bool)
            has_checks = isinstance(data.get("checks"), list)
            passed = resp.status_code in (200, 503) and has_ready and has_checks
            actual = f"status={resp.status_code}, ready={data.get('ready')!r}, checks={len(data.get('checks') or [])}"
        except Exception as exc:
            latency = int((time.perf_counter() - start) * 1000)
            passed = False
            actual = f"request failed: {exc}"
        return self._emit(
            _make_result(
                "E2E-02",
                "/ready returns valid readiness payload",
                query=None,
                expected="HTTP 200/503 with ready (bool) and checks (list)",
                passed=passed,
                actual=actual,
                latency_ms=latency,
            )
        )

    def _post_chat(self, query: str) -> tuple[int, dict[str, Any] | None, str, int]:
        start = time.perf_counter()
        try:
            resp = self._client.post(
                "/chat",
                json={"query": query},
                headers={"Content-Type": "application/json"},
            )
            latency = int((time.perf_counter() - start) * 1000)
            try:
                body = resp.json()
            except Exception:
                body = None
            return resp.status_code, body if isinstance(body, dict) else None, "", latency
        except Exception as exc:
            latency = int((time.perf_counter() - start) * 1000)
            return 0, None, str(exc), latency

    def check_factual_query(self, query: str, *, check_num: int) -> CheckResult:
        check_id = f"E2E-{2 + check_num:02d}"
        status, body, err, latency = self._post_chat(query)
        if err:
            return self._emit(
                _make_result(
                    check_id,
                    f"Factual query returns compliant factual envelope",
                    query=query,
                    expected="outcome_type=factual, allowlisted citation, <=3 sentences, footer present, no PII",
                    passed=False,
                    actual=f"request failed: {err}",
                    latency_ms=latency,
                )
            )

        assistant = (body or {}).get("assistant") or {}
        outcome = str((body or {}).get("outcome_type") or "")
        body_text = str(assistant.get("body_text") or "").strip()
        citation = str(assistant.get("citation_url") or "").strip()
        footer_line = str(assistant.get("footer_line") or "")
        footer_date = str(assistant.get("footer_date") or "")
        footer_ok = "Last updated from sources:" in footer_line or bool(footer_date.strip())
        sentences = _sentence_count(body_text)

        issues: list[str] = []
        if status != 200:
            issues.append(f"HTTP {status}")
        if outcome != "factual":
            issues.append(f"outcome_type={outcome!r}")
        if not body_text:
            issues.append("empty body_text")
        if sentences > 3:
            issues.append(f"{sentences} sentences (>3)")
        if not is_allowlisted(citation):
            issues.append(f"citation not allowlisted: {citation!r}")
        if not footer_ok:
            issues.append("footer missing 'Last updated from sources:'")
        if body and _contains_pii(body):
            issues.append("PII detected in response")

        passed = not issues
        actual = (
            f"status={status}, outcome_type={outcome!r}, sentences={sentences}, "
            f"citation={citation!r}, footer_line={footer_line!r}"
        )
        if issues:
            actual += f"; issues: {', '.join(issues)}"

        return self._emit(
            _make_result(
                check_id,
                "Factual query returns compliant factual envelope",
                query=query,
                expected="outcome_type=factual, allowlisted citation, <=3 sentences, footer present, no PII",
                passed=passed,
                actual=actual,
                latency_ms=latency,
            )
        )

    def check_refusal_query(self, query: str, *, check_num: int) -> CheckResult:
        check_id = f"E2E-{7 + check_num:02d}"
        status, body, err, latency = self._post_chat(query)
        if err:
            return self._emit(
                _make_result(
                    check_id,
                    "Advisory query returns refusal with allowlisted citation",
                    query=query,
                    expected="outcome_type=refusal, allowlisted citation_url",
                    passed=False,
                    actual=f"request failed: {err}",
                    latency_ms=latency,
                )
            )

        assistant = (body or {}).get("assistant") or {}
        outcome = str((body or {}).get("outcome_type") or "")
        citation = str(assistant.get("citation_url") or "").strip()

        issues: list[str] = []
        if status != 200:
            issues.append(f"HTTP {status}")
        if outcome != "refusal":
            issues.append(f"outcome_type={outcome!r}")
        if not is_allowlisted(citation):
            issues.append(f"citation not allowlisted: {citation!r}")

        passed = not issues
        actual = f"status={status}, outcome_type={outcome!r}, citation={citation!r}"
        if issues:
            actual += f"; issues: {', '.join(issues)}"

        return self._emit(
            _make_result(
                check_id,
                "Advisory query returns refusal with allowlisted citation",
                query=query,
                expected="outcome_type=refusal, allowlisted citation_url",
                passed=passed,
                actual=actual,
                latency_ms=latency,
            )
        )

    def check_comparison_refusal(self) -> CheckResult:
        status, body, err, latency = self._post_chat(COMPARISON_QUERY)
        if err:
            return self._emit(
                _make_result(
                    "E2E-11",
                    "Comparison query returns refusal",
                    query=COMPARISON_QUERY,
                    expected="outcome_type=refusal",
                    passed=False,
                    actual=f"request failed: {err}",
                    latency_ms=latency,
                )
            )

        outcome = str((body or {}).get("outcome_type") or "")
        passed = status == 200 and outcome == "refusal"
        actual = f"status={status}, outcome_type={outcome!r}"
        return self._emit(
            _make_result(
                "E2E-11",
                "Comparison query returns refusal",
                query=COMPARISON_QUERY,
                expected="outcome_type=refusal",
                passed=passed,
                actual=actual,
                latency_ms=latency,
            )
        )

    def check_empty_query(self) -> CheckResult:
        start = time.perf_counter()
        try:
            resp = self._client.post(
                "/chat",
                json={"query": EMPTY_QUERY},
                headers={"Content-Type": "application/json"},
            )
            latency = int((time.perf_counter() - start) * 1000)
            data = resp.json() if resp.content else {}
            error_obj = data.get("error") if isinstance(data, dict) else None
            passed = resp.status_code in (400, 422) and isinstance(error_obj, dict)
            actual = f"status={resp.status_code}, error={error_obj!r}"
        except Exception as exc:
            latency = int((time.perf_counter() - start) * 1000)
            passed = False
            actual = f"request failed: {exc}"

        return self._emit(
            _make_result(
                "E2E-12",
                "Empty query returns validation error",
                query=EMPTY_QUERY,
                expected="HTTP 400/422 with error object",
                passed=passed,
                actual=actual,
                latency_ms=latency,
            )
        )

    def check_pii_query(self) -> CheckResult:
        status, body, err, latency = self._post_chat(PII_QUERY)
        if err:
            return self._emit(
                _make_result(
                    "E2E-13",
                    "PII query refused without echoing PII",
                    query=PII_QUERY,
                    expected="outcome_type=refusal, no PII echoed in response",
                    passed=False,
                    actual=f"request failed: {err}",
                    latency_ms=latency,
                )
            )

        outcome = str((body or {}).get("outcome_type") or "")
        pii_echo = _contains_pii(body)
        passed = status == 200 and outcome == "refusal" and not pii_echo
        actual = f"status={status}, outcome_type={outcome!r}, pii_echo={pii_echo}"
        return self._emit(
            _make_result(
                "E2E-13",
                "PII query refused without echoing PII",
                query=PII_QUERY,
                expected="outcome_type=refusal, no PII echoed in response",
                passed=passed,
                actual=actual,
                latency_ms=latency,
            )
        )
