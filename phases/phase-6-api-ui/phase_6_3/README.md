# Phase 6.3 — `/chat` and GenerationService integration

Wires `POST /chat` to Phase 5.6 `GenerationService.answer()` and returns `AnswerEnvelope` JSON.

## Integration

Registered from `phase_6_2.app.create_app()` via `phase_6_3.routes.register_chat_routes`.

Flow:

```
InboundValidationMiddleware (6.2)
  → ChatHandler (6.3)
    → GenerationService.answer (5.6)
      → retrieve → compose → validate (5.5)
  → AnswerEnvelope JSON (200)
```

Policy outcomes (`refusal`, `abstention`) return **HTTP 200** with envelope JSON. Upstream failures map to **502/503** without stack traces.

## Smoke client

With server running (`python -m phase_6_2.run_server`):

```powershell
python -m phase_6_3.run_chat --query "expense ratio HSBC Gilt Fund Direct Growth"
python -m phase_6_3.run_chat --query "Should I buy HSBC Gilt Fund?"
```

## Tests

```powershell
python -m unittest discover -s tests -p "test_phase_6_3.py" -v
```
