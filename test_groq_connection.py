"""
Standalone Groq connectivity diagnostic for the Mutual Fund FAQ RAG project.

Run from the project root::

    python test_groq_connection.py
"""

from __future__ import annotations

import importlib.metadata
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"
PHASE5_ROOT = PROJECT_ROOT / "phases" / "phase-5-guardrails"
PLACEHOLDER_KEY = "your_groq_api_key_here"
GROQ_MODEL = "llama-3.1-8b-instant"
PING_MESSAGE = "Reply with exactly one word: connected"

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def sentence_count(text: str) -> int:
    stripped = text.strip()
    if not stripped:
        return 0
    parts = [p for p in _SENTENCE_SPLIT.split(stripped) if p.strip()]
    return len(parts) if parts else 1


def print_check_header(name: str) -> None:
    print(f"\n{'=' * 60}")
    print(name)
    print("=" * 60)


def check_env_loading() -> tuple[bool, list[str]]:
    print_check_header("CHECK 1 - ENV LOADING")
    issues: list[str] = []

    if not ENV_PATH.is_file():
        issues.append(f".env not found at {ENV_PATH}")
        print(f"FAIL — .env not found at {ENV_PATH}")
        return False, issues

    print(f"PASS — .env found at {ENV_PATH}")
    loaded = load_dotenv(ENV_PATH, override=True)
    if not loaded:
        print("WARN — load_dotenv returned False (file may be empty)")
    else:
        print("PASS — .env loaded successfully")

    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        issues.append("GROQ_API_KEY is missing or empty")
        print("FAIL — GROQ_API_KEY is missing or empty")
    elif api_key == PLACEHOLDER_KEY:
        issues.append("GROQ_API_KEY is still the placeholder value")
        print('FAIL — GROQ_API_KEY is still the placeholder "your_groq_api_key_here"')
    else:
        masked = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
        print(f"PASS — GROQ_API_KEY is set ({masked})")

    use_groq = os.environ.get("USE_GROQ", "").strip().lower()
    if use_groq == "true":
        print('PASS — USE_GROQ is set to "true"')
    else:
        issues.append(f'USE_GROQ is "{os.environ.get("USE_GROQ", "")}" (expected "true")')
        print(f'FAIL — USE_GROQ is "{os.environ.get("USE_GROQ", "")}" (expected "true")')

    passed = len(issues) == 0
    if passed:
        print("CHECK 1 RESULT: PASS")
    else:
        print("CHECK 1 RESULT: FAIL")
    return passed, issues


def check_groq_package() -> tuple[bool, list[str]]:
    print_check_header("CHECK 2 - GROQ PACKAGE")
    issues: list[str] = []

    try:
        import groq  # noqa: F401
    except ImportError as exc:
        issues.append(f"groq import failed: {exc}")
        print(f"FAIL — groq package is not installed: {exc}")
        print("CHECK 2 RESULT: FAIL")
        return False, issues

    print("PASS — groq package is importable")
    try:
        version = importlib.metadata.version("groq")
        print(f"PASS — groq version: {version}")
    except importlib.metadata.PackageNotFoundError:
        issues.append("groq version could not be determined")
        print("FAIL — groq is importable but version metadata is unavailable")

    passed = len(issues) == 0
    print(f"CHECK 2 RESULT: {'PASS' if passed else 'FAIL'}")
    return passed, issues


def check_api_connection() -> tuple[bool, list[str]]:
    print_check_header("CHECK 3 - API CONNECTION")
    issues: list[str] = []

    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key or api_key == PLACEHOLDER_KEY:
        issues.append("Cannot test API without a valid GROQ_API_KEY")
        print("FAIL — Skipping live call: GROQ_API_KEY is missing or placeholder")
        print("CHECK 3 RESULT: FAIL")
        return False, issues

    try:
        from groq import Groq

        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": PING_MESSAGE}],
            temperature=0.1,
            max_tokens=20,
        )
        text = (response.choices[0].message.content or "").strip()
        if not text:
            issues.append("Groq returned an empty response")
            print("FAIL — Groq returned an empty response")
            print("CHECK 3 RESULT: FAIL")
            return False, issues

        print("PASS — Groq API call succeeded")
        print(f"Response: {text!r}")
        print("CHECK 3 RESULT: PASS")
        return True, issues
    except Exception as exc:
        issues.append(str(exc))
        print(f"FAIL — Groq API call failed: {exc}")
        print("CHECK 3 RESULT: FAIL")
        return False, issues


def check_phase54_integration() -> tuple[bool, list[str]]:
    print_check_header("CHECK 4 - PHASE 5.4 INTEGRATION")
    issues: list[str] = []

    if not PHASE5_ROOT.is_dir():
        issues.append(f"Phase 5 guardrails folder not found: {PHASE5_ROOT}")
        print(f"FAIL — {PHASE5_ROOT} not found")
        print("CHECK 4 RESULT: FAIL")
        return False, issues

    phase5_str = str(PHASE5_ROOT)
    if phase5_str not in sys.path:
        sys.path.insert(0, phase5_str)

    try:
        from phase_5_4 import groq_composer
        from phase_5_4.env_config import groq_composer_enabled
    except ImportError as exc:
        issues.append(f"Phase 5.4 import failed: {exc}")
        print(f"FAIL — Could not import Phase 5.4 modules: {exc}")
        print("CHECK 4 RESULT: FAIL")
        return False, issues

    print("PASS — Imported phase_5_4.groq_composer and env_config")

    enabled = groq_composer_enabled()
    if enabled:
        print("PASS — groq_composer_enabled() returned True")
    else:
        issues.append("groq_composer_enabled() returned False")
        print("FAIL — groq_composer_enabled() returned False")

    chunk_text = (
        "The exit load for HSBC Small Cap Fund is 1% if redeemed within 1 year."
    )
    citation_url = "https://groww.in/mutual-funds/hsbc-small-cap-fund-direct-growth"
    section_title = "Exit Load"
    effective_date = "2026-01-01"
    query = "What is the exit load for HSBC Small Cap Fund?"

    print(f"Input chunk_text: {chunk_text!r}")
    print(f"Input citation_url: {citation_url}")
    print(f"Input section_title: {section_title!r}")
    print(f"Input effective_date: {effective_date!r}")

    if not enabled:
        issues.append("Cannot compose via Groq when groq_composer_enabled() is False")
        print("FAIL — Skipping compose_body_with_groq (Groq not enabled)")
        print("CHECK 4 RESULT: FAIL")
        return False, issues

    try:
        body_text = groq_composer.compose_body_with_groq(
            query=query,
            chunk_text=chunk_text,
            max_sentences=3,
        )
    except Exception as exc:
        issues.append(f"compose_body_with_groq failed: {exc}")
        print(f"FAIL — compose_body_with_groq raised: {exc}")
        print("CHECK 4 RESULT: FAIL")
        return False, issues

    print(f"Composed body_text: {body_text!r}")

    if not body_text.strip():
        issues.append("body_text is empty")
        print("FAIL — body_text is empty")
    else:
        print("PASS — body_text is not empty")

    count = sentence_count(body_text)
    if count <= 3:
        print(f"PASS — body_text is {count} sentence(s) (<= 3)")
    else:
        issues.append(f"body_text has {count} sentences (expected <= 3)")
        print(f"FAIL — body_text has {count} sentences (expected <= 3)")

    passed = len(issues) == 0
    print(f"CHECK 4 RESULT: {'PASS' if passed else 'FAIL'}")
    return passed, issues


def main() -> int:
    print("Groq connection diagnostic — Mutual Fund FAQ RAG")
    print(f"Project root: {PROJECT_ROOT}")

    results = [
        check_env_loading()[0],
        check_groq_package()[0],
        check_api_connection()[0],
        check_phase54_integration()[0],
    ]

    passed_count = sum(results)
    total = len(results)

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print("=" * 60)
    if passed_count == total:
        print("All checks passed - Groq is ready")
        return 0
    print(f"{passed_count}/{total} checks passed - see failures above")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
