# Phase 7.1 — Metrics collection

Measure four core quality metrics against the **live** system. Measurement only — no dashboard UI or acceptance report.

## Prerequisites

- FastAPI backend running: `python -m phase_6_2.run_server` (from `phases/phase-6-api-ui`)
- Phase 4 indexes loaded (`GET /ready` → `ready: true`)
- Python deps: `pip install -r requirements.txt` (from `phases/phase-7-qa-observability`)

## Run

```powershell
cd "d:\RAG Chatbot\phases\phase-7-qa-observability"
python -m phase_7_1.run_metrics
```

Optional:

```powershell
python -m phase_7_1.run_metrics --api-base http://127.0.0.1:8000
$env:PHASE7_API_BASE_URL = "http://127.0.0.1:8000"
```

## Output

`artifacts/metrics/phase7_1_metrics_snapshot.json`

## Four metrics

| Metric | Definition | Key fields |
|--------|------------|------------|
| **Retrieval hit quality** | Labeled factual probes return `factual`, correct scheme citation, evidence chunk, hybrid not skipped | `hit_rate`, `hits`, `total_probes` |
| **Refusal accuracy** | Advisory/comparison/projection probes return `refusal` with allowlisted citation | `accuracy_rate`, `correct`, `total_probes` |
| **Format compliance rate** | Factual responses: ≤3 sentences, one allowlisted citation, footer present, `validation_passed` | `factual_compliance_rate`, `allowlist_violations_total` |
| **Source freshness SLA** | All 16 Groww URLs reachable (HTTP 2xx) and ingestion `fetched_at` within SLA days | `sla_compliance_rate`, `reachable_rate` |

## Configuration

`config/metrics.defaults.json`:

- `api_base_url` — default `http://127.0.0.1:8000`
- `freshness_sla_days` — default `30`
- `paths.retrieval_probes` / `paths.refusal_probes` — benchmark JSON files
- `paths.source_registry` / `paths.metadata_dir` — freshness baselines
- `thresholds.*` — documented targets (informational in 7.1)

## Probe files

| File | Purpose |
|------|---------|
| `benchmarks/retrieval_probes.json` | 10 labeled factual queries |
| `benchmarks/refusal_probes.json` | 8 refusal queries |

## Log fields reused (Phase 6 handoff)

Per `/chat` response: `latency_ms`, `outcome_type`, `validation_passed`, `allowlist_violations` (computed), `audit.evidence_chunk_id`, `audit.hybrid_skipped`.

## Tests

```powershell
python -m unittest discover -s tests -p "test_phase_7_1.py" -v
```

Unit tests cover format checks and allowlist logic (no live API required).
