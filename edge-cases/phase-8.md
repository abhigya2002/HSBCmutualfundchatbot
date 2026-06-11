# Edge Cases — Phase 8: Deployment, Operations, and Continuous Improvement

Companion: `phase-wise-architecture.md` §Phase 8.

| ID | Edge case | Why it matters | Expected handling |
|----|-----------|----------------|-------------------|
| P8-01 | Cron refresh widened to “all mutual funds” by mistake | Corpus violation | Config guard: **only** 16 paths from sealed config map |
| P8-02 | Secret rotation breaks embedding API | Silent degradation | Health check fails closed; alert |
| P8-03 | Re-index deploys half of shards | Partial wrong answers | Blue/green or versioned index swap **after** full build |
| P8-04 | Rollback to old index + new code (schema mismatch) | Runtime errors | Pin `index_version` in service config |
| P8-05 | Disk full on raw snapshot store | Ingestion fails mid-run | Quota alerts; atomic batch dirs |
| P8-06 | Groww changes HTML; parser returns empty | Stale or empty answers | Alert on parse success drop; auto-disable answering if below threshold |
| P8-07 | One of 16 URLs permanently 404 | Incomplete corpus | Page-level alert; product decision: keep showing others vs full outage banner |
| P8-08 | Operator “hotfixes” registry in prod DB | Drift from git | Registry changes only via release pipeline |
| P8-09 | Log aggregation ships full request bodies | PII leak | Sampling + scrub fields at edge |
| P8-10 | DST/local time in reports | Confusing SLOs | UTC everywhere in ops dashboards |
| P8-11 | Incident: model suddenly outputs advice | Compliance incident | Kill switch to static refusal; preserve logs for RCA |
| P8-12 | CDN caches old UI disclaimer text | Compliance drift | Cache bust on legal copy change |
| P8-13 | Disaster recovery restores wrong bucket | Wrong corpus version | Bucket versioning + restore drill |

**Test hints:** Chaos test: kill vector dependency; game-day: simulate 404 on one URL; verify alerts and safe degradation path.
