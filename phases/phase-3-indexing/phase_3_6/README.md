# Phase 3.6 — Reproducible index build, benchmarks, and Phase 4 handoff

**Architecture:** `phase-wise-architecture.md` — Phase 3.6.

## Run

From `phases/phase-3-indexing`:

```powershell
cd "d:\RAG Chatbot\phases\phase-3-indexing"
python -m phase_3_6.run_build_all
```

### Modes

| Flag | Behavior |
|------|----------|
| (default) | Run **3.2 → 3.3 → 3.4 → 3.5** in `phase-3-chunking` / `phase-3-indexing`, then benchmark |
| `--eval-only` | Skip pipeline; evaluate **active** vector + keyword indexes |
| `--allow-partial` | Continue if fewer than 16 schemes are indexable |
| `--index-version ID` | Pin version for embed + keyword steps |

## What it does

1. Assigns shared `index_version` (config fingerprint + timestamp).
2. Orchestrates chunk → validate → embed → keyword index (subprocess to sibling packages).
3. Snapshots config to `artifacts/snapshots/{index_version}_config.json`.
4. Runs [benchmarks/retrieval_benchmark.json](../benchmarks/retrieval_benchmark.json) (12 factual queries, A1–A7).
5. Computes **recall@k** (default k=5, threshold=0.5) via hybrid vector + BM25 search.
6. Writes:
   - `artifacts/phase3_index_manifest.json`
   - `artifacts/phase3_retrieval_benchmark_report.json`
   - `artifacts/phase4_retrieval_handoff.json`

## Exit codes

- `0` — pipeline OK, benchmark passed, full corpus (or `--allow-partial`)
- `1` — step failure, benchmark below threshold, or partial corpus without flag
