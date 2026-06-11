"""Orchestrate all Phase 7.1 metrics against the live system."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from phase_7_1.chat_client import ChatClient
from phase_7_1.config_load import load_config, metrics_output_dir, resolve_path
from phase_7_1.metrics_format import measure_format_compliance_rate
from phase_7_1.metrics_freshness import measure_source_freshness_sla
from phase_7_1.metrics_refusal import measure_refusal_accuracy
from phase_7_1.metrics_retrieval import measure_retrieval_hit_quality


MetricFn = Callable[[], dict[str, Any]]


def collect_all_metrics(
    config: dict[str, Any] | None = None,
    *,
    on_metric: Callable[[str, dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    cfg = dict(config or load_config())
    api_base = str(cfg.get("api_base_url") or "http://127.0.0.1:8000")
    timeout = float(cfg.get("request_timeout_seconds") or 60)
    sla_days = float(cfg.get("freshness_sla_days") or 30)
    url_timeout = float(cfg.get("url_probe_timeout_seconds") or 25)

    retrieval_path = resolve_path(cfg, "retrieval_probes")
    refusal_path = resolve_path(cfg, "refusal_probes")
    registry_path = resolve_path(cfg, "source_registry")
    metadata_dir = resolve_path(cfg, "metadata_dir")

    snapshot: dict[str, Any] = {
        "phase": "7.1",
        "snapshot_version": "1.0.0",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "api_base_url": api_base,
        "live_system_required": True,
        "preflight": {},
        "metrics": {},
        "summary": {},
    }

    with ChatClient(api_base, timeout_seconds=timeout) as client:
        snapshot["preflight"] = {
            "health_ok": client.health_ok(),
            "retrieval_probes": retrieval_path.as_posix(),
            "refusal_probes": refusal_path.as_posix(),
        }

        if not snapshot["preflight"]["health_ok"]:
            snapshot["summary"]["error"] = f"API not reachable at {api_base}/health"
            return snapshot

        metric_jobs: list[tuple[str, MetricFn]] = [
            (
                "retrieval_hit_quality",
                lambda: measure_retrieval_hit_quality(client, retrieval_path),
            ),
            (
                "refusal_accuracy",
                lambda: measure_refusal_accuracy(client, refusal_path),
            ),
            (
                "format_compliance_rate",
                lambda: measure_format_compliance_rate(
                    client,
                    retrieval_probes_path=retrieval_path,
                    refusal_probes_path=refusal_path,
                ),
            ),
        ]

        for name, fn in metric_jobs:
            result = fn()
            snapshot["metrics"][name] = result
            if on_metric:
                on_metric(name, result)

    freshness = measure_source_freshness_sla(
        registry_path=registry_path,
        metadata_dir=metadata_dir,
        sla_days=sla_days,
        timeout_seconds=url_timeout,
    )
    snapshot["metrics"]["source_freshness_sla"] = freshness
    if on_metric:
        on_metric("source_freshness_sla", freshness)

    thresholds = dict(cfg.get("thresholds") or {})
    rh = snapshot["metrics"]["retrieval_hit_quality"]["hit_rate"]
    ra = snapshot["metrics"]["refusal_accuracy"]["accuracy_rate"]
    fc = snapshot["metrics"]["format_compliance_rate"]["factual_compliance_rate"]
    sr = snapshot["metrics"]["source_freshness_sla"]["sla_compliance_rate"]

    snapshot["summary"] = {
        "retrieval_hit_quality": rh,
        "refusal_accuracy": ra,
        "format_compliance_rate_factual": fc,
        "source_freshness_sla": sr,
        "allowlist_violations_total": snapshot["metrics"]["format_compliance_rate"].get(
            "allowlist_violations_total", 0
        ),
        "thresholds_met": {
            "retrieval_hit_quality": rh >= float(thresholds.get("retrieval_hit_quality_min", 0.85)),
            "refusal_accuracy": ra >= float(thresholds.get("refusal_accuracy_min", 1.0)),
            "format_compliance": fc >= float(thresholds.get("format_compliance_min", 0.95)),
            "source_freshness_sla": sr >= float(thresholds.get("source_freshness_min", 0.95)),
        },
    }

    return snapshot


def save_snapshot(snapshot: dict[str, Any], config: dict[str, Any] | None = None) -> str:
    cfg = dict(config or load_config())
    out_dir = metrics_output_dir(cfg)
    filename = str(cfg.get("snapshot_filename") or "phase7_1_metrics_snapshot.json")
    path = out_dir / filename
    import json

    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path.as_posix()
