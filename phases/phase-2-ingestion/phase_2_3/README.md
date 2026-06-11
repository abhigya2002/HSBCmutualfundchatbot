# Phase 2.3 — HTML parsing and primary content extraction

**Architecture:** `phase-wise-architecture.md` — Phase 2.3.

## What it does

- Reads each **`artifacts/raw/{slug}.html`** from Phase 2.2.
- Parses with **BeautifulSoup** (`html.parser`), prefers **`#root`** (Groww SSR fund content), then `main` / `article` / `#__next` / `body`.
- Strips `script` / `style` / `noscript` from the chosen subtree.
- Writes **`artifacts/extracted/{slug}.main.html`** (fragment HTML) and **`artifacts/extracted/{slug}.extract.json`** (`extract_status`: `ok` | `partial` | `empty_shell` | `parse_error`, text length, selector, `parser_version`).
- Writes **`artifacts/extract_report.json`**.

## Run

After a successful Phase 2.2 fetch, from `phases/phase-2-ingestion`:

```powershell
pip install -r requirements.txt
python -m phase_2_3.run_extract
```

Optional: `--report path\to\extract_report.json`

## Dependency

`beautifulsoup4` (see `requirements.txt`).

## Code

- [extract.py](extract.py) — heuristics
- [run_extract.py](run_extract.py) — CLI

Shared: [`../common/`](../common/).
