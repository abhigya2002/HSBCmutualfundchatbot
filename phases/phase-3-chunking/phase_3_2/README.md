# Phase 3.2 — Chunking strategies and chunk artifacts

**Architecture:** `phase-wise-architecture.md` — Phase 3.2.

## Run

From `phases/phase-3-chunking`:

```powershell
cd "d:\RAG Chatbot\phases\phase-3-chunking"
python -m phase_3_2.run_chunk
```

Options:

- `--scheme SLUG` — chunk one scheme only
- `--config PATH` — override `config/chunking.defaults.json`
- `--skip-handoff` — bypass Phase 3.1 indexability gate (not recommended)

## What it does

1. Re-validates Phase 2 handoff (Phase 3.1 rules) for each registry entry.
2. Loads Markdown body + `clean_document` + `doc_metadata` per indexable scheme.
3. Chunks with **`section_sliding_v1`** (table-safe, section offsets, token budget + overlap).
4. Writes `artifacts/chunks/{slug}.chunks.json` per scheme.
5. Writes `artifacts/phase3_chunk_manifest.json` corpus summary.

Does **not** embed or build vector/keyword indexes (Phase 3.4–3.5).

## Chunk bundle shape

Each `{slug}.chunks.json` includes:

- `chunk_strategy_version`, `strategy`, `body_sha256`, `chunk_count`
- `chunks[]`: `chunk_id`, `text`, `start_char`, `end_char`, `source_url`, `scheme`, `section_title`, …

## Code

| Module | Role |
|--------|------|
| [run_chunk.py](run_chunk.py) | CLI |
| [load.py](load.py) | Phase 2 inputs |
| [chunk_scheme.py](chunk_scheme.py) | `section_sliding_v1` wrapper |
| [persist.py](persist.py) | JSON bundle writer |
| [paths.py](paths.py) | Output paths |

Chunking algorithm: [`../chunking/section_sliding.py`](../chunking/section_sliding.py).

## Exit codes

- `0` — at least one scheme chunked successfully, no per-scheme errors
- `1` — failures or zero successes
- `2` — unknown `--scheme`
