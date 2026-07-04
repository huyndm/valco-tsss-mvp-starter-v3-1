# ROADMAP_PHASES.md

## Phase 0 — Starter Baseline

Goal:

- Minimal starter repo.
- Backend/frontend skeleton.
- Basic health checks.

Artifact:

```text
VALCO_STARTER_DOWNLOAD_READY.zip
```

## Phase 1 — Backend Data Layer

Status:

```text
DONE / phase1-pass
```

Scope:

- Database/session.
- Core models.
- Evidence/dedup/hard-filter/scoring/selection services.
- Deterministic workflow foundation.

## Phase 2 — FreeLLMAPI Extraction/Export/Audit

Status:

```text
DONE / phase2-pass
```

Scope:

- FreeLLMAPI client.
- Extraction service with safe fallback.
- Export service for Excel audit workbook.
- API routes for extraction/export/audit/gateway.
- Tests.

## Phase 3 — Workflow Routes + Minimal Dashboard

Status:

```text
ACTIVE / NEXT
```

Scope:

- Missing backend workflow API routes.
- Minimal frontend dashboard pages/panels.
- Tests for workflow routes.

Out of scope:

- Crawler.
- RAG.
- Advanced observability.
- Auto valuation engine.
- LLM final3 selection.
- LLM final value decision.

## Future Phases — Not Active Unless Explicitly Approved

Do not implement during Phase 3:

- crawler/data ingestion automation;
- RAG document knowledge base;
- advanced observability/telemetry;
- production auth/roles;
- deployment pipeline;
- multi-tenant access control;
- cloud storage integration;
- full Excel/Word valuation report templates.
