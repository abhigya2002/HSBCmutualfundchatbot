# Generated artifact layout (Phase 2+)

Subfolders are created by **Phase 2.1** (`python -m phase_2_1.dry_enumerate` or `python -m dry_enumerate` from `phases/phase-2-ingestion`):

| Directory | Purpose |
|-----------|---------|
| `raw/` | Raw HTTP response bytes + crawl metadata (Phase 2.2+) |
| `clean/` | Normalized Markdown for chunking (**Phase 2.4+**; `python -m phase_2_4.run_normalize`) |
| `extracted/` | Main HTML fragment + extract sidecar JSON (Phase 2.3+) |
| `metadata/` | `doc_metadata` + candidate tags per scheme (**Phase 2.5+**; `python -m phase_2_5.run_metadata`) |
| `quarantine/` | Failed-scheme review stubs (**Phase 2.6**; `python -m phase_2_6.run_finalize`) |

**Root JSON (under `artifacts/`):** `fetch_report.json`, `extract_report.json`, `normalize_report.json`, `doc_metadata_report.json`, **`phase2_corpus_manifest.json`**, **`phase2_quality_report.json`** (Phase 2.6).

**Per-scheme under `clean/`:** `{slug}.md` (Phase 2.4), `{slug}.normalize.json` (2.4), **`{slug}.clean.json`** (2.6 offsets + handoff pointers).

**Git:** Large binaries should stay untracked; add patterns under `phase-2-ingestion/.gitignore` when first snapshots land.
