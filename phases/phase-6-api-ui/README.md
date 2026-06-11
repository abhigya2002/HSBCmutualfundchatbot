# Phase 6 — API and UI experience

**Architecture:** `phase-wise-architecture.md` (Phase 6).

## Subphases

| Subphase | Folder | CLI |
|----------|--------|-----|
| 6.1 | `phase_6_1/` | `python -m phase_6_1.dry_load` |
| 6.2 | `phase_6_2/` | `python -m phase_6_2.run_server` |
| 6.3 | `phase_6_3/` | `POST /chat` + `python -m phase_6_3.run_chat` |
| 6.4 | `phase_6_4/` | `python -m phase_6_4.run_contract_eval` |
| 6.5 | `phase_6_5/frontend/` | `npm run dev` (Next.js UI) |
| 6.6 | (planned) | E2E validation |

Run all Phase 6 work from:

```powershell
cd "d:\RAG Chatbot\phases\phase-6-api-ui"
```

## Phase 6.1 — Done

- Workspace layout: `config/`, `api/`, `ui/`, `artifacts/`, `tests/`
- Loads `phase6_generation_handoff.json` from Phase 5.6
- Pins server, validation, CORS, and log-redaction config
- Instantiates `GenerationService` (no HTTP traffic)
- Reports Groq env status via Phase 5.4 (read-only)

## Phase 6.3 — Done

- `POST /chat` → `GenerationService.answer()` → `AnswerEnvelope` JSON (HTTP 200)
- Timeout + 502/503 error mapping (no stack traces to clients)
- Request logging includes `outcome_type` and `validation_passed`

```powershell
python -m phase_6_2.run_server
python -m phase_6_3.run_chat --query "expense ratio HSBC Gilt Fund Direct Growth"
```

## Phase 6.4 — Done

- HTTP status policy: policy outcomes → **200**; transport errors → 400/413/415/502/503
- Normalized `ApiError` JSON (no stack traces)
- Refusal/abstention contracts + handoff field validation
- OpenAPI stub: `phase_6_4/schemas/openapi.phase6.json`

```powershell
python -m phase_6_4.run_contract_eval
```

## Phase 6.5 — Done

Next.js 14 chat UI at `phase_6_5/frontend/`:

```powershell
cd "d:\RAG Chatbot\phases\phase-6-api-ui\phase_6_5\frontend"
npm install
npm run dev
```

## Planned (6.6)

| Artifact | Description |
|----------|-------------|
| Backend API | `POST /chat`, request validation, guardrail middleware |
| Frontend | Disclaimer, sample questions, citation rendering |
| Session policy | Stateless / ephemeral; no PII in logs |

## Edge cases

See [edge-cases/phase-6.md](../../edge-cases/phase-6.md).

## Tests

```powershell
python -m unittest discover -s tests -p "test_phase_6_*.py" -v
```
