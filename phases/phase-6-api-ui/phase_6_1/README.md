# Phase 6.1 — Workspace, configuration, and Phase 5 handoff

Validates API/UI workspace layout, runtime config, `phase6_generation_handoff.json` from Phase 5.6, and `GenerationService` import/instantiation (no HTTP server).

## Run

From `phases/phase-6-api-ui`:

```powershell
cd "d:\RAG Chatbot\phases\phase-6-api-ui"
python -m phase_6_1.dry_load
```

## Configuration

| File | Purpose |
|------|---------|
| `config/api.defaults.json` | Server bind, validation limits, CORS, logging redaction |
| `../phase-5-guardrails/artifacts/service/phase6_generation_handoff.json` | Phase 5.6 API contract |

## Environment

| Variable | Purpose |
|----------|---------|
| `API_UI_CONFIG_PATH` | Override config JSON |
| `PHASE6_ARTIFACT_ROOT` | Override `artifacts/` root |
| `PHASE5_GUARDRAILS_ROOT` | Override Phase 5 workspace path |
| Project-root `.env` | Groq flags (`USE_GROQ`, `GROQ_API_KEY`) — read-only via Phase 5.4 |

## Outputs

| File | Description |
|------|-------------|
| `artifacts/phase6_1_dry_manifest.json` | Readiness for Phase 6.2 |
| `artifacts/phase6_1_handoff_validation.json` | Validation snapshot |

## Tests

```powershell
python -m unittest discover -s tests -p "test_phase_6_1.py" -v
```
