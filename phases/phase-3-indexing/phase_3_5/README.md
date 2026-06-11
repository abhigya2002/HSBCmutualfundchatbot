# Phase 3.5 — Keyword index for hybrid retrieval

**Architecture:** `phase-wise-architecture.md` — Phase 3.5.

## Run

From `phases/phase-3-indexing` (requires Phase 3.4 vector index in `phase-3-chunking`):

```powershell
cd "d:\RAG Chatbot\phases\phase-3-indexing"
python -m phase_3_5.run_keyword_index
```

## What it does

1. Reads chunk records from the **active** Phase 3.4 vector index (`phase-3-chunking/artifacts/indexes/vector/active.json`).
2. Builds a **BM25** inverted index over the same chunks (keyword text normalized for ₹ / `%` only — P3-06).
3. Expands facet phrases (`exit load`, `riskometer`, etc.) in the keyword channel only.
4. Writes `artifacts/indexes/keyword/{index_version}/bm25_index.json` + manifest.
5. Updates `artifacts/indexes/keyword/active.json` and `artifacts/hybrid_retrieval_contract.json` for Phase 4.

## Hybrid contract (Phase 4)

`hybrid_retrieval_contract.json` documents:

- Shared merge keys: `chunk_id`, `source_url`, `scheme`
- `keyword_empty_fallback`: `vector` when BM25 returns no hits (e.g. stopword-only queries — P3-12)
- Scheme aliases: **query-side only** (P3-07)

## Code

| Module | Role |
|--------|------|
| [run_keyword_index.py](run_keyword_index.py) | CLI |
| [bm25.py](bm25.py) | BM25 index + search |
| [normalize.py](normalize.py) | Keyword-channel normalization |
| [load_chunks.py](load_chunks.py) | Load from Phase 3.4 chunk records |
| [hybrid_contract.py](hybrid_contract.py) | Phase 4 handoff JSON |
