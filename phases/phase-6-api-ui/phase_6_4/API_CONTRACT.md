# Phase 6.4 — HTTP error and outcome payload contracts

## HTTP status policy

| Situation | HTTP | Body |
|-----------|------|------|
| Factual / refusal / abstention answer | **200** | `AnswerEnvelope` JSON |
| Client validation (bad JSON, missing query, PII fields) | **400** | `ApiError` |
| Body too large | **413** | `ApiError` |
| Wrong `Content-Type` | **415** | `ApiError` |
| Rate limit (optional) | **429** | `ApiError` |
| Unexpected upstream failure | **502** | `ApiError` |
| Timeout / indexes unavailable | **503** | `ApiError` |

Policy outcomes (`outcome_type=refusal|abstention`) are **not** HTTP errors.

## ApiError shape

```json
{
  "error": {
    "code": "unsupported_media_type",
    "message": "Content-Type must be application/json"
  }
}
```

No stack traces or internal exception strings in `message`.

## Refusal UI branching

When `outcome_type=refusal`, use `assistant.refusal_type`:

| `refusal_type` | Meaning |
|----------------|---------|
| `advisory` | Investment advice request |
| `comparison` | Fund comparison |
| `mixed_intent` | Mixed factual + prohibited |
| `out_of_scope` | Non-HSBC / off-topic |
| `disambiguate` | Ambiguous scheme |
| `performance_info` | Performance-only (limited factual path) |

Branch hint helper: `outcome_contract.ui_branch(envelope)` (not added to response body).

## Abstention

When `outcome_type=abstention`:

- Weak/missing evidence copy in `display_text`
- `citation_url` when present must be one of the **16** allowlisted Groww URLs
- Default fallback citation (no scheme resolved): HSBC Multi Cap Fund direct growth URL

## validation_passed=false

Still HTTP **200**. Render `display_text` / `assistant.display_text` only — never raw pre-validator draft text.

## Run contract eval

```powershell
python -m phase_6_4.run_contract_eval
```

## OpenAPI stub

`schemas/openapi.phase6.json`
