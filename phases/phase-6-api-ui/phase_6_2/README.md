# Phase 6.2 — API foundation and request validation

FastAPI skeleton with health/readiness probes and strict inbound validation for `POST /chat` (generation ships in Phase 6.3).

## Run

From `phases/phase-6-api-ui`:

```powershell
pip install -r requirements.txt
python -m phase_6_2.run_server
```

Endpoints:

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| GET | `/ready` | Readiness (indexes + `GenerationService`) |
| POST | `/chat` | Full pipeline → `AnswerEnvelope` JSON |

## Validation (middleware)

- `Content-Type: application/json` only (415 otherwise — P6-03)
- Max body size / max `query` length (413/400 — P6-01)
- Rejects null bytes and invalid UTF-8 (400 — P6-02)
- Rejects forbidden PII fields (`pan`, `aadhaar`, `otp`, … — P6-10)
- Logs `query_length` and latency only — never raw query text

## Tests

```powershell
python -m unittest discover -s tests -p "test_phase_6_2.py" -v
```
