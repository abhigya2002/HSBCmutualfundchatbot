"""Generate static QA dashboard HTML (Phase 7.3)."""

from __future__ import annotations

import html
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from phase_7_3.constants import PHASE7_3_ROOT, THEME
from phase_7_3.live_metrics import (
    collect_live_metrics,
    e2e_score_text,
    load_phase66_report,
    load_phase72_report,
    overall_score_text,
    suite_pass_rate,
)

OUTPUT_PATH = PHASE7_3_ROOT / "dashboard.html"


def _pct_label(rate: float) -> str:
    return f"{int(round(rate))}%"


def _health_ok(live: dict, p72: dict, p66: dict) -> bool:
    health = live.get("health", {}).get("ok", False)
    ready = live.get("ready", {}).get("ok", False)
    overall = p72.get("overall") or {}
    p72_ok = bool(overall.get("all_pass_bars_met", False))
    p66_ok = int(p66.get("failed") or 0) == 0
    return health and ready and p72_ok and p66_ok


def generate_dashboard(*, output: Path | None = None) -> Path:
    out = output or OUTPUT_PATH
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    p72 = load_phase72_report()
    p66 = load_phase66_report()
    live = collect_live_metrics()

    f_pass, f_total, f_rate = suite_pass_rate(p72, "factual")
    r_pass, r_total, r_rate = suite_pass_rate(p72, "refusal")
    e_pass, e_total, e_rate = suite_pass_rate(p72, "edge_case")
    freshness = live.get("freshness") or {}
    latency = live.get("latency") or {}

    healthy = _health_ok(live, p72, p66)
    status_color = THEME["success"] if healthy else THEME["danger"]
    status_label = "HEALTHY" if healthy else "NEEDS ATTENTION"

    e2e_pass = int(p66.get("passed") or 0)
    e2e_total = int(p66.get("total") or 0)
    e2e_rate = (e2e_pass / e2e_total * 100) if e2e_total else 0

    rows = [
        ("Suite 1 — Factual", f_pass, f_total, f_rate),
        ("Suite 2 — Refusal", r_pass, r_total, r_rate),
        ("Suite 3 — Edge Cases", e_pass, e_total, e_rate),
    ]
    table_rows = "\n".join(
        f"<tr><td>{html.escape(name)}</td>"
        f"<td>{passed}/{total}</td>"
        f"<td><span class='badge'>{_pct_label(rate)}</span></td></tr>"
        for name, passed, total, rate in rows
    )

    url_rows = ""
    for item in (freshness.get("results") or []):
        ok = item.get("ok")
        dot = "ok" if ok else "fail"
        url_rows += (
            f"<tr><td class='url'>{html.escape(str(item.get('url', '')))}</td>"
            f"<td><span class='dot {dot}'></span> {item.get('status_code', '—')}</td></tr>\n"
        )

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>HSBC QA Dashboard</title>
  <style>
    :root {{
      --bg: {THEME["background"]};
      --accent: {THEME["accent"]};
      --text: {THEME["text"]};
      --muted: {THEME["muted"]};
      --card: {THEME["card"]};
      --border: {THEME["border"]};
      --success: {THEME["success"]};
      --danger: {THEME["danger"]};
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); line-height: 1.5; padding: 2rem; }}
    h1 {{ font-size: 1.75rem; margin-bottom: 0.25rem; }}
    .subtitle {{ color: var(--muted); margin-bottom: 1.5rem; }}
    .status-bar {{ display: flex; align-items: center; gap: 0.75rem; margin-bottom: 2rem; padding: 1rem 1.25rem; background: var(--card); border: 1px solid var(--border); border-radius: 12px; }}
    .status-dot {{ width: 14px; height: 14px; border-radius: 50%; background: {status_color}; box-shadow: 0 0 12px {status_color}; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
    .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; }}
    .card h3 {{ font-size: 0.85rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }}
    .card .value {{ font-size: 2rem; font-weight: 700; color: var(--accent); }}
    section {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; margin-bottom: 1.5rem; }}
    section h2 {{ font-size: 1.1rem; margin-bottom: 1rem; color: var(--accent); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    th, td {{ text-align: left; padding: 0.6rem 0.75rem; border-bottom: 1px solid var(--border); }}
    th {{ color: var(--muted); font-weight: 600; }}
    .badge {{ background: var(--accent); color: #fff; padding: 0.15rem 0.5rem; border-radius: 6px; font-size: 0.8rem; }}
    .meta {{ color: var(--muted); font-size: 0.85rem; }}
    .dot {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; }}
    .dot.ok {{ background: var(--success); }}
    .dot.fail {{ background: var(--danger); }}
    td.url {{ font-size: 0.75rem; word-break: break-all; }}
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
    @media (max-width: 768px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <h1>HSBC Mutual Fund Assistant — QA Dashboard</h1>
  <p class="subtitle">Phase 7.3 observability snapshot</p>

  <div class="status-bar">
    <span class="status-dot"></span>
    <strong>Overall health: {html.escape(status_label)}</strong>
    <span class="meta">Last run: {html.escape(now)}</span>
  </div>

  <div class="cards">
    <div class="card"><h3>Retrieval Quality</h3><div class="value">{_pct_label(f_rate)}</div><div class="meta">Phase 7.2 Suite 1 factual</div></div>
    <div class="card"><h3>Refusal Accuracy</h3><div class="value">{_pct_label(r_rate)}</div><div class="meta">Phase 7.2 Suite 2 refusal</div></div>
    <div class="card"><h3>Format Compliance</h3><div class="value">{_pct_label(e_rate)}</div><div class="meta">Phase 7.2 Suite 3 edge</div></div>
    <div class="card"><h3>Source Freshness</h3><div class="value">{freshness.get("reachable", 0)}/{freshness.get("total", 16)}</div><div class="meta">Groww URLs reachable</div></div>
  </div>

  <section>
    <h2>Phase 7.2 Test Pack Results</h2>
    <p class="meta" style="margin-bottom:0.75rem">Overall: {html.escape(overall_score_text(p72))}</p>
    <table>
      <thead><tr><th>Suite</th><th>Score</th><th>Pass Rate</th></tr></thead>
      <tbody>{table_rows}</tbody>
    </table>
  </section>

  <section>
    <h2>Phase 6.6 E2E Validation</h2>
    <p class="meta">Score: {html.escape(e2e_score_text(p66))} &nbsp;|&nbsp; Run: {html.escape(str(p66.get("run_timestamp", "—")))}</p>
    <table>
      <thead><tr><th>Metric</th><th>Value</th></tr></thead>
      <tbody>
        <tr><td>Checks passed</td><td>{e2e_pass}/{e2e_total} ({_pct_label(e2e_rate)})</td></tr>
        <tr><td>Failed checks</td><td>{int(p66.get("failed") or 0)}</td></tr>
      </tbody>
    </table>
  </section>

  <div class="grid-2">
    <section>
      <h2>Live API Status</h2>
      <table>
        <tbody>
          <tr><td>/health</td><td>{'OK' if live.get('health', {}).get('ok') else 'FAIL'}</td></tr>
          <tr><td>/ready</td><td>{'OK' if live.get('ready', {}).get('ok') else 'FAIL'} (ready={live.get('ready', {}).get('ready')})</td></tr>
          <tr><td>Avg latency (5 probes)</td><td>{latency.get('average_ms', 0)} ms</td></tr>
        </tbody>
      </table>
    </section>
    <section>
      <h2>Source URL Reachability</h2>
      <table>
        <thead><tr><th>URL</th><th>Status</th></tr></thead>
        <tbody>{url_rows or "<tr><td colspan='2'>No data</td></tr>"}</tbody>
      </table>
    </section>
  </div>
</body>
</html>
"""
    out.write_text(doc, encoding="utf-8")
    return out


if __name__ == "__main__":
    path = generate_dashboard()
    print(f"Dashboard written to {path.as_posix()}")
