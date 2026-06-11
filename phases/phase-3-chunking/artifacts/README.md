# Phase 3 artifacts

| Directory | Purpose |
|-----------|---------|
| `chunks/` | `{slug}.chunks.json` per scheme (**Phase 3.2**) |
| `chunks_validated/` | validated bundles for embedding (**Phase 3.3**) |
| `embeddings/{index_version}/` | Vectors + embedding manifest (**Phase 3.4**) |
| `indexes/vector/{index_version}/` | Chunk records + index manifest (**Phase 3.4**) |
| `indexes/vector/active.json` | Active index version pointer (**Phase 3.4**) |
| `indexes/` | Keyword index (**Phase 3.5+**) |
| `logs/` | Index-build logs |

Reports from Phase 3.1 (gitignored by default):

- `phase3_1_dry_manifest.json` — dry enumeration + handoff status per scheme
- `phase3_handoff_report.json` — summary for Phase 3.2 entry

Phase 3.2 reports (gitignored by default):

- `phase3_chunk_manifest.json` — corpus chunk build summary
- `phase3_validated_manifest.json` — indexable schemes/chunks (**Phase 3.3**)
- `phase3_index_build_quality_report.json` — validation + dedupe report (**Phase 3.3**)
- `phase3_embedding_build_report.json` — embedding + vector index build summary (**Phase 3.4**)
