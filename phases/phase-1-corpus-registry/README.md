# Phase 1 — Corpus curation and source registry

**Architecture:** `phase-wise-architecture.md` (Phase 1).

## Goal

Closed `source_registry` with **exactly sixteen** rows—one per allowlisted Groww URL in `phases/phase-0-foundation/scope.md` §3. Allowlist enforcement in code for downstream phases.

## Artifacts (implemented)

| Artifact | Description |
|----------|-------------|
| [source_registry.json](source_registry.json) | Canonical registry JSON (`registry_version`, `entries[]` with `url`, `source_type`, `scheme`, `doc_version`, `published_date`, `crawl_frequency`, `active`) |
| [source_registry.csv](source_registry.csv) | Same sixteen rows for spreadsheets / BI |
| [allowlist.py](allowlist.py) | `canonicalize_url`, `is_allowlisted`, `require_allowlisted`, `load_registry`, `validate_registry_integrity`, `get_canonical_urls`, `entry_by_scheme_slug` |
| [validate_urls.py](validate_urls.py) | Network check per row; writes `url-validation-report.json` and `url-validation-report.md` |
| [test_allowlist.py](test_allowlist.py) | `unittest` suite (no third-party deps) |

Reports (regenerate anytime):

| Artifact | Description |
|----------|-------------|
| `url-validation-report.json` | Machine-readable results from `validate_urls.py` |
| `url-validation-report.md` | Human-readable summary table |

## Usage

From this directory (`phases/phase-1-corpus-registry/`):

```powershell
python test_allowlist.py -v
python validate_urls.py --timeout 25
```

Options for `validate_urls.py`:

- `--timeout` — per-request seconds (default 20).
- `--insecure` — disable TLS certificate verification (**local debugging only**).

Exit code `0` when every URL returns HTTP 2xx and the final URL (after redirects) still canonicalizes to an allowlisted path. Non-zero if any error or off-allowlist redirect.

## Exit criteria (architecture)

- [x] Registry row count = **16**; unique `scheme` and `url`; `source_type` = `groww_scheme_page`; `active` = true.
- [x] Allowlist module rejects non-corpus URLs and normalizes equivalents (http/https, `www`, query strip, trailing slash).
- [x] URL validation script + committed reports (re-run after registry edits).

## Edge cases

See [edge-cases/phase-1.md](../../edge-cases/phase-1.md).
