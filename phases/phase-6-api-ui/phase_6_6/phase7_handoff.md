# Phase 7 Handoff — HSBC Mutual Fund FAQ Assistant

Generated as part of **Phase 6.6** (E2E validation and observability handoff).

---

## 1. System overview

| Component | Location | URL / Port | Version |
|-----------|----------|------------|---------|
| FastAPI backend | `phases/phase-6-api-ui/phase_6_2/` | `http://127.0.0.1:8000` | 6.4.0 |
| Next.js frontend | `phases/phase-6-api-ui/phase_6_5/frontend/` | `http://localhost:3000` | 6.5.0 |
| Generation service | `phases/phase-5-guardrails/phase_5_6/` | (in-process) | 5.6.0 |
| Vector + keyword indexes | Phase 3 artifacts | (on disk) | — |

**Start commands** (from `phases/phase-6-api-ui`):

```powershell
# Terminal 1 — API
python -m phase_6_2.run_server

# Terminal 2 — UI
cd phase_6_5\frontend
npm run dev
```

**Health probes:**

- Liveness: `GET /health` → `{"status":"ok"}`
- Readiness: `GET /ready` → `{"ready": bool, "checks": [...]}`

---

## 2. API contract

### `POST /chat`

**Request** (`Content-Type: application/json`):

```json
{
  "query": "string (required, non-empty, max 2000 chars)",
  "session_id": "string (optional, ephemeral, no PII)"
}
```

**Success response** — HTTP **200** with Phase 5 `AnswerEnvelope` JSON (no field renames):

```json
{
  "outcome_type": "factual | refusal | abstention",
  "query": "...",
  "session_id": "",
  "retrieval_outcome_type": "...",
  "compliance_decision": "...",
  "compliance_reasons": ["..."],
  "validation_passed": true,
  "validation_repaired": false,
  "assistant": {
    "answer_type": "...",
    "body_text": "...",
    "citation_url": "https://groww.in/mutual-funds/...",
    "citation_markdown": "[...](...)",
    "footer_line": "Last updated from sources: ...",
    "footer_date": "...",
    "disclaimer_line": "Facts-only. No investment advice.",
    "display_text": "...",
    "evidence_chunk_id": "...",
    "refusal_type": "",
    "validation_passed": true,
    "validation_repaired": false
  },
  "display_text": "...",
  "audit": { }
}
```

### Outcome types

| `outcome_type` | Meaning | HTTP status |
|----------------|---------|-------------|
| `factual` | Evidence-backed answer (≤3 sentences, one allowlisted citation) | 200 |
| `refusal` | Policy/compliance refusal (advice, comparison, PII, etc.) | 200 |
| `abstention` | Weak or missing evidence; safe fallback | 200 |

Policy outcomes are **never** transport-level HTTP errors.

### Error response shape

Transport / validation failures only:

```json
{
  "error": {
    "code": "empty_query",
    "message": "Field 'query' must not be empty"
  }
}
```

Common codes: `empty_query`, `missing_query`, `invalid_json`, `unsupported_media_type`, `payload_too_large`, `service_unavailable`, `bad_gateway`.

Typical HTTP statuses: **400**, **413**, **415**, **502**, **503**.

---

## 3. Allowlisted HSBC Groww URLs (16)

All rendered citation links must match this list exactly:

1. https://groww.in/mutual-funds/hsbc-india-opportunities-fund-direct-growth
2. https://groww.in/mutual-funds/hsbc-midcap-fund-direct-growth
3. https://groww.in/mutual-funds/hsbc-small-cap-fund-direct-growth
4. https://groww.in/mutual-funds/hsbc-multi-cap-fund-direct-growth
5. https://groww.in/mutual-funds/hsbc-value-fund-direct-growth
6. https://groww.in/mutual-funds/hsbc-large-and-mid-cap-fund-direct-growth
7. https://groww.in/mutual-funds/hsbc-equity-savings-fund-direct-growth
8. https://groww.in/mutual-funds/hsbc-infrastructure-fund-direct-growth
9. https://groww.in/mutual-funds/hsbc-multi-asset-allocation-fund-direct-growth
10. https://groww.in/mutual-funds/hsbc-focused-fund-direct-growth
11. https://groww.in/mutual-funds/hsbc-gold-etf-fof-direct-growth
12. https://groww.in/mutual-funds/hsbc-india-export-opportunities-fund-direct-growth
13. https://groww.in/mutual-funds/hsbc-consumption-fund-direct-growth
14. https://groww.in/mutual-funds/hsbc-medium-duration-fund-direct-growth
15. https://groww.in/mutual-funds/hsbc-dynamic-bond-fund-direct-growth
16. https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth

---

## 4. Log fields for Phase 7 metrics

Emit or aggregate from API request logs (`phase_6_2/request_logging.py`):

| Field | Source | Phase 7 use |
|-------|--------|-------------|
| `latency_ms` | Request middleware timing | p50/p95 API latency SLA |
| `outcome_type` | Chat handler → request.state | Factual vs refusal vs abstention mix |
| `validation_passed` | AnswerEnvelope | Format compliance rate |
| `allowlist_violations` | Post-gen validator / UI renderer | **Target: 0** — alert on any non-allowlisted `citation_url` |
| `query_length` | Validated payload | Abuse / oversized input monitoring |
| `http_status` | Response | Transport error rate (4xx/5xx) |

Recommended derived metrics:

- **Format compliance rate** = responses where `validation_passed=true` AND citation ∈ allowlist
- **Refusal accuracy** = manual QA on refusal query pack vs expected `outcome_type=refusal`
- **Source freshness SLA** = parse `footer_date` / `footer_line` vs crawl timestamps

---

## 5. Known limitations (Phase 6)

- **Stateless sessions** — no transcript persistence; `session_id` is ephemeral only.
- **16-scheme corpus** — only HSBC funds on the 16 Groww URLs above; out-of-scope schemes abstain or refuse.
- **No investment advice** — advisory, comparison, and PII-bearing queries must refuse.
- **ELSS / schemes not in corpus** — factual queries for unknown schemes may return `refusal` or `abstention` instead of `factual`.
- **Live dependency** — E2E validation requires both API and UI servers running locally.
- **UX checks are static HTML** — no browser automation; dynamic chat rendering not verified by Phase 6.6 script alone.

---

## 6. Recommended Phase 7 test focus

1. **Allowed factual matrix** — expense ratio, exit load, minimum SIP, lock-in, riskometer across all 16 schemes.
2. **Refusal matrix** — advice, comparison, PII, non-HSBC funds, ambiguous queries.
3. **Citation integrity** — every `citation_url` matches answered scheme (or agreed refusal default).
4. **Footer freshness** — `Last updated from sources:` date aligns with ingestion metadata.
5. **Format compliance** — ≤3 sentences, single citation, disclaimer present.
6. **Load / latency** — p95 under agreed SLA with Groq generation enabled.
7. **UI E2E** — Playwright/Cypress for chat bubbles, copy button, error toast, mobile breakpoints.

---

## 7. Validation report

Latest automated Phase 6.6 run:

**[phase6_e2e_validation_report.json](./phase6_e2e_validation_report.json)**

Run validation:

```powershell
cd "d:\RAG Chatbot\phases\phase-6-api-ui"
python -m phase_6_6.run_validation
```

---

## UI test hooks (selectors / strings)

| Element | Stable string / selector hint |
|---------|--------------------------------|
| Page title | `HSBC Mutual Fund Assistant` |
| Disclaimer | `Facts-only. No investment advice.` |
| Sample chips | Three fixed factual questions (see `WelcomeScreen.tsx`) |
| Send button | `aria-label="Send message"` |
| Copy button | `aria-label="Copy answer"` |
| Error toast | `role="alert"`, text `Connection Interrupted` |
