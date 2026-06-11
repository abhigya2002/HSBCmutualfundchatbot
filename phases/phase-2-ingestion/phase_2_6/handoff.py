"""Phase 3 handoff notes (static contract; Phase 2.6 embeds this in reports)."""

from __future__ import annotations

PHASE3_HANDOFF = {
    "chunker_primary_text": "artifacts/clean/{slug}.md (UTF-8 Markdown from Phase 2.4)",
    "section_offsets": (
        "artifacts/clean/{slug}.clean.json → `sections[]` with "
        "`start_char` / `end_char` (end exclusive) into the Markdown string"
    ),
    "per_document_metadata": "artifacts/metadata/{slug}.json (Phase 2.5 doc_metadata + candidates)",
    "citations": "Use `source_url` from metadata/registry; must be one of the 16 allowlisted Groww URLs",
    "version_fields": [
        "parser_version (Phase 2.3)",
        "normalizer_version (Phase 2.4)",
        "metadata_builder_version (Phase 2.5)",
        "clean_document_version (Phase 2.6)",
    ],
}
