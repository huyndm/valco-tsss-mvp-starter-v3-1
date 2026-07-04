# PHASE3_TASK.md

## Phase 3 Scope

Implement only:

1. Backend workflow routes still missing.
2. Minimal frontend dashboard.

Do not implement crawler, RAG, advanced observability, or unrelated features.

## Backend Routes To Add

```text
POST /api/v1/projects
GET  /api/v1/projects
GET  /api/v1/projects/{project_id}

POST /api/v1/projects/{project_id}/subject-asset
GET  /api/v1/projects/{project_id}/subject-asset

POST /api/v1/projects/{project_id}/raw-candidates
GET  /api/v1/projects/{project_id}/raw-candidates

POST /api/v1/dedup/run/{project_id}
POST /api/v1/hard-filter/run/{project_id}
POST /api/v1/scoring/run/{project_id}

GET  /api/v1/top10/{project_id}
```

## Frontend Minimal Dashboard

- ProjectListPage
- SubjectAssetInputPage
- ManualRawCandidateInputPage
- RawCandidatePoolPage
- ExtractionResultsPage
- ExportAuditPage
- GatewayHealthPanel

## Backend Tests To Add

- `test_project_routes.py`
- `test_raw_candidate_routes.py`
- `test_dedup_route.py`
- `test_hard_filter_route.py`
- `test_scoring_top10_route.py`

## Required Behavior

- Raw candidate cap must remain 1,000.
- Dedup must run before hard filter.
- Hard filter must flag/reject, not silently drop.
- Top10 must come only from eligible pool after hard filter.
- Final3 remains analyst/user selected.
- Missing data must not be fabricated.
