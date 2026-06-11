# Edge Cases — Phase 1: Corpus Curation and Source Registry

Companion: `phase-wise-architecture.md` §Phase 1.

| ID | Edge case | Why it matters | Expected handling |
|----|-----------|----------------|-------------------|
| P1-01 | Duplicate row with same path but trailing slash | Registry count > 16 or duplicate index keys | Canonicalize to **exact** URL string from architecture; reject duplicates |
| P1-02 | `http://` vs `https://`, or `www.` prefix | Allowlist bypass or fetch mismatch | Normalize to canonical **https://groww.in/...** only |
| P1-03 | URL-encoded variants of same path | False negative on allowlist check | Decode once for comparison; store canonical form |
| P1-04 | Manual edit introduces UTM params (`?utm=`) | Fetch/cache key fragmentation | Strip tracking params in **comparison** only; persist canonical path |
| P1-05 | `scheme` slug typo vs URL path | Metadata inconsistency | Derive `scheme` from path or single validated mapping table |
| P1-06 | 17th URL sneaks in via merge conflict | Breaks exit criteria | CI/assert: `len(registry) == 16` |
| P1-07 | `active: false` on one URL “temporarily” | Partial corpus without explicit product decision | Either all active or document product exception; avoid silent 15-URL index |
| P1-08 | `published_date` unknown for Groww HTML | Footer date logic undefined | Use `last_fetched_at` + document “as shown on page as of crawl” per Phase 5 contract |
| P1-09 | Case sensitivity in hostname `Groww.in` | Allowlist false negative | Lowercase host before compare |
| P1-10 | Unicode lookalike characters in URL | Security / wrong fetch | Reject non-ASCII path or strict ASCII allowlist match |
| P1-11 | Registry JSON loads arbitrary extra keys per row | Silent schema drift | Strict schema validation (e.g. only allowed columns) |
| P1-12 | Two schemes share very similar slugs | Wrong citation mapping | Human-readable `scheme_name` + unique `scheme_id` in registry |

**Test hints:** Unit test canonical URL equality; snapshot test registry row count and hash of sorted URLs.
