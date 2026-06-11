# Phase 7 — Observability, QA, and acceptance testing

**Architecture:** `phase-wise-architecture.md` (Phase 7).

## Subphases

| Subphase | Folder | Status |
|----------|--------|--------|
| 7.1 Metrics collection | `phase_7_1/` | Implemented |
| 7.2 Automated test packs | `phase_7_2/` | Planned |
| 7.3 Dashboard, manual QA, go-live | `phase_7_3/` | Planned |

## Phase 7.1 — Run metrics

```powershell
cd "d:\RAG Chatbot\phases\phase-7-qa-observability"
pip install -r requirements.txt
python -m phase_6_2.run_server   # from phase-6-api-ui, separate terminal
python -m phase_7_1.run_metrics
```

Output: `artifacts/metrics/phase7_1_metrics_snapshot.json`

See [phase_7_1/README.md](phase_7_1/README.md) for metric definitions.

## Tests

```powershell
python -m unittest discover -s tests -p "test_phase_7_1.py" -v
```

## Edge cases

See [edge-cases/phase-7.md](../../edge-cases/phase-7.md).
