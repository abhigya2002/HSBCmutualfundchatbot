# Phase 2.1 — Workspace, configuration, registry integration

**Architecture:** `phase-wise-architecture.md` — Phase 2.1.

## Run

From `phases/phase-2-ingestion` (this directory’s parent must be on `PYTHONPATH` via `-m` from that folder):

```powershell
python -m phase_2_1.dry_enumerate
```

Short shim at workspace root: `python -m dry_enumerate` (see [`../dry_enumerate.py`](../dry_enumerate.py)).

## Code

- [dry_enumerate.py](dry_enumerate.py) — dry enumeration CLI

Shared helpers live in [`../common/`](../common/).
