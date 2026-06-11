# Phase 2.6 — `clean_document`, quality report, and corpus manifest

**Architecture:** `phase-wise-architecture.md` — Phase 2.6.

## What it does

- Writes final **`artifacts/clean/{slug}.clean.json`** per scheme: `body_markdown_path` (reference to Phase 2.4 `.md`), `body_sha256` / length from Phase 2.5 metadata when present, **`sections`** with `start_char` / `end_char` (**end exclusive**) into the Markdown string for chunk boundaries, plus upstream status and `pipeline_versions`.
- Writes **`artifacts/phase2_corpus_manifest.json`**: all 16 URLs with paths and `parse_success` / `quarantined` flags.
- Writes **`artifacts/phase2_quality_report.json`**: aggregates (counts by `extract_status`, `normalize_status`, byte totals, `parse_success_rate`, wall-clock ms), per-row diagnostics, **`phase3_handoff`** notes, and **`quarantine_slugs`**.
- **Quarantine:** for any scheme that fails the parse-success gate, writes **`artifacts/quarantine/{slug}.review.json`** with reasons and artifact paths (no silent drops).

## Run

After Phases 2.2–2.5, from `phases/phase-2-ingestion`:

```powershell
pip install -r requirements.txt
python -m phase_2_6.run_finalize
```

Exit code **1** if more than one document fails the same **≤1 failure in 16** gate used elsewhere (~94% floor).

## Code

- [sections.py](sections.py) — Markdown heading → char offsets
- [clean_document.py](clean_document.py) — assemble `clean_document` JSON
- [quality.py](quality.py) — `parse_success` + aggregates
- [handoff.py](handoff.py) — static Phase 3 field/path notes
- [run_finalize.py](run_finalize.py) — CLI

Shared: [`../common/`](../common/) (`ArtifactPaths.quarantine`, `clean_document_path`, manifest/quality paths).
