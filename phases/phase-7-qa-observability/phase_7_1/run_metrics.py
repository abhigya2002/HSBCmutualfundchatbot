"""
Phase 7.1 — Collect live quality metrics (no dashboard).

Run from ``phases/phase-7-qa-observability`` with API server live::

    python -m phase_7_1.run_metrics
    python -m phase_7_1.run_metrics --api-base http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import sys

from phase_7_1.collector import collect_all_metrics, save_snapshot
from phase_7_1.config_load import load_config


def _print_metric(name: str, result: dict) -> None:
    if name == "retrieval_hit_quality":
        print(
            f"  retrieval_hit_quality: {result.get('hits')}/{result.get('total_probes')} "
            f"({result.get('hit_rate_pct')}) avg {result.get('avg_latency_ms')}ms"
        )
    elif name == "refusal_accuracy":
        print(
            f"  refusal_accuracy: {result.get('correct')}/{result.get('total_probes')} "
            f"({result.get('accuracy_rate_pct')})"
        )
    elif name == "format_compliance_rate":
        print(
            f"  format_compliance_rate (factual): {result.get('factual_compliant')}/"
            f"{result.get('factual_responses')} ({result.get('factual_compliance_rate_pct')}) "
            f"allowlist_violations={result.get('allowlist_violations_total')}"
        )
    elif name == "source_freshness_sla":
        print(
            f"  source_freshness_sla: {result.get('sla_ok_count')}/{result.get('total_urls')} "
            f"({result.get('sla_compliance_rate_pct')}) reachable={result.get('reachable_rate_pct')}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 7.1 live metrics collection.")
    parser.add_argument("--config", default=None, help="Path to metrics.defaults.json")
    parser.add_argument("--api-base", default=None, help="Override API base URL")
    args = parser.parse_args(argv)

    cfg = load_config()
    if args.api_base:
        cfg["api_base_url"] = args.api_base.strip()

    print(f"Phase 7.1 metrics — API {cfg.get('api_base_url')}\n")

    snapshot = collect_all_metrics(cfg, on_metric=_print_metric)

    if snapshot.get("summary", {}).get("error"):
        print(f"\nERROR: {snapshot['summary']['error']}")
        return 1

    out_path = save_snapshot(snapshot, cfg)
    summary = snapshot.get("summary") or {}

    print("\nSummary:")
    print(f"  retrieval_hit_quality:     {summary.get('retrieval_hit_quality')}")
    print(f"  refusal_accuracy:          {summary.get('refusal_accuracy')}")
    print(f"  format_compliance (fact):  {summary.get('format_compliance_rate_factual')}")
    print(f"  source_freshness_sla:      {summary.get('source_freshness_sla')}")
    print(f"  allowlist_violations:      {summary.get('allowlist_violations_total')}")
    print(f"\nSnapshot saved to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
