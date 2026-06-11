"""Daily corpus refresh — hash-gated re-indexing for 16 allowlisted Groww URLs."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from mf_faq.ingestion.config import CONTENT_HASHES_PATH, DRIFT_THRESHOLD, REFRESH_DIR
from mf_faq.ingestion.fetch import fetch_page_for_hash
from mf_faq.ingestion.pipeline.service import Pipeline
from mf_faq.ingestion.sources import SourceEntry, load_sources
from mf_faq.ingestion.stable_hash import stable_content_hash

log = logging.getLogger(__name__)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def _load_hashes(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def _save_hashes(path: Path, hashes: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_refresh(*, hashes_path: Path | None = None) -> int:
    """
    Compare stable content hashes; re-index changed URLs only.

    Returns process exit code (0 = success, 1 = failure / drift / fetch errors).
    """
    _configure_logging()
    store_path = hashes_path or CONTENT_HASHES_PATH
    previous = _load_hashes(store_path)
    sources = load_sources()

    changed_urls: list[str] = []
    failed_urls: list[str] = []
    unchanged_count = 0
    baseline_count = 0
    new_hashes: dict[str, str] = dict(previous)

    for entry in sources:
        result = fetch_page_for_hash(entry.url)
        if not result.ok:
            failed_urls.append(entry.url)
            continue

        current_hash = stable_content_hash(result.text)
        old_hash = previous.get(entry.url)

        if old_hash is None:
            new_hashes[entry.url] = current_hash
            baseline_count += 1
            log.info("baseline_recorded scheme=%s", entry.scheme)
        elif old_hash != current_hash:
            changed_urls.append(entry.url)
            new_hashes[entry.url] = current_hash
            log.info("content_changed scheme=%s", entry.scheme)
        else:
            unchanged_count += 1
            new_hashes[entry.url] = current_hash

    _save_hashes(store_path, new_hashes)

    if len(changed_urls) >= DRIFT_THRESHOLD:
        log.critical(
            "DRIFT ALERT: %s URLs changed (threshold=%s) — skipping re-index, hashes saved",
            len(changed_urls),
            DRIFT_THRESHOLD,
        )
        log.info(
            "refresh_summary changed=%s failed=%s unchanged=%s baseline=%s drift_frozen=true",
            len(changed_urls),
            len(failed_urls),
            unchanged_count,
            baseline_count,
        )
        return 1

    if changed_urls:
        pipeline = Pipeline()
        reindexed = 0
        for url in changed_urls:
            try:
                pipeline.refresh_url(url)
                reindexed += 1
            except Exception:
                log.exception("reindex_failed url=%s", url)
                failed_urls.append(url)
    else:
        reindexed = 0

    log.info(
        "refresh_summary changed=%s failed=%s unchanged=%s baseline=%s reindexed=%s",
        len(changed_urls),
        len(failed_urls),
        unchanged_count,
        baseline_count,
        reindexed,
    )

    if failed_urls:
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    _ = argv
    return run_refresh()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
