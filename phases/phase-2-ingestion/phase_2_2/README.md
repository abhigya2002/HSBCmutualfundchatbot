# Phase 2.2 — Allowlist-enforced HTTP fetch and raw snapshot storage

**Architecture:** `phase-wise-architecture.md` — Phase 2.2.

## Run

From `phases/phase-2-ingestion`:

```powershell
pip install -r requirements.txt
python -m phase_2_2.run_fetch
```

## Code

- [fetcher.py](fetcher.py) — allowlist GET, redirects, retries
- [raw_store.py](raw_store.py) — write `artifacts/raw/{slug}.html` + `.crawl.json`
- [run_fetch.py](run_fetch.py) — CLI over all 16 registry URLs

Shared: [`../common/`](../common/).
