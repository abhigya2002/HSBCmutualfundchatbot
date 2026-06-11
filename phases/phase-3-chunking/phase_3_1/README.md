# Phase 3.1 — Workspace, configuration, and Phase 2 handoff

**Architecture:** `phase-wise-architecture.md` — Phase 3.1.

## Run

From `phases/phase-3-chunking` (so `chunking` and `phase_3_1` are importable):

```powershell
cd "d:\RAG Chatbot\phases\phase-3-chunking"
python -m phase_3_1.dry_enumerate
```

Options:

- `--config PATH` — override `config/chunking.defaults.json`
- `--json-out PATH` — custom manifest path (default: `artifacts/phase3_1_dry_manifest.json`)
- `--allow-blockers` — exit 0 even when some schemes fail handoff checks

Environment:

- `CHUNKING_CONFIG_PATH` — config file (via `chunking.config_load`)
- `PHASE3_ARTIFACT_ROOT` — override Phase 3 `artifact_root`
- `PHASE2_ARTIFACT_ROOT` — override Phase 2 artifact directory

## What it does

1. Creates Phase 3 workspace dirs: `artifacts/chunks/`, `embeddings/`, `indexes/`, `logs/`.
2. Loads chunking config (token budget, overlap, `default_strategy`).
3. Validates Phase 1 registry (16 URLs).
4. For each scheme, checks Phase 2 handoff:
   - `clean_document` (`.clean.json`) with `sections`
   - normalized Markdown (`.md`, non-empty)
   - `doc_metadata` (`.json`)
   - `extract_status` in `ok` | `partial` (not `parse_error` / `empty_shell`)
   - not quarantined; `source_url` allowlisted and matches registry
5. Writes `artifacts/phase3_1_dry_manifest.json` and `artifacts/phase3_handoff_report.json`.
6. **Does not** chunk, embed, or build indexes.

## Code

| Module | Role |
|--------|------|
| [dry_enumerate.py](dry_enumerate.py) | CLI entrypoint |
| [paths.py](paths.py) | Phase 3 + Phase 2 artifact path resolution |
| [handoff.py](handoff.py) | Per-scheme validation |
| [registry_bridge.py](registry_bridge.py) | Phase 1 registry + allowlist |
| [logging_setup.py](logging_setup.py) | Structured logging with PII redaction |

## Exit codes

- `0` — all 16 schemes indexable (or `--allow-blockers`)
- `1` — one or more schemes blocked
- `2` — Phase 2 artifact root missing
