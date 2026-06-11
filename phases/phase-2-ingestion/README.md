# Phase 2 — Data ingestion and document processing

**Architecture:** `phase-wise-architecture.md` (Phase 2).

## Repository layout

```text
phase-2-ingestion/
  README.md                    # this file
  dry_enumerate.py             # shim -> phase_2_1.dry_enumerate
  config/
    ingestion.defaults.json    # timeouts, user-agent, artifact dirs, logging
  common/                      # shared by subphases 2.1–2.6
    config.py
    paths.py
    registry_bridge.py
    logging_setup.py
  artifacts/                   # generated raw / clean / metadata (see artifacts/README.md)
  requirements.txt             # beautifulsoup4 (Phase 2.3+)
  tests/
    test_phase_2_1.py          # 2.1 + common paths
    test_phase_2_3.py          # extraction heuristics
    test_phase_2_4.py          # normalization + Markdown emit
    test_phase_2_5.py          # doc_metadata + candidate tags
    test_phase_2_6.py          # clean_document + quality rollup
    fixtures/
      minimal_mf.html          # tiny HTML for unit tests
  phase_2_1/                   # workspace + dry run
  phase_2_2/                   # fetch + raw_store + run_fetch
  phase_2_3/                   # extract + run_extract
  phase_2_4/                   # normalize + run_normalize → artifacts/clean/
  phase_2_5/                   # doc_metadata + run_metadata → artifacts/metadata/
  phase_2_6/                   # run_finalize → *.clean.json, manifest, quality, quarantine
```

## Goal

Transform the sixteen allowlisted Groww HTML pages into clean, retrieval-ready text (raw snapshot, cleaned text, parse metadata).

## Phase 2.1 (implemented)

**Workspace, configuration, and registry integration** — no network I/O.

| Item | Location |
|------|----------|
| Default config | [config/ingestion.defaults.json](config/ingestion.defaults.json) |
| Artifact paths | [common/paths.py](common/paths.py) |
| Config loader + env overrides | [common/config.py](common/config.py) |
| Phase 1 registry + allowlist | [common/registry_bridge.py](common/registry_bridge.py) |
| PII redacting logs | [common/logging_setup.py](common/logging_setup.py) |
| Dry CLI (canonical) | [phase_2_1/dry_enumerate.py](phase_2_1/dry_enumerate.py) |
| Dry CLI (shim) | [dry_enumerate.py](dry_enumerate.py) |

### Commands

From `phases/phase-2-ingestion/`:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
python -m phase_2_1.dry_enumerate
python -m dry_enumerate
```

Optional JSON manifest:

```powershell
python -m phase_2_1.dry_enumerate --json-out artifacts/dry_manifest.json
```

### Environment overrides

| Variable | Effect |
|----------|--------|
| `INGESTION_CONFIG_PATH` | Absolute path to a JSON config file |
| `INGESTION_ARTIFACT_ROOT` | Overrides `artifact_root` |
| `INGESTION_USER_AGENT` | Overrides `user_agent` |
| `INGESTION_TIMEOUT_SECONDS` | Overrides `http.timeout_seconds` |

### Exit criteria (Phase 2.1)

- [x] Directory layout for `raw/`, `clean/`, `metadata/`
- [x] Load and validate Phase 1 `source_registry.json` via allowlist
- [x] Config: HTTP settings, User-Agent, logging + PII redaction
- [x] Dry enumeration of all **16** schemes

---

## Phase 2.2 (implemented)

**Allowlist-only HTTP fetch** and raw HTML + crawl JSON under `artifacts/raw/`. See [phase_2_2/README.md](phase_2_2/README.md).

```powershell
pip install -r requirements.txt
python -m phase_2_2.run_fetch
```

Produces `artifacts/fetch_report.json`.

---

## Phase 2.3 (implemented)

**Main content extraction** from each raw HTML file into `artifacts/extracted/`. See [phase_2_3/README.md](phase_2_3/README.md).

```powershell
pip install -r requirements.txt
python -m phase_2_3.run_extract
```

Produces `artifacts/extract_report.json` (per-URL `extract_status`: `ok` | `partial` | `empty_shell` | `parse_error`).

---

## Phase 2.4 (implemented)

**Normalization and semantic preservation** — Markdown under `artifacts/clean/`. See [phase_2_4/README.md](phase_2_4/README.md).

```powershell
pip install -r requirements.txt
python -m phase_2_4.run_normalize
```

Produces `artifacts/normalize_report.json`, per-scheme `*.md`, and `*.normalize.json` sidecars.

---

## Phase 2.5 (implemented)

**Candidate structured fields and `doc_metadata`** under `artifacts/metadata/`. See [phase_2_5/README.md](phase_2_5/README.md).

```powershell
pip install -r requirements.txt
python -m phase_2_5.run_metadata
```

Produces per-scheme `artifacts/metadata/{slug}.json` and `artifacts/doc_metadata_report.json`.

---

## Phase 2.6 (implemented)

**Final `clean_document`, corpus manifest, parsing quality report, and quarantine records.** See [phase_2_6/README.md](phase_2_6/README.md).

```powershell
pip install -r requirements.txt
python -m phase_2_6.run_finalize
```

Produces `artifacts/clean/{slug}.clean.json`, `artifacts/phase2_corpus_manifest.json`, `artifacts/phase2_quality_report.json`, and optional `artifacts/quarantine/{slug}.review.json`.

---

## Exit criteria (full Phase 2 rollup)

- ≥95% parse success on curated corpus; failures isolated for manual review.

## Edge cases

See [edge-cases/phase-2.md](../../edge-cases/phase-2.md).
