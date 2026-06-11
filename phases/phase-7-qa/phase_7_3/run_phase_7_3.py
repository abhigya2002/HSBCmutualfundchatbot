"""Phase 7.3 master runner — dashboard, manual QA, go-live, acceptance report."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from phase_7_3.constants import PHASE7_3_ROOT
from phase_7_3.dashboard import generate_dashboard
from phase_7_3.go_live_checklist import generate_go_live_checklist, run_auto_checks
from phase_7_3.live_metrics import (
    collect_live_metrics,
    e2e_score_text,
    load_phase66_report,
    load_phase72_report,
    overall_score_text,
)
from phase_7_3.manual_qa_checklist import generate_manual_qa_checklist

ACCEPTANCE_PATH = PHASE7_3_ROOT / "phase7_acceptance_report.json"


def run_phase_7_3(*, skip_live: bool = False) -> dict:
    p72 = load_phase72_report()
    p66 = load_phase66_report()

    if skip_live:
        live = {
            "health": {"ok": False},
            "ready": {"ok": False},
            "latency": {"average_ms": 0},
            "freshness": {"reachable": 0, "total": 16, "summary": "0/16 URLs reachable"},
        }
    else:
        live = collect_live_metrics()

    dashboard_path = generate_dashboard()
    manual_path = generate_manual_qa_checklist()
    golive_path, golive_meta = generate_go_live_checklist()

    auto_checks, auto_pass, _ = run_auto_checks()
    verdict = golive_meta["verdict"]

    report = {
        "phase": "7.3",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "phase_7_2_score": overall_score_text(p72),
        "phase_6_6_score": e2e_score_text(p66),
        "source_freshness": live.get("freshness", {}).get("summary", "0/16 URLs reachable"),
        "average_latency_ms": int((live.get("latency") or {}).get("average_ms") or 0),
        "auto_checks_passed": auto_pass,
        "go_live_verdict": verdict.replace(" ✅", "").replace(" ❌", "").strip(),
        "dashboard_path": dashboard_path.relative_to(PHASE7_3_ROOT.parent).as_posix(),
        "manual_qa_path": manual_path.relative_to(PHASE7_3_ROOT.parent).as_posix(),
        "go_live_path": golive_path.relative_to(PHASE7_3_ROOT.parent).as_posix(),
        "auto_checks": [
            {"label": c["label"], "passed": c["passed"], "detail": c["detail"]} for c in auto_checks
        ],
        "health_ok": bool((live.get("health") or {}).get("ok")),
        "ready_ok": bool((live.get("ready") or {}).get("ok")),
    }

    ACCEPTANCE_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 7.3 — Dashboard, manual QA, go-live")
    parser.add_argument("--skip-live", action="store_true", help="Skip live API/URL probes")
    args = parser.parse_args(argv)

    report = run_phase_7_3(skip_live=args.skip_live)

    print("Phase 7.3 Complete")
    print(f"Dashboard: {report['dashboard_path']}")
    print(f"Manual QA: {report['manual_qa_path']}")
    print(f"Go-Live: {report['go_live_path']}")
    verdict_display = (
        "READY FOR DEPLOYMENT [OK]" if report["auto_checks_passed"] else report["go_live_verdict"]
    )
    print(f"Verdict: {verdict_display}")
    print(f"Acceptance report: {ACCEPTANCE_PATH.as_posix()}")

    return 0 if report["auto_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
