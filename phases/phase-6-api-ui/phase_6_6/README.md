# Phase 6.6 — E2E validation and Phase 7 handoff

Automated end-to-end checks against the live FastAPI backend and Next.js frontend, plus a JSON report artifact and Phase 7 handoff document.

## Prerequisites

Both servers must be running:

```powershell
# Terminal 1 — API (from phases/phase-6-api-ui)
python -m phase_6_2.run_server

# Terminal 2 — UI
cd phase_6_5\frontend
npm run dev
```

Install Python deps (once):

```powershell
pip install -r requirements.txt
```

## Run validation

From `phases/phase-6-api-ui`:

```powershell
python -m phase_6_6.run_validation
```

Optional flags:

```powershell
python -m phase_6_6.run_validation --api-base http://127.0.0.1:8000 --ui-url http://localhost:3000
```

## What each check tests

### Backend (E2E-01 … E2E-13)

| ID | Description |
|----|-------------|
| E2E-01 | `GET /health` → `{"status":"ok"}` |
| E2E-02 | `GET /ready` → valid `ready` + `checks` payload |
| E2E-03–07 | Factual queries: `outcome_type=factual`, non-empty `body_text`, ≤3 sentences, allowlisted citation, footer present, no PII |
| E2E-08–10 | Advisory queries: `outcome_type=refusal`, allowlisted citation |
| E2E-11 | Comparison query → `outcome_type=refusal` |
| E2E-12 | Empty query → HTTP 400/422 with error object |
| E2E-13 | PII query → refusal, no PII echoed in response |

### Frontend (UX-01 … UX-07)

| ID | Description |
|----|-------------|
| UX-01 | Page returns HTTP 200 |
| UX-02 | Contains `HSBC Mutual Fund Assistant` |
| UX-03 | Contains `Facts-only` |
| UX-04 | Contains `No investment advice` |
| UX-05–07 | Each of the 3 sample questions present in HTML |

## Interpreting the report

Output file: **`phase6_e2e_validation_report.json`**

```json
{
  "run_timestamp": "2026-06-09T...",
  "total": 20,
  "passed": 18,
  "failed": 2,
  "pass_rate": "90%",
  "checks": [ { "check_id": "E2E-01", "passed": true, ... } ]
}
```

- **`passed`** — count of checks with `"passed": true`
- **`failed`** — checks needing investigation before Phase 7 QA
- Each check includes **`expected`**, **`actual`**, and **`latency_ms`** for debugging

Exit code: **0** if all checks pass, **1** if any fail.

## Artifacts

| File | Purpose |
|------|---------|
| `phase6_e2e_validation_report.json` | Machine-readable validation results |
| `phase7_handoff.md` | Phase 7 QA/observability handoff document |

## Module layout

```
phase_6_6/
├── __init__.py
├── allowlist.py          # 16 Groww URLs for citation checks
├── check_result.py       # CheckResult dataclass
├── e2e_validator.py      # Backend live checks
├── ux_checklist.py       # Frontend HTML checks (httpx)
├── run_validation.py     # CLI entrypoint
├── phase7_handoff.md
└── README.md
```
