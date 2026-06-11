"""Phase 7.3 constants — self-contained, no cross-phase imports."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

PHASE7_QA_ROOT = Path(__file__).resolve().parents[1]
PHASE7_3_ROOT = Path(__file__).resolve().parent
PHASE72_REPORT_PATH = PHASE7_QA_ROOT / "phase_7_2" / "phase7_2_test_report.json"
PHASE66_REPORT_PATH = (
    PHASE7_QA_ROOT.parent / "phase-6-api-ui" / "phase_6_6" / "phase6_e2e_validation_report.json"
)

API_BASE = "http://127.0.0.1:8000"
HEALTH_URL = f"{API_BASE}/health"
READY_URL = f"{API_BASE}/ready"
CHAT_URL = f"{API_BASE}/chat"
HTTP_TIMEOUT = 15.0
LATENCY_PROBE_TIMEOUT = 30.0

LATENCY_PROBE_QUERIES: tuple[str, ...] = (
    "What is the expense ratio of HSBC Small Cap Fund?",
    "What is the exit load of HSBC Midcap Fund?",
    "What is the minimum SIP for HSBC Gilt Fund?",
    "Should I invest in HSBC Small Cap Fund?",
    "What is the benchmark of HSBC Midcap Fund?",
)

ALLOWLISTED_CITATION_URLS: tuple[str, ...] = (
    "https://groww.in/mutual-funds/hsbc-india-opportunities-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-midcap-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-small-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-multi-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-value-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-large-and-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-equity-savings-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-infrastructure-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-multi-asset-allocation-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-focused-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-gold-etf-fof-direct-growth",
    "https://groww.in/mutual-funds/hsbc-india-export-opportunities-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-consumption-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-medium-duration-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-dynamic-bond-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth",
)

THEME = {
    "background": "#0f1117",
    "accent": "#2563eb",
    "text": "#ffffff",
    "muted": "#6b7280",
    "success": "#22c55e",
    "danger": "#ef4444",
    "warning": "#f59e0b",
    "card": "#1a1d27",
    "border": "#2d3140",
}

GO_LIVE_THRESHOLDS = {
    "phase72_min_pct": 95.0,
    "phase66_min_pct": 90.0,
    "max_avg_latency_ms": 10000,
}

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
HTTP_HEADERS = {"User-Agent": BROWSER_USER_AGENT}
