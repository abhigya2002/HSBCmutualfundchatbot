# Phase 3 — Indexing (keyword + hybrid handoff)

**Architecture:** `phase-wise-architecture.md` — Phase 3.5–3.6.

Chunking, embedding, and vector index: [`../phase-3-chunking/`](../phase-3-chunking/).

## Phase 3.5 (implemented)

BM25 keyword index over the same chunks as Phase 3.4.

```powershell
cd "d:\RAG Chatbot\phases\phase-3-indexing"
python -m phase_3_5.run_keyword_index
```

See [phase_3_5/README.md](phase_3_5/README.md).

## Phase 3.6 (implemented)

One-command pipeline (3.2→3.5), retrieval benchmark, Phase 4 handoff.

```powershell
python -m phase_3_6.run_build_all --eval-only
```

Full rebuild (slow; re-chunks and re-embeds):

```powershell
python -m phase_3_6.run_build_all
```

See [phase_3_6/README.md](phase_3_6/README.md).

## Layout

```text
phase-3-indexing/
  config/indexing.defaults.json
  phase_3_5/
  phase_3_6/
  benchmarks/retrieval_benchmark.json
  artifacts/
  tests/
```

## Tests

```powershell
cd "d:\RAG Chatbot\phases\phase-3-indexing"
python -m unittest discover -s tests -p "test_*.py" -v
```
