# Phase 3.4 — Embedding generation and vector index

**Architecture:** `phase-wise-architecture.md` — Phase 3.4.

## Run

From `phases/phase-3-chunking` (requires Phase 3.3 validated chunks):

```powershell
cd "d:\RAG Chatbot\phases\phase-3-chunking"
python -m phase_3_4.run_embed
```

Options:

- `--config PATH` — chunking JSON config
- `--index-version ID` — pin a specific version string
- `--no-activate` — build without updating `indexes/vector/active.json`

## What it does

1. Loads all indexable chunks from `artifacts/chunks_validated/`.
2. Batch-embeds text via configured provider (default: **`hash_v1`** — local, deterministic, no API key).
3. Persists vectors under `artifacts/embeddings/{index_version}/`.
4. Builds vector index under `artifacts/indexes/vector/{index_version}/`.
5. Updates `artifacts/indexes/vector/active.json` for Phase 4 retrieval (P8-03 rollback = swap pointer).
6. Writes `artifacts/phase3_embedding_build_report.json`.

## Providers

| `embedding.provider` | Description |
|----------------------|-------------|
| `hash_v1` (default) | Offline hash-trick vectors for dev/CI |
| `openai` | OpenAI `/v1/embeddings` (requires `OPENAI_API_KEY`) |

Example OpenAI override in config:

```json
"embedding": {
  "provider": "openai",
  "model_id": "text-embedding-3-small",
  "dimensions": 1536,
  "batch_size": 32
}
```

## Artifacts

| Path | Content |
|------|---------|
| `embeddings/{index_version}/embedding_manifest.json` | Model id, dimensions, count |
| `embeddings/{index_version}/vectors.json` | `chunk_id` → vector |
| `indexes/vector/{index_version}/chunk_records.json` | Full chunk metadata for retrieval |
| `indexes/vector/{index_version}/vector_index_manifest.json` | Index metadata |
| `indexes/vector/active.json` | Active version pointer |

## Code

| Module | Role |
|--------|------|
| [run_embed.py](run_embed.py) | CLI |
| [index_build.py](index_build.py) | Orchestration |
| [vector_store.py](vector_store.py) | Persist + `LocalVectorIndex.search` |
| [providers/](providers/) | Embedding backends |

## Exit codes

- `0` — success
- `1` — build failure (no chunks, context exceeded, provider error)
