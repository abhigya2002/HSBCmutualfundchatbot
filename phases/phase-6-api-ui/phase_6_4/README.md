# Phase 6.4 — Standardized error, refusal, and abstention HTTP payloads

See [API_CONTRACT.md](API_CONTRACT.md) for the full HTTP status policy.

## Modules

| Module | Role |
|--------|------|
| `http_policy.py` | Status code map (400/413/415/429/502/503 vs 200 policy outcomes) |
| `errors.py` | Normalized `ApiError` JSON |
| `handoff_contract.py` | Validates responses against `phase6_generation_handoff.json` |
| `outcome_contract.py` | Refusal types, abstention rules, UI branch hints |
| `responses.py` | `transport_error_response`, `chat_envelope_response` |
| `schemas/openapi.phase6.json` | OpenAPI stub |

## Run

```powershell
python -m phase_6_4.run_contract_eval
python -m unittest discover -s tests -p "test_phase_6_4.py" -v
```

## Tests

Contract tests assert handoff field stability, error shape, refusal/abstention HTTP 200 semantics.
