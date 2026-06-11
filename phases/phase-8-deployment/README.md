# Phase 8 — Deployment, operations, and continuous improvement

**Architecture:** `phase-wise-architecture.md` (Phase 8).

## Goal

Production deployment, scheduled refresh **only** for the sixteen allowlisted URLs, re-index versioning, incident playbooks.

## Planned artifacts

| Artifact | Description |
|----------|-------------|
| Deployment runbook | Environments, secrets, rollback |
| Monitoring and alerts | Parse failures, staleness, compliance drift |
| Maintenance SOP | Re-fetch fixed allowlist; URL list changes = product/architecture change |

## Exit criteria (from architecture)

- Stable operation with measurable compliance and uptime.

## Edge cases

See [edge-cases/phase-8.md](../../edge-cases/phase-8.md).
