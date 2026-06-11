"""Generate go-live checklist HTML with auto-verified checks (Phase 7.3)."""

from __future__ import annotations

import html
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from phase_7_3.constants import GO_LIVE_THRESHOLDS, PHASE7_3_ROOT, THEME
from phase_7_3.live_metrics import (
    collect_live_metrics,
    has_allowlist_violations,
    load_phase66_report,
    load_phase72_report,
)

OUTPUT_PATH = PHASE7_3_ROOT / "go_live_checklist.html"

MANUAL_ITEMS: tuple[str, ...] = (
    "README is complete and accurate",
    ".env file is NOT committed to git",
    "API key is not hardcoded anywhere",
    "All Phase 1-8 deliverables documented",
    "Known limitations documented",
    "Incident playbooks written",
    "Monitoring alerts configured",
)

RISKS: tuple[tuple[str, str], ...] = (
    (
        "Groww page structure changes → parser breaks",
        "Mitigation: content hash monitoring",
    ),
    (
        "Groq API downtime → extractive fallback active",
        "Mitigation: USE_GROQ=false fallback",
    ),
    (
        "Stale corpus → wrong facts",
        "Mitigation: weekly re-index scheduled",
    ),
)


def _pct_from_report(p72: dict, p66: dict) -> tuple[float, float]:
    o = p72.get("overall") or {}
    p72_total = int(o.get("total") or 0)
    p72_passed = int(o.get("passed") or 0)
    p72_rate = (p72_passed / p72_total * 100) if p72_total else 0.0

    p66_total = int(p66.get("total") or 0)
    p66_passed = int(p66.get("passed") or 0)
    p66_rate = (p66_passed / p66_total * 100) if p66_total else 0.0
    return p72_rate, p66_rate


def run_auto_checks() -> tuple[list[dict], bool, int]:
    p72 = load_phase72_report()
    p66 = load_phase66_report()
    live = collect_live_metrics()

    p72_rate, p66_rate = _pct_from_report(p72, p66)
    freshness = live.get("freshness") or {}
    latency = live.get("latency") or {}
    avg_ms = int(latency.get("average_ms") or 0)

    checks = [
        {
            "id": "phase72",
            "label": f"Phase 7.2 overall score ≥ {GO_LIVE_THRESHOLDS['phase72_min_pct']:.0f}%",
            "passed": p72_rate >= GO_LIVE_THRESHOLDS["phase72_min_pct"],
            "detail": f"{p72_rate:.0f}%",
        },
        {
            "id": "phase66",
            "label": f"Phase 6.6 E2E score ≥ {GO_LIVE_THRESHOLDS['phase66_min_pct']:.0f}%",
            "passed": p66_rate >= GO_LIVE_THRESHOLDS["phase66_min_pct"],
            "detail": f"{p66_rate:.0f}%",
        },
        {
            "id": "urls",
            "label": "All 16 source URLs reachable",
            "passed": freshness.get("reachable", 0) >= freshness.get("total", 16),
            "detail": freshness.get("summary", "0/16"),
        },
        {
            "id": "health",
            "label": "/health returns ok",
            "passed": bool((live.get("health") or {}).get("ok")),
            "detail": (
                str((live.get("health") or {}).get("status_code", "—"))
                if (live.get("health") or {}).get("status_code")
                else str((live.get("health") or {}).get("error", "unreachable"))
            ),
        },
        {
            "id": "ready",
            "label": "/ready returns ok",
            "passed": bool((live.get("ready") or {}).get("ok")),
            "detail": (
                f"ready={(live.get('ready') or {}).get('ready')}"
                if (live.get("ready") or {}).get("status_code")
                else str((live.get("ready") or {}).get("error", "unreachable"))
            ),
        },
        {
            "id": "allowlist",
            "label": "No allowlist violations in test runs",
            "passed": not has_allowlist_violations(p72),
            "detail": "clean" if not has_allowlist_violations(p72) else "violations found",
        },
        {
            "id": "latency",
            "label": f"Average latency < {GO_LIVE_THRESHOLDS['max_avg_latency_ms']}ms",
            "passed": bool(latency.get("api_reachable"))
            and avg_ms > 0
            and avg_ms <= GO_LIVE_THRESHOLDS["max_avg_latency_ms"],
            "detail": (
                f"{avg_ms} ms ({latency.get('samples', 0)} samples)"
                if latency.get("api_reachable")
                else "API unreachable — start server on port 8000"
            ),
        },
    ]

    failed = sum(1 for c in checks if not c["passed"])
    all_pass = failed == 0
    return checks, all_pass, failed


def generate_go_live_checklist(*, output: Path | None = None) -> tuple[Path, dict]:
    out = output or OUTPUT_PATH
    auto_checks, auto_pass, failed_count = run_auto_checks()
    now = datetime.now(timezone.utc).isoformat()

    auto_rows = ""
    for check in auto_checks:
        status = "PASS" if check["passed"] else "FAIL"
        cls = "pass" if check["passed"] else "fail"
        auto_rows += (
            f"<tr><td>{html.escape(check['label'])}</td>"
            f"<td>{html.escape(str(check['detail']))}</td>"
            f"<td><span class='status {cls}'>{status}</span></td></tr>\n"
        )

    manual_html = ""
    for i, item in enumerate(MANUAL_ITEMS):
        manual_html += (
            f'<label class="manual-row">'
            f'<input type="checkbox" id="manual-{i}" onchange="updateVerdict()"/> '
            f"<span>{html.escape(item)}</span></label>\n"
        )

    risks_html = ""
    for i, (risk, mitigation) in enumerate(RISKS, 1):
        risks_html += f"<li><strong>{i}. {html.escape(risk)}</strong> → {html.escape(mitigation)}</li>\n"

    verdict_ready = auto_pass
    verdict_text = "READY FOR DEPLOYMENT ✅" if verdict_ready else f"NOT READY ❌ — {failed_count} items need attention"
    verdict_class = "ready" if verdict_ready else "not-ready"

    meta = {
        "auto_checks_passed": auto_pass,
        "auto_failed_count": failed_count,
        "auto_checks": auto_checks,
        "verdict": verdict_text,
        "generated_at": now,
    }

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Go-Live Checklist</title>
  <style>
    :root {{
      --bg: {THEME["background"]}; --accent: {THEME["accent"]}; --text: {THEME["text"]};
      --muted: {THEME["muted"]}; --card: {THEME["card"]}; --border: {THEME["border"]};
      --success: {THEME["success"]}; --danger: {THEME["danger"]};
    }}
    body {{ font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); padding: 2rem; max-width: 960px; margin: 0 auto; }}
    h1 {{ margin-bottom: 0.25rem; }}
    .verdict {{ font-size: 1.25rem; font-weight: 700; padding: 1rem 1.25rem; border-radius: 12px; margin: 1.5rem 0; text-align: center; }}
    .verdict.ready {{ background: rgba(34,197,94,0.15); border: 2px solid var(--success); color: var(--success); }}
    .verdict.not-ready {{ background: rgba(239,68,68,0.15); border: 2px solid var(--danger); color: var(--danger); }}
    section {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; margin-bottom: 1.25rem; }}
    h2 {{ color: var(--accent); font-size: 1rem; margin-bottom: 0.75rem; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    th, td {{ text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid var(--border); }}
    .status.pass {{ color: var(--success); font-weight: 600; }}
    .status.fail {{ color: var(--danger); font-weight: 600; }}
    .manual-row {{ display: flex; gap: 0.75rem; padding: 0.45rem 0; border-bottom: 1px solid var(--border); cursor: pointer; }}
    .manual-row:last-child {{ border-bottom: none; }}
    input {{ accent-color: var(--accent); width: 16px; height: 16px; }}
    ul {{ padding-left: 1.25rem; }}
    li {{ margin-bottom: 0.5rem; }}
    .meta {{ color: var(--muted); font-size: 0.85rem; }}
  </style>
</head>
<body>
  <h1>Go-Live Checklist</h1>
  <p class="meta">Generated: {html.escape(now)}</p>

  <div class="verdict {verdict_class}" id="verdict">{html.escape(verdict_text)}</div>

  <section>
    <h2>Pre-deployment checks (auto-verified)</h2>
    <table>
      <thead><tr><th>Check</th><th>Result</th><th>Status</th></tr></thead>
      <tbody>{auto_rows}</tbody>
    </table>
  </section>

  <section>
    <h2>Manual sign-off items</h2>
    {manual_html}
  </section>

  <section>
    <h2>Risk assessment</h2>
    <ul>{risks_html}</ul>
  </section>

  <script>
    const autoPass = {'true' if auto_pass else 'false'};
    const autoFailed = {failed_count};
    const manualTotal = {len(MANUAL_ITEMS)};

    function updateVerdict() {{
      const manualDone = document.querySelectorAll('input[type=checkbox]:checked').length;
      const el = document.getElementById('verdict');
      if (autoPass && manualDone === manualTotal) {{
        el.textContent = 'READY FOR DEPLOYMENT ✅';
        el.className = 'verdict ready';
      }} else if (!autoPass) {{
        el.textContent = 'NOT READY ❌ — ' + autoFailed + ' auto-check(s) need attention';
        el.className = 'verdict not-ready';
      }} else {{
        el.textContent = 'NOT READY ❌ — ' + (manualTotal - manualDone) + ' manual item(s) pending';
        el.className = 'verdict not-ready';
      }}
    }}
  </script>
</body>
</html>
"""
    out.write_text(doc, encoding="utf-8")
    return out, meta


if __name__ == "__main__":
    path, _ = generate_go_live_checklist()
    print(f"Go-live checklist written to {path.as_posix()}")
