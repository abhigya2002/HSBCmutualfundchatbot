# HSBC Mutual Fund FAQ Assistant

A **facts-only** RAG chatbot for **16 allowlisted HSBC mutual fund scheme pages** on Groww. It answers objective queries (expense ratio, exit load, minimum SIP, lock-in, riskometer, benchmark, statements) and **refuses** advisory, comparison, and out-of-scope questions.

> **Compliance:** No investment advice. One allowlisted citation per response. Closed corpus — URLs come only from [`config/sources.yaml`](config/sources.yaml).

## Features

- FastAPI backend with guardrails (Phases 4–5) and `/chat` API (Phase 6)
- Next.js chat UI with disclaimer, citations, and refusal handling (Phase 6.5)
- Automated test packs and QA dashboard (Phases 7.2–7.3)
- Daily corpus refresh via GitHub Actions (Phase 8)

## Architecture

Phased delivery mirrors [`phase-wise-architecture.md`](phase-wise-architecture.md):

| Phase | Folder | Purpose |
|-------|--------|---------|
| 0–1 | `phases/phase-0-foundation`, `phase-1-corpus-registry` | Scope, policy, 16-url registry |
| 2–3 | `phases/phase-2-ingestion`, `phase-3-chunking`, `phase-3-indexing` | Ingestion, chunking, embeddings |
| 4–5 | `phases/phase-4-retrieval`, `phases/phase-5-guardrails` | Intent, retrieval, generation |
| 6 | `phases/phase-6-api-ui` | API + Next.js UI |
| 7 | `phases/phase-7-qa`, `phase-7-qa-observability` | Test packs, metrics, go-live |
| 8 | `src/mf_faq`, `.github/workflows` | Scheduled corpus refresh |

## Quick start

### Prerequisites

- Python **3.11+**
- Node.js **18+** (for the UI)
- [Groq API key](https://console.groq.com/) (optional; extractive fallback when `USE_GROQ=false`)

### 1. Clone and install

```powershell
cd "d:\RAG Chatbot"

# Root package (ingestion / refresh)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[embed,index]"

# API backend
pip install -r phases\phase-6-api-ui\requirements.txt

# Frontend
cd phases\phase-6-api-ui\phase_6_5\frontend
npm install
cd ..\..\..\..
```

### 2. Configure environment

```powershell
copy .env.example .env
# Edit .env — set GROQ_API_KEY (or USE_GROQ=false)
```

Frontend API URL (optional, defaults to localhost):

```powershell
# phases/phase-6-api-ui/phase_6_5/frontend/.env.local
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

### 3. Run the app

**Terminal 1 — API (port 8000):**

```powershell
cd phases\phase-6-api-ui
python -m phase_6_2.run_server
```

**Terminal 2 — UI (port 3000):**

```powershell
cd phases\phase-6-api-ui\phase_6_5\frontend
npm run dev
```

Open **http://localhost:3000**

Health check: http://127.0.0.1:8000/health

## Project layout

```
RAG Chatbot/
├── config/
│   └── sources.yaml              # 16 allowlisted Groww URLs
├── data/
│   ├── raw/                      # gitignored — fetched HTML
│   ├── processed/                # gitignored — parsed JSON
│   ├── index/manifest.json       # tracked — index metadata
│   └── refresh/content_hashes.json
├── src/mf_faq/                   # Ingestion & daily refresh
├── phases/                       # Phased source (0–8)
├── edge-cases/                   # Per-phase edge-case notes
└── .github/workflows/            # Daily corpus refresh CI
```

## Testing & QA

From `phases/phase-7-qa` (API must be running):

```powershell
pip install -r requirements.txt
python -m phase_7_2.run_tests
python -m phase_7_3.run_phase_7_3
```

Open generated reports in `phases/phase-7-qa/phase_7_3/` (`dashboard.html`, go-live checklist).

Phase 6.6 E2E validation:

```powershell
cd phases\phase-6-api-ui
python -m phase_6_6.run_validation
```

## Corpus refresh

Manual run (compares content hashes, re-indexes changed URLs only):

```powershell
python -m mf_faq.ingestion.refresh
```

Automated: [`.github/workflows/corpus_refresh.yml`](.github/workflows/corpus_refresh.yml) runs daily at 02:00 UTC. Requires `GROQ_API_KEY` in GitHub repository secrets.

## Compliance & policy

- **Closed corpus:** Only URLs in `config/sources.yaml` (16 HSBC Groww scheme pages)
- **Refusal intents:** Advisory, comparison, performance projection, out-of-scope — see `phases/phase-0-foundation/query-policy-matrix.md`
- **No PII:** Queries containing PAN/email are refused; PII is not logged or echoed
- **Redirects:** Allowlisted URL redirects are treated as governance alerts (not followed)

## Building the index (first time)

If vector/keyword indexes are not present locally, build them using the phase pipelines documented under `phases/phase-2-ingestion` through `phases/phase-3-indexing`. Large artifacts under `phases/**/artifacts/` and `data/raw/` are gitignored — rebuild after clone.

## License

Specify your license here (e.g. MIT). This project uses third-party data from public Groww scheme pages; respect Groww terms of use.
