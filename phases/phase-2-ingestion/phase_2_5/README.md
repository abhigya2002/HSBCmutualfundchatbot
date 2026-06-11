# Phase 2.5 — Candidate structured fields and `doc_metadata`

**Architecture:** `phase-wise-architecture.md` — Phase 2.5.

## What it does

- Reads **`artifacts/clean/{slug}.md`** (Phase 2.4) and optional sidecars: crawl (2.2), extract (2.3), normalize (2.4).
- Writes **`artifacts/metadata/{slug}.json`** per registry row with:
  - **`doc_metadata` core:** `scheme`, `source_url`, `content_sha256` (of clean Markdown bytes), `parser_version`, `fetched_at`, `extract_status`, `normalizer_version`, `normalize_status`, `metadata_builder_version`.
  - **`candidates`:** best-effort hints for expense ratio, exit load, min SIP, lock-in, riskometer, benchmark, statement/tax — each either **`null`** or a small evidence object (`snippet`, `pattern`, optional `value_text`). **Not QA-verified.**
  - **`registry`:** Phase 1 `id` + `scheme` (read-only linkage).
  - **`artifact_paths`:** paths to raw HTML, clean md, sidecars, this JSON.
- Writes corpus summary **`artifacts/doc_metadata_report.json`**.

## Run

From `phases/phase-2-ingestion` (after 2.4):

```powershell
pip install -r requirements.txt
python -m phase_2_5.run_metadata
```

## Code

- [candidates.py](candidates.py) — regex/snippet extractors on normalized text only
- [doc_metadata.py](doc_metadata.py) — assemble + write one `doc_metadata` file
- [run_metadata.py](run_metadata.py) — CLI over all **16** URLs

Shared: [`../common/`](../common/).
