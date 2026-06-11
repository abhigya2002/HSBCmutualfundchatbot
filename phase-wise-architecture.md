# Detailed Phase-Wise Architecture
## Mutual Fund FAQ Assistant (Facts-Only RAG System)

## 1) Objective and Non-Negotiable Constraints
- Build a facts-only assistant for mutual fund scheme FAQs. **Corpus allowlist (strict):** only the **16** HSBC scheme pages on Groww listed in [2.1](#21-curated-corpus-urls-hsbc-mutual-fund--groww). **Do not** register, fetch, index, embed, or cite any other URL (no AMC/AMFI/SEBI pages, no PDFs from other hosts, no following outbound links to expand the corpus).
- Return objective, verifiable answers only; no advice, no recommendations, no projections.
- Enforce response format:
  - Maximum 3 sentences.
  - Exactly one source citation link.
  - Footer: `Last updated from sources: <date>`.
- Never collect/store PAN, Aadhaar, account numbers, OTP, or personal contact data.

---

## 2) Target System Architecture (High-Level)

### Core Layers
1. **Source Registry Layer**
   - **Fixed allowlist:** exactly the **16** Groww URLs in [2.1](#21-curated-corpus-urls-hsbc-mutual-fund--groww)—no additions, no substitutions in this project phase.
   - Metadata per URL: `source_type`, `scheme_name`, `published_date`, `last_verified`, `status`.

2. **Ingestion and Normalization Layer**
   - Fetch **only** those registered Groww HTML pages (same origin/path as allowlist); do not crawl or ingest linked documents on other domains.
   - Parse and clean text.
   - Normalize fields (expense ratio, exit load, SIP minimum, lock-in, benchmark, riskometer, process steps).

3. **Chunking and Indexing Layer**
   - Semantic chunking with source-preserving metadata.
   - Embedding generation.
   - Vector index for retrieval + lightweight keyword index for exact regulatory terms.

4. **Retrieval and Ranking Layer**
   - Query classification (factual vs prohibited/advisory).
   - Hybrid retrieval (vector + keyword).
   - Re-ranking within allowlisted chunks (e.g. freshness/recency vs chunk relevance); no cross-domain authority tiers because only Groww scheme pages exist in the index.

5. **Guardrails and Response Composer Layer**
   - Refusal logic for advisory/comparison/performance-projection prompts.
   - Response templating to force 3-sentence cap and single citation.
   - Date footer injection from selected source metadata.

6. **API and UI Layer**
   - Chat endpoint with policy-first middleware.
   - Minimal UI: welcome text, 3 sample questions, visible disclaimer.

7. **Observability and Governance Layer**
   - Structured logs (no PII).
   - Source freshness monitoring.
   - Quality/compliance scorecards.

---

## 2.1) Curated corpus URLs (HSBC Mutual Fund / Groww)

The following **16 Groww mutual fund scheme URLs** are the **complete and exclusive** corpus for this project: ingestion, chunking, retrieval, and **every user-visible citation hyperlink** must resolve to exactly one of these URLs (canonical HTTPS form below). Map each URL to `scheme_name`, `source_type: groww_scheme_page`, and `amc: HSBC Mutual Fund` in `source_registry`.

| # | Scheme (slug hint) | URL |
|---|---------------------|-----|
| 1 | HSBC India Opportunities Fund (Direct Growth) | https://groww.in/mutual-funds/hsbc-india-opportunities-fund-direct-growth |
| 2 | HSBC Midcap Fund (Direct Growth) | https://groww.in/mutual-funds/hsbc-midcap-fund-direct-growth |
| 3 | HSBC Small Cap Fund (Direct Growth) | https://groww.in/mutual-funds/hsbc-small-cap-fund-direct-growth |
| 4 | HSBC Multi Cap Fund (Direct Growth) | https://groww.in/mutual-funds/hsbc-multi-cap-fund-direct-growth |
| 5 | HSBC Value Fund (Direct Growth) | https://groww.in/mutual-funds/hsbc-value-fund-direct-growth |
| 6 | HSBC Large and Mid Cap Fund (Direct Growth) | https://groww.in/mutual-funds/hsbc-large-and-mid-cap-fund-direct-growth |
| 7 | HSBC Equity Savings Fund (Direct Growth) | https://groww.in/mutual-funds/hsbc-equity-savings-fund-direct-growth |
| 8 | HSBC Infrastructure Fund (Direct Growth) | https://groww.in/mutual-funds/hsbc-infrastructure-fund-direct-growth |
| 9 | HSBC Multi Asset Allocation Fund (Direct Growth) | https://groww.in/mutual-funds/hsbc-multi-asset-allocation-fund-direct-growth |
| 10 | HSBC Focused Fund (Direct Growth) | https://groww.in/mutual-funds/hsbc-focused-fund-direct-growth |
| 11 | HSBC Gold ETF FoF (Direct Growth) | https://groww.in/mutual-funds/hsbc-gold-etf-fof-direct-growth |
| 12 | HSBC India Export Opportunities Fund (Direct Growth) | https://groww.in/mutual-funds/hsbc-india-export-opportunities-fund-direct-growth |
| 13 | HSBC Consumption Fund (Direct Growth) | https://groww.in/mutual-funds/hsbc-consumption-fund-direct-growth |
| 14 | HSBC Medium Duration Fund (Direct Growth) | https://groww.in/mutual-funds/hsbc-medium-duration-fund-direct-growth |
| 15 | HSBC Dynamic Bond Fund (Direct Growth) | https://groww.in/mutual-funds/hsbc-dynamic-bond-fund-direct-growth |
| 16 | HSBC Gilt Fund (Direct Growth) | https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth |

**Build notes**
- Ingestion is limited to the **HTML (or same-URL response body)** for each allowlisted path only; **do not** follow links to register or ingest other URLs.
- Respect `robots.txt` and Groww terms of use when fetching these pages.
- **Refusal / “educational” replies:** any mandatory hyperlink must still be **one of these 16 URLs** (e.g. cite the most relevant scheme page from the list, or a team-agreed default among the 16). Do not add AMFI/SEBI/AMC links while this strict allowlist is in force.

---

## 3) Phase-Wise Delivery Plan

## Phase 0: Foundation and Scope Freeze
### Goal
Lock problem boundaries, schemes, and compliance acceptance criteria.

### Tasks
- **Scope lock:** AMC = **HSBC Mutual Fund**; corpus = **only** the **16** Groww URLs in [2.1](#21-curated-corpus-urls-hsbc-mutual-fund--groww)—no other sources for this phase.
- Build canonical query taxonomy:
  - Allowed: expense ratio, exit load, minimum SIP, lock-in, riskometer, benchmark, statement/tax process.
  - Refusal: advisory, comparison, return predictions.
- Define acceptance checklist for each answer:
  - factual-only, <=3 sentences, one citation, footer present.

### Deliverables
- Scope document with AMC + schemes.
- Query policy matrix (allowed/refuse/redirect).
- Initial risk register.

### Exit Criteria
- Stakeholder-approved scope and policy matrix.

---

## Phase 1: Corpus Curation and Source Registry
### Goal
Create a **closed** `source_registry` containing **exactly** the **16** Groww HSBC scheme URLs in [2.1](#21-curated-corpus-urls-hsbc-mutual-fund--groww)—no other rows.

### Tasks
- Register all **16** URLs as `source_type: groww_scheme_page` with stable `scheme` identifiers matching slugs.
- Enforce allowlist in code and config: reject any URL not in the canonical list (typo-safe compare on full string).
- Build `source_registry` dataset with:
  - `url`, `source_type`, `scheme`, `doc_version`, `published_date`, `crawl_frequency`, `active`.

### Deliverables
- Versioned source registry (JSON/CSV + docs) with **16** entries only.
- URL validation report (each URL reachable, parseable, canonical).

### Exit Criteria
- Registry row count = **16**; all mapped to allowed query intents; no extra URLs present.

---

## Phase 2: Data Ingestion and Document Processing
### Goal
Transform the **16** allowlisted Groww HTML pages into clean retrieval-ready text.

Implement **Phase 2** in order via the subphases below; each subphase should be shippable and reviewable on its own before starting the next.

### Phase 2 overview (rollup)
- Implement fetchers:
  - HTML fetch + parse for **allowlisted Groww URLs only**.
  - **No** generic PDF pipeline or off-list document ingestion.
- Normalize content:
  - Remove boilerplate/navigation.
  - Preserve headings, tables, bullet semantics.
  - Extract candidate key fields into structured tags.
- Store artifacts:
  - Raw snapshot.
  - Cleaned text.
  - Parse metadata.

---

### Phase 2.1 — Workspace, configuration, and registry integration
**Goal:** Define where artifacts live, how runs are configured, and how ingestion reads the Phase 1 registry (exactly **16** URLs)—without fetching the network yet if undesired.

**Tasks:**
- Directory layout for `raw/`, `clean/`, and metadata (or equivalent object keys).
- Load and validate `source_registry` via Phase 1 allowlist rules before any fetch.
- Run configuration: timeouts, max retries, User-Agent string, log redaction rules (no PII).
- Stub “dry” pipeline entrypoint that enumerates all **16** schemes and exits.

**Deliverable:** Config + registry wiring documented; dry enumeration passes.

---

### Phase 2.2 — Allowlist-enforced HTTP fetch and raw snapshot storage
**Goal:** Reliably download each page’s response body **only** for allowlisted URLs and persist immutable `raw_document` artifacts.

**Tasks:**
- HTTP client with allowlist gate (reject enqueue/fetch for any URL not in registry).
- Handle redirects: final URL must canonicalize to the same allowlisted path (or fail closed).
- Retries with backoff for 429/5xx/transient errors; bounded attempts.
- Persist **raw bytes** + `crawl_metadata` (timestamp, status, content-type, byte length, SHA-256).
- Detect obvious **non-content** responses (e.g. captcha/login interstitials) and mark status for Phase 2.3.

**Deliverable:** One raw snapshot per registry URL on a full successful run; fetch audit log.

---

### Phase 2.3 — HTML parsing and primary content extraction
**Goal:** Turn each `raw_document` into structured DOM or intermediate representation and extract **main scheme content** (not full page chrome).

**Tasks:**
- HTML5 parse; charset handling; stable error reporting on malformed HTML.
- Primary content extraction (CSS selectors, landmark regions, or readability-style extraction—pick one and version it).
- Per-document **extract status**: `ok`, `partial`, `empty_shell`, `parse_error`.
- Preserve minimal provenance: byte/char offsets or DOM node refs for debugging (optional).

**Deliverable:** Extracted main-content artifact (intermediate) per URL + per-URL status in an internal manifest.

---

### Phase 2.4 — Normalization and semantic preservation
**Goal:** Produce human- and chunker-friendly text while keeping factual structure (tables, lists, headings).

**Tasks:**
- Strip navigation, cookie banners, and repeated chrome; dedupe obvious boilerplate across pages.
- Map headings / bullets / tables into a stable plain format (e.g. lightweight Markdown or tagged lines).
- Normalize whitespace and unicode; keep numbers and `%` / rupee symbols intact where present.
- Optional: language detection note (English-only v1 per Phase 0).

**Deliverable:** Normalized text stream per URL suitable for chunking (still per `source_url`).

---

### Phase 2.5 — Candidate structured fields and `doc_metadata`
**Goal:** Attach machine-readable **hints** (not trusted facts without QA) for common FAQ facets and complete `doc_metadata` for downstream indexing.

**Tasks:**
- Populate `doc_metadata`: `scheme`, `source_url`, `content_sha256`, `parser_version`, `fetched_at`, `extract_status`, `normalizer_version`.
- Best-effort **candidate tags** for: expense ratio, exit load, minimum SIP, lock-in, riskometer, benchmark, statement/tax process—only when extracted from normalized text (no inference off-corpus).
- Empty/missing fields explicit (`null` / omitted) rather than guessed.

**Deliverable:** `doc_metadata.json` (or row per URL) linked to raw and clean artifacts.

---

### Phase 2.6 — `clean_document` persistence, quality report, and corpus-wide dry run
**Goal:** Freeze the Phase 2 pipeline: write final `clean_document` + manifest, measure success rates, and fail safely for manual review.

**Tasks:**
- Assemble `clean_document`: normalized body + optional section offsets for chunk boundaries.
- End-to-end run over all **16** URLs; aggregate **parsing quality report** (counts by `extract_status`, bytes, parse time).
- Fail-safe behavior: quarantine failed URLs; do not silently drop without log + manifest entry.
- Handoff notes for Phase 3 (chunking): expected file shapes and versioning fields.

**Deliverable:** Parsing quality report + manifest; meets exit criteria below.

---

### Data Contracts
- `raw_document`: source bytes + crawl metadata.
- `clean_document`: normalized text + section offsets.
- `doc_metadata`: scheme/source/date/version/hash.

### Deliverables (phase rollup)
- Ingestion pipeline with retry and fail-safe logging.
- Parsing quality report with document-level success rates.

### Exit Criteria
- >=95% parse success on curated corpus; failed docs isolated for manual review.

---

## Phase 3: Chunking, Embeddings, and Index Build
### Goal
Index content for high-precision factual retrieval.

Implement **Phase 3** in order via the subphases below; each subphase should be shippable and reviewable on its own before starting the next.

### Phase 3 overview (rollup)
- Chunk allowlisted `clean_document` outputs from Phase 2:
  - Target chunk size around 300–600 tokens; overlap 50–100 tokens.
  - Section-aware, table-preserving strategy (default: `section_sliding_v1`).
- Attach retrieval metadata per chunk (`source_url`, `scheme`, `section_title`, dates, compliance rank).
- Generate embeddings; load versioned vector store.
- Build keyword index for exact regulatory terms (e.g. "lock-in", "exit load", "riskometer").
- Reproducible index build + offline retrieval benchmark before Phase 4.

---

### Phase 3.1 — Workspace, configuration, and Phase 2 handoff
**Goal:** Define where chunk/index artifacts live, how runs are configured, and verify Phase 2 outputs are present and valid for all **16** schemes—without building indexes yet.

**Tasks:**
- Directory layout for `chunks/`, `embeddings/`, `indexes/` (or equivalent object keys) and index-build logs.
- Load `chunking.defaults.json` (or env override): token budget, overlap, `chars_per_token_estimate`, strategy id.
- Resolve Phase 2 artifact root; for each registry URL assert: `clean_document`, normalized Markdown body, `doc_metadata`, `extract_status` acceptable for indexing.
- Dry entrypoint: enumerate **16** schemes, report missing/quarantined Phase 2 artifacts, exit without embedding.

**Deliverable:** Config + Phase 2 handoff validation documented; dry enumeration passes (or lists blockers per URL).

---

### Phase 3.2 — Chunking strategies and chunk artifacts
**Goal:** Turn each `clean_document` into versioned, section-aware chunks with table-safe boundaries.

**Tasks:**
- Implement default strategy **`section_sliding_v1`**: atomic units per section (paragraphs; **Markdown tables kept whole**; oversized tables stay single units rather than split mid-row).
- Soft max char budget from target token range; tail overlap from overlap token range.
- Respect Phase 2.6 `sections` char offsets (`start_char` / `end_char`, end exclusive) for `section_title` and boundary hints.
- Persist **`chunk` artifacts** per scheme: `chunk_id`, `text`, `start_char`, `end_char`, `chunk_strategy_version`.
- Handle short documents: minimum one chunk; reduce overlap adaptively when body shorter than overlap window (P3-01).

**Deliverable:** Chunk files (or manifest) for all indexable schemes; golden-boundary test on at least one table-heavy page.

---

### Phase 3.3 — Chunk metadata, validation, and quality gates
**Goal:** Every chunk is retrieval-ready, allowlist-safe, and deduplicated before embedding.

**Tasks:**
- Attach per-chunk metadata: `source_url`, `scheme`, `doc_type`, `section_title`, `effective_date` (fallback: Phase 2 `crawl_timestamp` / `fetched_at` when on-page date unknown—P3-09), `compliance_rank`.
- **Hard fail** index build if any chunk lacks `source_url` or URL ∉ canonical **16** (P3-04).
- Exclude zero-chunk / empty post-clean documents from vector index; surface in index-build report (P3-08).
- Optional: dedupe identical chunk text per URL (P3-11); log near-dup counts.
- Enforce embedding context limit: if model max tokens < chunk target, cap chunk size or flag truncation (P3-05).

**Deliverable:** Validated chunk manifest + index-build quality report (counts, failures, skipped URLs).

---

### Phase 3.4 — Embedding generation and vector index
**Goal:** Embed all validated chunks and load a versioned vector store for semantic retrieval.

**Tasks:**
- Select embedding model; record `embedding_model_id` and build `index_version` on every run (P3-10).
- Batch-embed chunk text; persist vectors keyed by `chunk_id` + metadata for filtering by `scheme` / `source_url`.
- Upsert into vector store (local or managed—small corpus friendly).
- Support full rebuild and versioned index name for rollback handoff to Phase 8 (blue/green or swap-after-full-build—P8-03).

**Deliverable:** Populated vector index for the corpus; embedding manifest with model id and version.

---

### Phase 3.5 — Keyword index for hybrid retrieval
**Goal:** Support exact-term retrieval for factual FAQ facets alongside the vector index.

**Tasks:**
- Build BM25-like (or equivalent) keyword index over the same chunk set as Phase 3.4.
- Index facet-friendly terms: "exit load", "lock-in", "riskometer", "expense ratio", "minimum sip", "benchmark", etc.
- Normalize currency and `%` for **keyword channel only** where needed (P3-06); do not alter stored chunk text used for generation.
- Document hybrid contract for Phase 4: vector + keyword merge; keyword-only stopword queries must still allow vector fallback (P3-12).
- Scheme aliases remain **query-side only** (P3-07)—no new corpus URLs.

**Deliverable:** Keyword index artifact + documented merge fields shared with vector index (`chunk_id`, `source_url`, `scheme`).

---

### Phase 3.6 — Reproducible index build, benchmarks, and Phase 4 handoff
**Goal:** Freeze a one-command index pipeline and prove baseline retrieval quality before query service work.

**Tasks:**
- Single reproducible script/job: **3.2 → 3.3 → 3.4 → 3.5** with shared `index_version` and config snapshot.
- Corpus-wide build over all **16** URLs; fail-safe: quarantine failed schemes; do not silently publish partial index without manifest flag.
- Author **retrieval benchmark set**: canonical factual queries with expected `source_url` and/or `chunk_id` targets (subset of Phase 0 query taxonomy).
- Measure baseline top-k recall / citation-target hit rate; record threshold pass/fail for factual intents.
- Handoff notes for Phase 4: index paths, version pins, hybrid API surface, filter rules (allowlisted `source_url` only).

**Deliverable:** Reproducible index build script + benchmark report; meets exit criteria below.

---

### Data Contracts
- `chunk`: text span + char offsets + `chunk_id` + `chunk_strategy_version`.
- `chunk_metadata`: `source_url`, `scheme`, `doc_type`, `section_title`, `effective_date`, `compliance_rank`.
- `embedding_record`: `chunk_id`, vector, `embedding_model_id`, `index_version`.
- `index_manifest`: build timestamp, config hash, counts per scheme, skipped/failed URLs, vector + keyword index locations.

### Deliverables (phase rollup)
- Indexed corpus (vector + keyword) with reproducible build script.
- Chunk and index manifests with versioning for Phase 8 refresh jobs.
- Retrieval benchmark set with expected source targets.

### Exit Criteria
- All indexable schemes produce allowlisted chunks with required metadata.
- Baseline top-k recall meets threshold for factual intents on the benchmark set.
- Index build is reproducible from pinned Phase 2 artifacts + config (documented `index_version`).

---

## Phase 4: Query Understanding, Retrieval, and Re-Ranking
### Goal
Return the most relevant snippet from indexed **allowlisted** Groww content for each factual question.

Implement **Phase 4** in order via the subphases below; each subphase should be shippable and reviewable on its own before starting the next.

### Phase 4 overview (rollup)
- Classify query intent (factual, performance-info, advisory/comparison, out-of-scope) per Phase 0 policy matrix.
- Resolve **scheme** among the **16** registry slugs (query-side aliases only—P3-07).
- Run **hybrid retrieval** (vector + keyword) over allowlisted chunks only; keyword-empty → vector fallback (P3-12).
- Re-rank, apply score threshold, select **one** chunk and **one** `source_url` citation.
- Refusal / limited factual paths for non-retrieval intents; hand off ranked evidence to Phase 5.

### Retrieval Policy
- Citation must be **exactly one** URL from the allowlist—typically the Groww page for the scheme the user asked about.
- If the query is ambiguous across schemes, pick the best-matching scheme’s allowlisted URL as the single citation (or product default from Phase 0).
- Never surface or stitch in content whose provenance is not one of the **16** registered pages.

---

### Phase 4.1 — Workspace, configuration, and Phase 3 index handoff
**Goal:** Wire retrieval to active vector + keyword indexes and Phase 1 registry—no query handling yet.

**Tasks:**
- Define Phase 4 workspace layout (`config/`, service artifacts, eval reports).
- Load `phase4_retrieval_handoff.json`, `hybrid_retrieval_contract.json`, and active index pointers (`vector/active.json`, `keyword/active.json`).
- Pin `index_version`, `embedding_model_id`, and paths to chunk records / BM25 index.
- Validate Phase 1 `source_registry` (16 URLs) for allowlist checks in later subphases.
- Dry entrypoint: confirm indexes load, chunk count matches manifest, exit without classifying a query.

**Deliverable:** Config + index handoff validation documented; dry load passes.

---

### Phase 4.2 — Intent classification
**Goal:** Route every user query to allowed, refusal, or retrieval paths before search.

**Tasks:**
- Implement intent labels aligned with Phase 0 / query policy matrix:
  - **factual** (A1–A7 taxonomy: expense ratio, exit load, SIP min, lock-in, riskometer, benchmark, statement/tax process),
  - **performance-info** (P4-09),
  - **advisory** / **comparison** (R1–R2),
  - **out-of-scope** (non-HSBC AMC, off-topic, unsupported language—P4-01, P4-10),
  - **mixed** intent (P4-04: refusal-first or factual-only per policy).
- Rule-based classifier v1 (keywords + patterns); optional LLM labeler behind a feature flag.
- Map intents to actions: `retrieve`, `refuse`, `performance_limited`, `disambiguate`.
- Log intent + confidence for observability (no PII).

**Deliverable:** Intent classifier module + unit tests on canonical allowed/refusal phrases.

---

### Phase 4.3 — Scheme resolution
**Goal:** Map queries to at most one of the **16** `scheme` slugs (or explicit ambiguous / unknown).

**Tasks:**
- Match against registry `scheme`, `scheme_display_name`, and URL slug tokens in the query.
- **Query-side alias map only** (P3-07, P4-02): e.g. nicknames → slug; never add corpus URLs.
- Detect **comparison** or **two-scheme** mentions → route to refusal (P4-03), not dual retrieval.
- Handle typos with conservative fuzzy match; low confidence → `ambiguous` (P4-05).
- Output: `resolved_scheme`, `confidence`, `citation_url_candidate` (canonical allowlisted URL).

**Deliverable:** Scheme resolver + tests (nickname, typo, non-HSBC name, two-fund compare).

---

### Phase 4.4 — Hybrid retrieval (allowlist-scoped)
**Goal:** Retrieve top candidate chunks from vector + keyword indexes with mandatory allowlist filtering.

**Tasks:**
- Load `LocalVectorIndex` + `BM25Index` per Phase 3 handoff; embed query via pinned `embedding_model_id`.
- Run keyword search + vector search; **union by `chunk_id`** per hybrid contract.
- Filter: every hit’s `source_url` must canonicalize to one of the **16** URLs (P3-04).
- When `resolved_scheme` is confident, pass `scheme=` (or `source_url=`) filter to both channels (P4-06).
- If keyword returns empty (stopword-only query), **vector-only fallback** (P3-12, P4-07).
- Configurable `top_k` per channel and fused candidate pool size (e.g. 10–15).

**Deliverable:** Hybrid retriever returning scored candidates with `chunk_id`, `source_url`, `scheme`, `text` preview.

---

### Phase 4.5 — Re-ranking, thresholding, and citation selection
**Goal:** Deterministically pick one best chunk and **one** citation URL for downstream generation.

**Tasks:**
- Fuse channel scores (e.g. normalized weighted sum; document weights in config).
- Re-rank with interpretable signals: facet/intent match (exit load, riskometer, …), lexical overlap, scheme-match boost, `effective_date` / freshness tie-break (P4-12).
- **Score threshold:** if no candidate passes → `not_found_in_sources` payload with one allowlisted URL (resolver or Phase 0 default—P4-07, P4-08).
- **Citation policy:** `citation_url` = allowlisted URL for chosen chunk; if resolver and top chunk disagree, document precedence (prefer resolver scheme for citation—P4-06).
- Emit retrieval result: `chunk_id`, `chunk_text`, `citation_url`, `section_title`, `effective_date`, ranks/scores for audit.

**Deliverable:** Re-ranker + citation picker with documented deterministic tie-breaks.

---

### Phase 4.6 — Retrieval service, evaluation, and Phase 5 handoff
**Goal:** Expose an end-to-end retrieval API and prove quality before guardrails + generation.

**Tasks:**
- Compose pipeline: **4.2 → 4.3 → 4.4 → 4.5** (skip retrieval on refusal intents).
- CLI or function `retrieve(query) -> RetrievalResponse | RefusalResponse`.
- Extend benchmark set with adversarial cases from `edge-cases/phase-4.md` (OOD AMC, compare, mixed intent, typos).
- Offline metrics: precision@k, recall@k (where applicable), **citation URL accuracy** ⊆ allowlist, scheme-match rate.
- Document Phase 5 handoff: evidence fields, refusal shapes, performance-info flag, index version pins.

**Deliverable:** Retrieval service + evaluation report; meets exit criteria below.

---

### Data Contracts
- `RetrievalRequest`: `query`, optional session id (no PII).
- `IntentResult`: `intent`, `action`, `confidence`, `reasons[]`.
- `SchemeResolution`: `scheme`, `source_url`, `confidence`, `status` (`resolved` | `ambiguous` | `unknown`).
- `RetrievalCandidate`: `chunk_id`, `text`, `source_url`, `scheme`, `scores` (vector, keyword, fused).
- `RetrievalResponse`: top candidate + `citation_url` + metadata for Phase 5; or `not_found` with single allowlisted link.
- `RefusalResponse`: `refusal_type`, `messagent`, `citation_url` (one of **16** or default).

### Deliverables (phase rollup)
- Retrieval service with deterministic ranking and citation policy.
- Offline evaluation report (precision@k, citation relevance, adversarial refusal cases).
- Phase 5 handoff document (evidence + refusal contracts).

### Exit Criteria
- Citations are always exactly one URL from the allowlist; scheme alignment meets agreed threshold on benchmark + adversarial set.
- Advisory/comparison/mixed-policy queries do not invoke hybrid retrieval.
- Consistent single-source selection with low hallucination risk; abstention path when evidence is weak.

---

## Phase 5: Guardrails, Compliance Engine, and Response Generation
### Goal
Guarantee policy-compliant outputs every time—refusals, limited performance answers, and grounded factual replies with exactly one allowlisted citation.

Implement **Phase 5** in order via the subphases below; each subphase should be shippable and reviewable on its own before starting the next.

### Phase 5 overview (rollup)
- Consume Phase 4 `RetrieveOutcome` (retrieval evidence or refusal payload).
- Run **pre-generation compliance gates** (advice/comparison/injection/performance-info policy).
- Compose **refusal** or **factual** user-visible responses from templates and/or optional LLM (feature-flagged).
- Enforce **post-generation validators**: ≤3 sentences, one allowlisted hyperlink, prohibited-phrase checks, footer date policy (Phase 0).
- On validation failure: deterministic repair or safe refusal—never emit non-compliant output.
- Hand off stable API contracts to Phase 6 (API/UI).

---

### Phase 5.1 — Workspace, configuration, and Phase 4 handoff
**Goal:** Wire generation/compliance to Phase 4 retrieval outputs—no user-facing answers yet.

**Tasks:**
- Define Phase 5 workspace layout (`config/`, composer templates, validator rules, eval/red-team reports).
- Load `phase5_retrieval_handoff.json` from Phase 4.6 (evidence fields, refusal shapes, `performance_limited`, index version pins).
- Pin composer defaults: sentence budget (3), citation format (markdown link), footer template, default allowlisted URL (Phase 0 matrix).
- Load prohibited-phrase lists and advisory/comparison patterns (align with Phase 0 / `edge-cases/phase-5.md`).
- Dry entrypoint: validate handoff + config; exit without composing a response.

**Deliverable:** Config + Phase 4 handoff validation documented; dry load passes.

---

### Phase 5.2 — Pre-generation compliance rule engine
**Goal:** Block or route unsafe inputs before any answer text is produced.

**Tasks:**
- Accept `RetrieveOutcome` from Phase 4.6 (`retrieval` | `refusal`, `performance_limited` flag).
- **Refusal short-circuit:** if Phase 4 already refused or disambiguated, skip factual composition (pass to 5.3).
- **Policy gates** on retrieval path:
  - reject regeneration when evidence is empty and status is `not_found_in_sources` (abstention template),
  - enforce `performance_limited` handling (no projections; ground only in retrieved spans—P4-09),
  - ignore/strip prompt-injection patterns in user query echo paths (P4-11, P5-10).
- Emit `ComplianceDecision`: `allow_compose` | `refuse` | `abstain` with `reasons[]` for audit.

**Deliverable:** Pre-generation rule engine + unit tests (refusal passthrough, abstain on weak evidence, performance-info gate).

---

### Phase 5.3 — Refusal response composer
**Goal:** Produce polite, policy-compliant refusal messages with exactly one allowlisted link.

**Tasks:**
- Map Phase 4 `RefusalResponse.refusal_type` → user-visible templates (`advisory`, `comparison`, `mixed_intent`, `out_of_scope`, `disambiguate`, `performance_info`).
- Use `message_hint` from Phase 4 as internal guidance; render fixed, reviewable copy (no open-ended advice).
- **Citation:** exactly **one** URL from the **16** allowlisted Groww pages—prefer scheme-resolved URL; else Phase 0 default (P5-12).
- Include visible disclaimer line: `Facts-only. No investment advice.` (Phase 6 may reuse).
- Output: `RefusalAnswer` with `body_text`, `citation_url`, `citation_markdown` (single link).

**Deliverable:** Refusal composer + tests (one link, allowlist-only, all refusal types).

---

### Phase 5.4 — Factual response composer (evidence-grounded)
**Goal:** Turn top retrieved chunk into a ≤3-sentence factual answer with one citation.

**Tasks:**
- Input: Phase 4 `RetrievalResponse` (`chunk_text`, `citation_url`, `section_title`, `effective_date`, scores).
- **Composition policy:**
  - Sentences 1–2: direct factual answer grounded **only** in `chunk_text` (extractive/template v1; optional LLM behind feature flag).
  - Sentence 3 (optional): brief clarifier if needed; still ≤3 sentences total.
  - **Citation:** inject exactly one markdown link using Phase 4 `citation_url` (resolver precedence already applied in 4.5—P4-06, P5-06).
  - **Footer:** `Last updated from sources: <date>` from chunk `effective_date` or crawl metadata—**never invent** (P5-05; Phase 0 footer policy).
- **Number grounding:** prefer values present in retrieved span; flag or omit uncited numerics (P5-09).
- Output: `FactualAnswer` draft (`body_text`, `citation_url`, `footer_date`, `evidence_chunk_id`).

**Deliverable:** Factual composer + tests on canonical FAQ queries (shape, citation, footer rules).

---

### Phase 5.5 — Post-generation validators and repair
**Goal:** Hard-stop non-compliant drafts before anything reaches the user or Phase 6 API.

**Tasks:**
- **Sentence budget:** ≤3 sentences (define tokenizer/heuristic; document semicolon edge case—P5-04).
- **Link policy:** exactly **one** hyperlink; normalize URL (`https://`, Unicode—P5-02, P5-08); host/path must match one of **16** allowlisted Groww URLs (P5-01, P5-07).
- **Prohibited phrases:** advisory/comparison/projection patterns; handle quoted user echo vs model advice (P5-03, P5-13).
- **Footer validator:** required footer present; date matches metadata or approved “unavailable” copy—no fabricated dates (P5-05).
- **Repair path:** on failure, attempt template-only citation/footer injection or fall back to safe refusal/abstention (document precedence).
- Emit `ValidationResult`: `passed`, `violations[]`, `repaired` flag.

**Deliverable:** Validator suite + property tests (link count, allowlist, sentence cap) per `edge-cases/phase-5.md`.

---

### Phase 5.6 — Generation service, red-team evaluation, and Phase 6 handoff
**Goal:** Expose end-to-end `answer(query)` and prove compliance before API/UI integration.

**Tasks:**
- Compose pipeline: **Phase 4.6 `retrieve` → 5.2 → (5.3 | 5.4) → 5.5**.
- Public API: `answer(query) -> AssistantResponse | RefusalAnswer` (or unified envelope with `outcome_type`).
- **Red-team suite:** jailbreak/advisory/comparison/double-link/ wrong-scheme citation cases (`edge-cases/phase-5.md` + architecture deliverable list).
- Offline metrics: compliance pass rate, refusal formatting pass rate, factual format pass rate, allowlist violation count (target: **0**).
- Document **Phase 6 handoff:** request/response JSON schema, error/refusal payloads, validator hooks for `/chat` middleware.

**Deliverable:** Generation service + compliance evaluation report; meets exit criteria below.

---

### Data Contracts
- `GenerationRequest`: `query`, optional `session_id` (no PII); wraps Phase 4 `RetrievalRequest` when calling retrieval inline.
- `ComplianceDecision`: `decision`, `reasons[]`, `performance_limited`.
- `FactualAnswer` / `RefusalAnswer`: `body_text`, `citation_url`, `citation_markdown`, `footer_line`, `evidence_chunk_id` (factual only).
- `ValidationResult`: `passed`, `violations[]`, `repaired`.
- `AssistantResponse`: final user-visible payload after validation (≤3 sentences + one link + footer).

### Deliverables (phase rollup)
- Compliance middleware package (pre-gen engine + post-gen validators).
- Refusal and factual response composers.
- Red-team prompt suite for jailbreak/advisory attempts.
- Phase 6 handoff document (API shapes + middleware integration points).

### Exit Criteria
- **100%** pass on compliance test suite for refusal and formatting checks.
- Zero allowlist violations in red-team and regression runs.
- Factual answers grounded in retrieved evidence; advisory/comparison paths never invoke factual composer.
- Footer date policy respected (no invented source dates).

---

## Phase 6: API and UI Experience
### Goal
Expose the assistant through a simple, safe, user-friendly interface—wrapping Phase 5.6 `GenerationService` behind a validated `/chat` API and a minimal chat UI.

Implement **Phase 6** in order via the subphases below; each subphase should be shippable and reviewable on its own before starting the next.

### Phase 6 overview (rollup)
- Load Phase 5.6 handoff (`phase6_generation_handoff.json`) and wire `GenerationService.answer()` as the single generation entrypoint.
- Backend **`POST /chat`** with request validation, size limits, and guardrail middleware (no bypass of Phase 5.5 validators).
- Standardized JSON for factual, refusal, and abstention outcomes; safe HTTP errors (no stack traces to clients).
- Minimal UI: welcome message, **three factual sample questions**, visible disclaimer (`Facts-only. No investment advice.`), clear single citation link.
- **Stateless / ephemeral** sessions; structured logs with **no PII** (align with `edge-cases/phase-6.md`).

---

### Phase 6.1 — Workspace, configuration, and Phase 5 handoff
**Goal:** Define Phase 6 project layout and confirm Phase 5 generation contracts load—no HTTP server or UI yet.

**Tasks:**
- Directory layout under `phases/phase-6-api-ui/` (`config/`, `api/`, `ui/`, `artifacts/`, `tests/`).
- Load `phase6_generation_handoff.json` from Phase 5.6 (API surface, `AnswerEnvelope`, middleware hooks, error/refusal shapes).
- Pin runtime config: bind host/port, max request body size, CORS policy (dev vs prod), log redaction rules.
- Resolve import path to `GenerationService` (`phase_5_6.service`) and `.env` loading for Groq (read-only from Phase 5.4; no duplicate composer logic).
- Dry entrypoint: validate handoff JSON + config; instantiate `GenerationService`; exit without serving traffic.

**Deliverable:** Config + Phase 5 handoff validation documented; dry load passes.

---

### Phase 6.2 — API foundation and request validation
**Goal:** Stand up a minimal backend app with health checks and strict inbound validation before `/chat` exists.

**Tasks:**
- Choose lightweight framework (e.g. FastAPI or Flask) and version-pin in `requirements.txt`.
- Implement `GET /health` (or `/healthz`) for liveness; optional readiness probe that confirms Phase 4 indexes + Phase 5 service import.
- **Request validation middleware:**
  - enforce `Content-Type: application/json` (P6-03),
  - max body size / max `query` length (P6-01),
  - reject null bytes and invalid UTF-8 (P6-02),
  - optional `session_id` string with length cap; **never** accept PAN/Aadhaar/OTP fields.
- Structured request logging: query length, outcome type, latency—**no raw user PII** in persistent logs (P6-10).
- Unit tests for validation edge cases from `edge-cases/phase-6.md`.

**Deliverable:** Runnable API skeleton with health route + validation middleware + tests.

---

### Phase 6.3 — `/chat` endpoint and generation service integration
**Goal:** Expose `POST /chat` that delegates to Phase 5.6 and returns `AnswerEnvelope` JSON unchanged in shape.

**Tasks:**
- Implement `POST /chat` per handoff suggestion:
  - request: `{ "query": string, "session_id"?: string }`,
  - response: `AnswerEnvelope` (`outcome_type`, `assistant`, `display_text`, `validation_passed`, `audit`, …).
- Wire call chain: validate request → `GenerationService().answer(GenerationRequest(...))` → serialize envelope.
- **Guardrail middleware (policy-first):** do not render or stream partial drafts; return only post–Phase 5.5 `assistant` payload (P6-11).
- If `validation_passed=false`, return safe user copy from validator output—never leak non-compliant draft text (Phase 5 handoff).
- Configurable server timeout; map internal errors to generic 502/503 without stack traces (P6-09).
- Integration tests: canonical factual query, advisory refusal, abstention path; assert allowlisted citation in response.

**Deliverable:** Working `/chat` endpoint backed by Phase 5.6; integration test suite green.

---

### Phase 6.4 — Standardized error, refusal, and abstention HTTP payloads
**Goal:** Consistent API semantics for all non-happy paths so UI and future clients handle outcomes uniformly.

**Tasks:**
- Document HTTP status policy:
  - **200** for successful envelope delivery (including `outcome_type=refusal|abstention`—policy outcomes are not HTTP errors),
  - **400** validation failures, **413** oversize body, **415** wrong content-type, **429** optional rate limit, **502/503** upstream/index failures.
- Normalize error JSON: `{ "error": { "code", "message" } }`—no internal exception strings.
- Map Phase 5 refusal types (`advisory`, `comparison`, `mixed_intent`, …) to stable `assistant.refusal_type` + `display_text` for UI branching.
- Abstention: weak-evidence copy with single allowlisted link when present; document default citation behavior.
- Contract tests asserting JSON schema stability against `phase6_generation_handoff.json`.

**Deliverable:** API error/refusal contract doc + contract tests; OpenAPI or equivalent schema stub optional.

---

### Phase 6.5 — Minimal chat UI (welcome, samples, disclaimer, citation)
**Goal:** Ship a browser UI that meets specification UX and compliance visibility requirements.

**Tasks:**
- Static or SPA frontend (team choice) served by Phase 6 backend or separate dev server with documented CORS.
- **Welcome message** explaining facts-only scope and HSBC Groww corpus.
- **Three sample questions**—purely factual prompts only (P6-05); click fills input and submits to `/chat`.
- Persistent visible disclaimer: `Facts-only. No investment advice.` (contrast-safe styling—P6-04).
- Render assistant reply:
  - body text (≤3 sentences),
  - **one** citation as clear hyperlink (`citation_markdown` or `citation_url`),
  - footer line (`Last updated from sources: …`),
  - `rel="noopener noreferrer"` on external links (P6-06).
- **Security:** sanitize rendered markdown; allowlist `href` to the **16** Groww URLs in client renderer (P6-07); debounce submit / prevent double-submit (P6-08).
- Mobile-friendly layout; footer visible on key breakpoints (P6-12); plain-text copy fallback includes full URL (P6-13).

**Deliverable:** Functional chat UI meeting mandatory UX elements; component or E2E tests for disclaimer + citation presence.

---

### Phase 6.6 — End-to-end integration, UX validation, and Phase 7 handoff
**Goal:** Prove full browser → API → retrieval → generation → validation loop and freeze handoff for QA/observability work.

**Tasks:**
- End-to-end run: UI sample questions + manual spot-check matrix (expense ratio, exit load, refusal, comparison) against live `/chat`.
- UX validation checklist: welcome, 3 samples, disclaimer, single citation, footer, error states (offline/502—P6-09).
- Optional: simple rate limiting or request debounce at API edge for demo deployment.
- Document **Phase 7 handoff:** `/chat` OpenAPI/schema, UI test selectors, log fields for metrics (latency, `outcome_type`, `validation_passed`, allowlist violations).
- Artifact: `phase6_e2e_validation_report.json` (pass/fail per checklist item).

**Deliverable:** E2E validation report + Phase 7 handoff document; meets exit criteria below.

---

### Data Contracts
- `ChatRequest`: `query` (required), `session_id` (optional, ephemeral).
- `ChatResponse`: Phase 5 `AnswerEnvelope` JSON (no field renames without version bump).
- `AssistantPayload`: post-validation `assistant` object (`body_text`, `citation_url`, `citation_markdown`, `footer_line`, `disclaimer_line`, `display_text`, …).
- `ApiError`: `{ "error": { "code", "message" } }` for transport/validation failures only.

### Deliverables (phase rollup)
- Functional chat UI + `/chat` API integration.
- Request validation and guardrail-first middleware (Phase 5.5 never bypassed).
- UX validation for mandatory elements and policy text.
- Phase 7 handoff (schemas, test hooks, log field map).

### Exit Criteria
- End-to-end factual queries return compliant response shape (≤3 sentences, one allowlisted citation, footer present).
- Refusal and abstention paths render correctly in UI with disclaimer visible.
- No PII persisted; validation and policy failures never expose raw non-compliant drafts to users.
- Phase 6 E2E checklist passes on agreed browser matrix (desktop + one mobile breakpoint).

---

## Phase 7: Observability, QA, and Acceptance Testing
### Goal
Measure reliability, compliance, and source freshness against the live system before release—then automate regression packs, surface results in a dashboard, and complete manual QA with a go-live sign-off.

Implement **Phase 7** in order via the subphases below; each subphase should be shippable and reviewable on its own before starting the next. All implementation lives under `phases/phase-7-qa-observability/` (`phase_7_1/`, `phase_7_2/`, `phase_7_3/`, `config/`, `artifacts/`, `tests/`).

### Phase 7 overview (rollup)
- **7.1 — Metrics collection:** measure four core metrics against the live API + retrieval stack (measurement only—no UI or final reports).
- **7.2 — Automated test packs:** factual, refusal, and edge-case suites with pass/fail verdicts, building on 7.1 metric hooks.
- **7.3 — Dashboard, manual QA, go-live:** visual test dashboard, manual citation/footer checklist, go-live risk sign-off, and `phase7_acceptance_report.json`.
- **Inputs:** Phase 6.6 handoff (`phase7_handoff.md`, `phase6_e2e_validation_report.json`), live `/chat` API, Phase 4 retrieval service, 16-url allowlist.

---

### Phase 7.1 — Metrics collection
**Goal:** Instrument and measure the four core quality metrics against the **live** system. Purely measurement—no dashboard UI and no acceptance report yet.

**Prerequisites:** Phase 6 API + UI running; Phase 4 indexes loaded; Phase 6.6 E2E baseline green.

**Tasks — measure these four metrics:**

| Metric | What to measure | Data sources |
|--------|-----------------|--------------|
| **Retrieval hit quality** | Did the right chunk/evidence come back for factual queries? (scheme match, facet relevance, top-1 chunk correctness vs benchmark) | Phase 4 retrieval/rerank outputs, `/chat` audit fields, optional labeled query→chunk pairs |
| **Refusal accuracy** | Did advisory, comparison, and performance-projection queries receive `outcome_type=refusal` (or agreed abstention)? | `/chat` responses, Phase 4.2 intent labels, refusal scenario queries |
| **Format compliance rate** | Share of responses with ≤3 sentences, exactly one citation, footer present (`Last updated from sources:`), allowlisted URL | Phase 5.5 validator output, `validation_passed`, `assistant` payload shape |
| **Source freshness SLA** | Are all **16** allowlisted Groww URLs reachable (HTTP 200) and within agreed freshness window vs ingestion metadata? | Source registry, ingestion timestamps, scheduled HEAD/GET probes |

**Tasks (implementation):**
- Directory layout: `phases/phase-7-qa-observability/phase_7_1/`.
- Config for API base URL, sample sizes, freshness SLA thresholds (hours/days), allowlist path.
- CLI/runner that executes metric probes against live `/chat` and source URLs; emit structured JSON per metric (no HTML dashboard).
- Reuse Phase 6 log fields: `latency_ms`, `outcome_type`, `validation_passed`, allowlist violation counts (target: 0).
- Artifact: `artifacts/metrics/phase7_1_metrics_snapshot.json` (timestamped raw measurements).

**Deliverable:** Repeatable metrics collection runner + JSON snapshots for all four metrics.

**Exit criteria:**
- All four metrics produce numeric scores/counts from a live run (not mocked).
- Metric definitions documented in `phase_7_1/README.md`.
- No dashboard or go-live report in this subphase.

---

### Phase 7.2 — Automated test packs
**Goal:** Build and run three automated test suites that produce **pass/fail verdicts**, using 7.1 metric hooks where applicable.

**Prerequisites:** Phase 7.1 metrics runner available; live `/chat` endpoint.

**Tasks — three test suites:**

1. **Factual query pack (30+ queries)**
   - Cover all allowed factual facets (A1–A7) across the 16 schemes where applicable.
   - Each case: query, expected `outcome_type=factual`, expected scheme/citation URL (one of 16), optional expected facet keyword in answer.
   - Assert: format compliance (≤3 sentences, one allowlisted citation, footer present).

2. **Refusal scenario pack (15+ queries)**
   - Advisory, comparison, performance-projection, and mixed-intent prompts.
   - Each case: query, expected `outcome_type=refusal` (or documented abstention).
   - Assert: citation still one of 16 allowlisted URLs; no investment advice in body.

3. **Edge case pack**
   - Ambiguous wording, mixed intent (factual + advisory), typos, empty/near-empty input, PII-bearing queries, non-HSBC AMC mentions, prompt-injection attempts.
   - Assert: safe outcome (refusal/disambiguate/validation error); no PII echoed in assistant text.

**Tasks (implementation):**
- Directory: `phases/phase-7-qa-observability/phase_7_2/`.
- Pack definitions: `benchmarks/factual_pack.json`, `benchmarks/refusal_pack.json`, `benchmarks/edge_case_pack.json`.
- Runner: `python -m phase_7_2.run_packs` — calls live `/chat`, records latency, compares to expected outcomes.
- Integrate 7.1 checks: retrieval hit (where labeled), format compliance, refusal accuracy per case.
- Artifacts:
  - `artifacts/eval/phase7_2_factual_pack_report.json`
  - `artifacts/eval/phase7_2_refusal_pack_report.json`
  - `artifacts/eval/phase7_2_edge_case_pack_report.json`
  - Rollup: `artifacts/eval/phase7_2_pack_summary.json`

**Deliverable:** Three automated packs with pass/fail reports and rollup summary.

**Exit criteria:**
- Factual pack ≥30 cases; refusal pack ≥15 cases; edge pack covers ambiguous/mixed/typo/PII categories.
- Each pack produces JSON report with per-case `passed`, `expected`, `actual`, `latency_ms`.
- Documented pass thresholds (e.g. ≥95% factual format compliance, 100% refusal accuracy on advisory pack).

---

### Phase 7.3 — Dashboard, manual QA, and go-live checklist
**Goal:** Visualize all metrics and pack results, complete manual QA, and produce the final acceptance artifact with risk sign-off.

**Prerequisites:** Phase 7.1 metrics snapshots; Phase 7.2 pack reports; Phase 6.5 UI available for manual checks.

**Tasks:**
- **Test dashboard**
  - Read-only dashboard (CLI HTML export or minimal static page) showing: retrieval hit quality, refusal accuracy, format compliance rate, source freshness SLA, and 7.2 pack pass rates over time.
  - No new backend logic—visualize 7.1/7.2 JSON artifacts.
- **Manual QA checklist**
  - Spot-check matrix: verify single citation is **one of the 16** allowlisted Groww URLs and matches the answered scheme (or agreed default for refusals).
  - Verify footer date consistency (`footer_line` / `footer_date` vs source metadata).
  - UI checks: welcome, 3 samples, disclaimer, citation link, copy fallback (from Phase 6.6 UX baseline).
  - Artifact: `artifacts/qa/phase7_3_manual_qa_checklist.json` (item, pass/fail, reviewer notes).
- **Go-live checklist**
  - Risk sign-off items: allowlist violations = 0, PII handling, refusal coverage, freshness SLA, E2E 20/20, pack thresholds met.
  - Artifact: `artifacts/qa/phase7_go_live_checklist.json`.
- **Final acceptance report**
  - `artifacts/phase7_acceptance_report.json` — rollup of 7.1 metrics, 7.2 packs, 7.3 manual QA, go-live sign-off, timestamp, overall `accepted: true/false`.

**Deliverable:** Dashboard + manual QA checklist + go-live checklist + `phase7_acceptance_report.json`.

**Exit criteria:**
- Dashboard renders all four core metrics and pack summaries from saved JSON.
- Manual QA checklist completed with documented citation/footer verification samples.
- Go-live checklist signed off (or explicit waivers recorded).
- `phase7_acceptance_report.json` generated; meets specification success criteria with evidence links.

---

### Phase 7 exit criteria (rollup)
- Meets all success criteria from specification with documented evidence in `phase7_acceptance_report.json`.
- Four core metrics measured and within agreed thresholds.
- Automated packs pass at documented rates (factual, refusal, edge).
- Zero allowlist violations in QA runs; no PII in persisted logs or echoed responses.
- Manual QA confirms citation URL and footer date consistency on spot-check matrix.

---

## Phase 8: Deployment, Operations, and Continuous Improvement
### Goal
Run reliably in production with controlled updates.

### Tasks
- Deploy services (API, retriever, UI) with environment-based config.
- Schedule refresh **only** for the **16** allowlisted URLs (re-fetch same paths; do not broaden scope).
- Re-index pipeline with versioning and rollback support.
- Incident playbooks:
  - stale source handling,
  - parser breakage,
  - citation mismatch alerts.

### Deliverables
- Production deployment runbook.
- Monitoring and alert configuration.
- Maintenance SOP for re-fetching the fixed allowlist (URL list changes = architecture/product change, not routine ops).

### Exit Criteria
- Stable production operation with measurable compliance and uptime.

---

## 4) Recommended Component Blueprint

## A. Data and Retrieval
- **Source Registry Store:** JSON/CSV + optional lightweight DB table.
- **Document Store:** Raw + cleaned artifacts in file/object storage.
- **Vector DB:** Any managed/local vector engine (small corpus friendly).
- **Keyword Index:** BM25-like local index for exact term retrieval.

## B. Service Layer
- **Ingestion Worker:** crawl/parse/normalize pipeline.
- **Index Builder:** chunk/embed/upsert pipeline.
- **Query Service:** classify/retrieve/re-rank/generate.
- **Compliance Middleware:** refusal + formatting enforcement.

## C. Interface Layer
- **API Gateway:** request validation, rate limiting, logging.
- **Frontend App:** minimal chat with mandatory disclaimer and examples.

## D. Governance
- **Audit Logger:** prompt intent class, selected source, compliance verdict.
- **No-PII Filter:** masks or drops sensitive tokens before persistence.

---

## 5) End-to-End Runtime Flow
1. User submits query in UI.
2. Intent classifier labels query.
3. If prohibited intent -> refusal response; if a link is required, it must be **one of the 16** allowlisted Groww URLs.
4. If factual intent -> hybrid retrieval from indexed corpus.
5. Re-ranker selects top chunk set from allowlisted content only.
6. Generator produces concise answer from retrieved evidence only.
7. Validator enforces sentence/link/footer constraints.
8. API returns compliant response to UI.
9. Telemetry logs non-PII quality/compliance events.

---

## 6) Compliance-by-Design Rules
- Block advice language patterns (`should I invest`, `best fund`, `which is better`).
- For performance-related questions, respond with factual limitation grounded in allowlisted Groww text; citation = **that scheme’s allowlisted Groww URL** (no external factsheet hosts).
- Reject answers not grounded in retrieved context.
- Never emit more than one citation URL.
- Hard-stop if footer date cannot be resolved from source metadata.

---

## 7) Testing Strategy by Layer
- **Unit Tests:** parser rules, chunker boundaries, sentence/link validators.
- **Integration Tests:** retrieval + re-ranking + response composer.
- **Policy Tests:** advisory/comparison refusal; any link in the response must be allowlist-only.
- **Regression Tests:** canonical FAQ dataset with expected citations restricted to the **16** Groww paths.
- **UAT:** verify all required UI and legal disclaimer elements.

---

## 8) Suggested Timeline (Example)
- **Week 1:** Phases 0-1 (scope freeze + source registry).
- **Week 2:** Phase 2 (ingestion/parsing).
- **Week 3:** Phases 3-4 (indexing + retrieval/re-ranking).
- **Week 4:** Phases 5-6 (guardrails + API/UI).
- **Week 5:** Phases 7.1–7.3 (metrics → test packs → dashboard/QA/go-live), then Phase 8 (deployment, monitoring).

---

## 9) Mapping to Success Criteria
- Accurate retrieval from curated corpus -> Phases 2-4.
- 3-sentence max enforcement -> Phase 5 validator.
- Single valid source citation -> Phases 4-5 policy + output checks.
- Zero advisory responses -> Phase 5 refusal engine + Phase 7.2 refusal pack + Phase 7.1 refusal accuracy metric.

---

## 10) Immediate Next Build Steps
1. **Done (architecture):** AMC = HSBC Mutual Fund; **only** the **16** Groww scheme URLs in [2.1](#21-curated-corpus-urls-hsbc-mutual-fund--groww).
2. Instantiate `source_registry` (CSV/JSON) with **exactly those 16 URLs**—no other rows.
3. Implement ingestion + chunk/index pipeline **strictly** against that registry (allowlist enforcement in fetch layer).
4. Build guardrail-first query service (validators reject any generated link not in the allowlist).
5. Add minimal UI and run compliance test suite.
