"""Source freshness SLA metric (Phase 7.1)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from phase_7_1.allowlist import ALLOWLISTED_URLS, normalize_url


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        text = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _load_registry_urls(registry_path: Path) -> list[dict[str, str]]:
    if not registry_path.is_file():
        return [{"url": u, "scheme": urlparse(u).path.split("/")[-1]} for u in ALLOWLISTED_URLS]
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    rows: list[dict[str, str]] = []
    for entry in data.get("entries") or []:
        url = str(entry.get("url") or "")
        scheme = str(entry.get("scheme") or urlparse(url).path.split("/")[-1])
        if url:
            rows.append({"url": url, "scheme": scheme})
    return rows


def _ingestion_fetched_at(metadata_dir: Path, scheme: str) -> str | None:
    meta_path = metadata_dir / f"{scheme}.json"
    if not meta_path.is_file():
        return None
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        return str(data.get("fetched_at") or "") or None
    except Exception:
        return None


def measure_source_freshness_sla(
    *,
    registry_path: Path,
    metadata_dir: Path,
    sla_days: float,
    timeout_seconds: float = 25.0,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    rows: list[dict[str, Any]] = []
    reachable = 0
    fresh = 0
    allowlisted_final = 0

    with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
        for entry in _load_registry_urls(registry_path):
            url = normalize_url(entry["url"])
            scheme = entry["scheme"]
            row: dict[str, Any] = {"scheme": scheme, "url": url}

            fetched_at_raw = _ingestion_fetched_at(metadata_dir, scheme)
            fetched_at = _parse_ts(fetched_at_raw)
            row["ingestion_fetched_at"] = fetched_at_raw

            if fetched_at:
                age_days = (now - fetched_at).total_seconds() / 86400.0
                row["ingestion_age_days"] = round(age_days, 2)
                row["ingestion_fresh"] = age_days <= sla_days
            else:
                row["ingestion_age_days"] = None
                row["ingestion_fresh"] = False

            try:
                resp = client.get(url)
                final_url = normalize_url(str(resp.url))
                row["http_status"] = resp.status_code
                row["reachable"] = 200 <= resp.status_code < 300
                row["final_url"] = final_url
                row["final_url_allowlisted"] = final_url in {normalize_url(u) for u in ALLOWLISTED_URLS}
            except Exception as exc:
                row["http_status"] = 0
                row["reachable"] = False
                row["final_url"] = None
                row["final_url_allowlisted"] = False
                row["error"] = str(exc)

            if row["reachable"]:
                reachable += 1
            if row.get("ingestion_fresh"):
                fresh += 1
            if row.get("final_url_allowlisted"):
                allowlisted_final += 1

            row["sla_ok"] = bool(row["reachable"] and row.get("ingestion_fresh") and row.get("final_url_allowlisted"))
            rows.append(row)

    total = len(rows)
    reachable_rate = round(reachable / total, 4) if total else 0.0
    fresh_rate = round(fresh / total, 4) if total else 0.0
    sla_ok_count = sum(1 for r in rows if r.get("sla_ok"))
    sla_rate = round(sla_ok_count / total, 4) if total else 0.0

    return {
        "metric": "source_freshness_sla",
        "description": "Reachability and ingestion freshness for all 16 allowlisted Groww URLs",
        "sla_max_days": sla_days,
        "total_urls": total,
        "reachable_count": reachable,
        "reachable_rate": reachable_rate,
        "reachable_rate_pct": f"{int(round(reachable_rate * 100))}%",
        "ingestion_fresh_count": fresh,
        "ingestion_fresh_rate": fresh_rate,
        "ingestion_fresh_rate_pct": f"{int(round(fresh_rate * 100))}%",
        "final_url_allowlisted_count": allowlisted_final,
        "sla_ok_count": sla_ok_count,
        "sla_compliance_rate": sla_rate,
        "sla_compliance_rate_pct": f"{int(round(sla_rate * 100))}%",
        "urls": rows,
    }
