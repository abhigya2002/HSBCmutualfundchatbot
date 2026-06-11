"""Phase 3 chunking strategies (section-aware, table-preserving, token-budgeted)."""

from chunking.contracts import CHUNK_STRATEGY_VERSION, Chunk, ChunkingParams
from chunking.section_sliding import chunk_markdown_section_sliding

__all__ = [
    "CHUNK_STRATEGY_VERSION",
    "Chunk",
    "ChunkingParams",
    "chunk_markdown_section_sliding",
]
