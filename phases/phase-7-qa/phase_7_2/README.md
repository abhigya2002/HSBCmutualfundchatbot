# Phase 7.2 — Automated Test Packs

Self-contained live `/chat` regression packs. No Phase 1–6 imports — constants and allowlist are copied into `constants.py`.

## Prerequisites

API server running on port 8000:

```powershell
cd "d:\RAG Chatbot\phases\phase-6-api-ui"
python -m phase_6_2.run_server
```

```powershell
cd "d:\RAG Chatbot\phases\phase-7-qa"
pip install -r requirements.txt
```

## Run

```powershell
cd "d:\RAG Chatbot\phases\phase-7-qa"
python -m phase_7_2.run_tests
```

Run a single suite:

```powershell
python -m phase_7_2.test_factual
python -m phase_7_2.test_refusals
python -m phase_7_2.test_edge_cases
```

## Pass bars

| Suite | Cases | Target |
|-------|-------|--------|
| Factual | 30 | >= 90% |
| Refusal | 20 | 100% |
| Edge | 15 | >= 80% |

Results saved to `phase7_2_test_report.json`.

## Folder layout

```
phase_7_2/
├── constants.py        # API URL + 16 allowlisted URLs + helpers
├── test_factual.py     # 30 factual queries
├── test_refusals.py    # 20 refusal queries
├── test_edge_cases.py  # 15 edge cases
├── run_tests.py        # runs all 3 suites
├── phase7_2_test_report.json
└── README.md
```
