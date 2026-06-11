# Phase 3.3 — Chunk metadata, validation, and quality gates

**Architecture:** `phase-wise-architecture.md` — Phase 3.3.

## Run

From `phases/phase-3-chunking` (requires Phase 3.2 chunk bundles):

```powershell
cd "d:\RAG Chatbot\phases\phase-3-chunking"
python -m phase_3_3.run_validate
```

Options:

- `--scheme SLUG` — validate one scheme
- `--allow-warnings` — exit 0 even if chunks exceed embedding `max_input_tokens` (flagged, not truncated)
- `--config PATH` — override `config/chunking.defaults.json`

## What it does

1. Loads `artifacts/chunks/*.chunks.json` from Phase 3.2.
2. Enriches metadata: `source_url`, `scheme`, `doc_type`, `section_title`, `effective_date` (Phase 2 `fetched_at` fallback — P3-09), `compliance_rank`.
3. **Hard fails** if any chunk lacks `source_url` or URL is not in the canonical **16** (P3-04).
4. Excludes zero-chunk schemes from the indexable set (P3-08).
5. Dedupes identical chunk text per URL (P3-11); optional near-dup via config.
6. Flags chunks over `embedding.max_input_tokens` (P3-05).
7. Writes:
   - `artifacts/chunks_validated/{slug}.chunks.json`
   - `artifacts/phase3_validated_manifest.json`
   - `artifacts/phase3_index_build_quality_report.json`

Does **not** embed or build indexes (Phase 3.4).

## Config (`chunking.defaults.json`)

```json
"validation": { "dedupe_identical_text": true, "near_dup_enabled": false },
"embedding": { "model_id": "placeholder-embedding-v1", "max_input_tokens": 8192 }
```

## Exit codes

- `0` — no hard failures; at least one indexable scheme
- `1` — allowlist/required-field hard fail, zero indexable, or context limit exceeded (unless `--allow-warnings`)
- `2` — missing input bundles
