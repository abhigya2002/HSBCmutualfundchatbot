# Edge Cases — Phase 3: Chunking, Embeddings, and Index Build

Companion: `phase-wise-architecture.md` §Phase 3.

| ID | Edge case | Why it matters | Expected handling |
|----|-----------|----------------|-------------------|
| P3-01 | Document shorter than overlap window | Negative or zero chunk count | Minimum one chunk; reduce overlap adaptively |
| P3-02 | Table row split mid-row across chunk boundary | Wrong facts (expense ratio halves) | Table-aware chunking or “do not split table” rule |
| P3-03 | Repeated boilerplate on every page | Retrieval dominated by noise | Dedupe or down-weight repeated blocks in `clean_document` phase |
| P3-04 | `source_url` metadata missing on chunk | Allowlist enforcement breaks in Phase 4 | Hard fail index build if any chunk lacks allowlisted `source_url` |
| P3-05 | Embedding model context limit < chunk target | Truncation drops facts | Reduce max tokens or hierarchical chunk; log truncation |
| P3-06 | Special tokens / rupee / percent encoding | Keyword index misses | Normalize currency and `%` for keyword channel only |
| P3-07 | Scheme name alias (“HSBC Mid cap” vs slug) | Keyword mismatch | Optional synonym map **for query side only**—not new URLs |
| P3-08 | Empty document after cleaning | Zero chunks | Exclude from vector index; surface in parse report |
| P3-09 | `effective_date` unknown | Footer date ambiguous | Propagate `crawl_timestamp` from Phase 2 metadata |
| P3-10 | Rebuild changes embedding model version | Incomparable vectors | Version index name + store `embedding_model_id` |
| P3-11 | Duplicate chunks (same text, same URL) | Wasted retrieval slots | Near-dup detection optional; at minimum dedupe identical strings |
| P3-12 | BM25 index includes stopwords only query | Zero hits | Hybrid fallback must still return vector hits |

**Test hints:** Golden chunk boundaries on one table-heavy page; assert every chunk’s `source_url` ∈ canonical 16.
