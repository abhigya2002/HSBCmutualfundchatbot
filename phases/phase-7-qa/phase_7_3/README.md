# Phase 7.3 — Dashboard, Manual QA, and Go-Live Checklist

Self-contained Phase 7 QA acceptance tooling. Reads Phase 7.2 and Phase 6.6 JSON reports from disk (no cross-phase Python imports).

## Prerequisites

Both servers should be running for live probes (health, latency, URL freshness):

```powershell
# API (port 8000)
cd "d:\RAG Chatbot\phases\phase-6-api-ui"
python -m phase_6_2.run_server

# UI (port 3000) — needed for manual QA checklist
cd "d:\RAG Chatbot\phases\phase-6-api-ui\phase_6_5\frontend"
npm run dev
```

Phase 7.2 test report should exist (run test packs first):

```powershell
cd "d:\RAG Chatbot\phases\phase-7-qa"
python -m phase_7_2.run_tests
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Run Phase 7.3

From `phases/phase-7-qa`:

```powershell
python -m phase_7_3.run_phase_7_3
```

Skip live API/URL probes (offline HTML generation only):

```powershell
python -m phase_7_3.run_phase_7_3 --skip-live
```

## Outputs

| File | Description |
|------|-------------|
| `phase_7_3/dashboard.html` | Metrics dashboard with Phase 7.2/6.6 scores and live probes |
| `phase_7_3/manual_qa_checklist.html` | Interactive 27-item manual QA checklist |
| `phase_7_3/go_live_checklist.html` | Auto-verified pre-deploy checks + manual sign-off |
| `phase_7_3/phase7_acceptance_report.json` | Final acceptance rollup |

## Open in browser

Double-click any `.html` file, or:

```powershell
start phase_7_3\dashboard.html
start phase_7_3\manual_qa_checklist.html
start phase_7_3\go_live_checklist.html
```

## Manual QA checklist

1. Open `manual_qa_checklist.html` with the UI running at http://localhost:3000
2. Tick each checkbox as you verify the item
3. Section progress counters update automatically (e.g. "Section A: 3/8 complete")
4. Click **Generate Sign-off** when done — shows completion count and Ready for Go-Live YES/NO

## Go-live verdict

**Auto-verified checks** (from test reports + live probes):

- Phase 7.2 overall ≥ 95%
- Phase 6.6 E2E ≥ 90%
- All 16 Groww URLs reachable (HEAD)
- `/health` and `/ready` OK
- No allowlist violations in Phase 7.2 report
- Average API latency < 5000 ms

**Verdict:**

- `READY FOR DEPLOYMENT ✅` — all auto-checks pass
- `NOT READY ❌ — X items need attention` — one or more auto-checks failed

Manual sign-off items on the go-live page are tracked separately in the browser.

## Folder layout

```
phase_7_3/
├── __init__.py
├── constants.py
├── live_metrics.py
├── dashboard.py
├── manual_qa_checklist.py
├── go_live_checklist.py
├── run_phase_7_3.py
├── dashboard.html              (generated)
├── manual_qa_checklist.html    (generated)
├── go_live_checklist.html      (generated)
├── phase7_acceptance_report.json
└── README.md
```
