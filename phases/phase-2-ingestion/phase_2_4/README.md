# Phase 2.4 — Normalization and semantic preservation

**Architecture:** `phase-wise-architecture.md` — Phase 2.4.

## What it does

- Reads each **`artifacts/extracted/{slug}.main.html`** from Phase 2.3 (and optional **`{slug}.extract.json`** for status).
- Strips common Groww chrome (`nav` / `header` / `footer`, role landmarks, heuristic CSS-module header/nav/footer/cookie blocks).
- Emits **lightweight Markdown**: headings (`#`–`######`), paragraphs, nested lists, simple tables (`| … |`).
- Applies **Unicode NFKC** and collapses excessive blank lines; keeps **`%`**, **`₹`**, and digits intact.
- Drops a small **static boilerplate** line set and, by default, **corpus-wide** repeated short lines that appear on almost every page (menu noise), without touching lines that look numeric/factual.
- Writes **`artifacts/clean/{slug}.md`**, sidecar **`artifacts/clean/{slug}.normalize.json`**, and **`artifacts/normalize_report.json`**.

## Run

After Phase 2.3, from `phases/phase-2-ingestion`:

```powershell
pip install -r requirements.txt
python -m phase_2_4.run_normalize
```

Skip cross-document line dedupe (e.g. single-scheme experiments):

```powershell
python -m phase_2_4.run_normalize --no-corpus-dedupe
```

## Code

- [normalize.py](normalize.py) — `NORMALIZER_VERSION`, `normalize_extracted_html`, `build_corpus_boilerplate_lines`
- [run_normalize.py](run_normalize.py) — CLI over all registry URLs

Shared: [`../common/`](../common/) (`ArtifactPaths.planned_clean_path`, `normalize_sidecar_path`).

## Metadata

Sidecar includes **`language_note`**: English-only v1 (per Phase 0).
