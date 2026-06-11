# Phase 3 — Chunking, embeddings, and index build

**Architecture:** `phase-wise-architecture.md` — Phase 3 (subphases 3.1–3.6).

## Phase 3.1 (implemented)

Workspace, config, and Phase 2 handoff validation — **no chunking or embedding yet**.

```powershell
cd "d:\RAG Chatbot\phases\phase-3-chunking"
python -m phase_3_1.dry_enumerate
```

See [phase_3_1/README.md](phase_3_1/README.md).

## Phase 3.2 (implemented)

Chunk all indexable schemes with `section_sliding_v1` and write `artifacts/chunks/{slug}.chunks.json`.

```powershell
python -m phase_3_2.run_chunk
```

See [phase_3_2/README.md](phase_3_2/README.md).

## Phase 3.3 (implemented)

Validate chunk metadata, dedupe, allowlist gates; write `chunks_validated/` + quality report.

```powershell
python -m phase_3_3.run_validate
```

See [phase_3_3/README.md](phase_3_3/README.md).

## Phase 3.4 (implemented)

Embed validated chunks and build a versioned local vector index.

```powershell
python -m phase_3_4.run_embed
```

See [phase_3_4/README.md](phase_3_4/README.md).

## Chunking library (`chunking/`)

This package defines **chunking strategies** over Phase 2 outputs:

- **Inputs:** normalized Markdown body + Phase 2.6 `clean_document` (`sections` with char offsets), plus provenance from `doc_metadata` / registry (`source_url`, `scheme`, `doc_type`, `effective_date`, `compliance_rank`).
- **Default strategy — `section_sliding_v1`:** build atomic units per section (paragraphs on blank lines; **Markdown tables kept whole** unless they exceed the char budget, in which case they stay a single oversized unit to avoid splitting rows). Pack units into chunks with a **soft max** char budget derived from target token range, then step the window with **tail overlap** in characters (from overlap token range).
- **Token estimates:** `chars / chars_per_token_estimate` (configurable); swap for a real tokenizer later if needed.

## Layout

```text
phase-3-chunking/
  README.md
  config/chunking.defaults.json
  artifacts/           # chunks/, embeddings/, indexes/, logs/ (Phase 3.1+)
  phase_3_1/           # workspace + Phase 2 handoff (dry enumerate)
  phase_3_2/           # chunk + persist bundles
  phase_3_3/           # validate + dedupe for index build
  phase_3_4/           # embeddings + vector index
  chunking/
    contracts.py       # Chunk, ChunkingParams, version tag
    tokenizer.py       # estimate_tokens
    table_units.py     # table spans + atomic units + whitespace splits
    section_sliding.py # section_sliding_v1
    config_load.py     # load JSON + resolve phase2 artifact root
  tests/
```

## Run tests

From this directory (so `chunking` is importable):

```powershell
cd "d:\RAG Chatbot\phases\phase-3-chunking"
python -m unittest discover -s tests -p "test_*.py" -v
```

Optional env: `CHUNKING_CONFIG_PATH` for a custom JSON config.

## Next steps (later Phase 3)

- Embeddings + vector store, keyword index, reproducible build script, and retrieval benchmarks per architecture.
