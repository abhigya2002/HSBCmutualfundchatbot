# Phase 3 indexing artifacts

| Path | Phase | Description |
|------|-------|-------------|
| `indexes/keyword/{index_version}/` | 3.5 | BM25 index + manifest |
| `indexes/keyword/active.json` | 3.5 | Active keyword index pointer |
| `hybrid_retrieval_contract.json` | 3.5 | Phase 4 hybrid merge policy |
| `phase3_keyword_build_report.json` | 3.5 | Build summary |
| `phase3_index_manifest.json` | 3.6 | Rollup manifest (vector + keyword + benchmark) |
| `phase3_retrieval_benchmark_report.json` | 3.6 | Recall@k evaluation |
| `phase4_retrieval_handoff.json` | 3.6 | Phase 4 integration notes |
| `snapshots/` | 3.6 | Pinned config per `index_version` |

Vector index and chunk artifacts live under `phases/phase-3-chunking/artifacts/`.
