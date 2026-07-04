# BASELINE_PHASE1_PHASE2.md

## Phase 1 — Completed Baseline

Tag:

```text
phase1-pass
```

Scope completed:

- Backend data layer and pipeline foundation.
- SQLModel database/session SQLite.
- Models:
  - Project
  - SubjectAsset
  - RawCandidate
  - DuplicateResult
  - ExtractionResult
  - EligibleCandidate
  - ScoringResult
  - Top10Recommendation
  - Final3Selection
  - AuditLog
  - ExportRecord
- Services:
  - evidence_service
  - dedup_service
  - hard_filter_service
  - scoring_service
  - selection_service
- llm_client gateway guard/stub, not real FreeLLMAPI call in Phase 1.
- Tests:
  - raw pool cap 1,000
  - dedup
  - hard filter adjustment >40%
  - scoring/top10
  - insufficient data status
  - final3 selection
  - no direct provider

Validation:

```text
pytest: 6 passed
ruff check: All checks passed
ruff format --check: 18 files already formatted
phase1-pass pushed
```

## Phase 2 — Completed Baseline

Tag:

```text
phase2-pass
```

Scope completed:

- `llm_client.py` upgraded:
  - async chat_completion
  - check_health
  - GatewayUnavailableError
  - blocks direct provider URLs
- `extraction_service.py`:
  - Pydantic extraction schema
  - build messages
  - parse response
  - fallback_from_raw when gateway fails
  - no data fabrication
- `export_service.py`:
  - Excel audit workbook using openpyxl
  - sheets RawCandidates, ExtractionResults, EligibleCandidates, Top10Recommendations, Final3Selections, AuditLog
- API routes:
  - POST /api/v1/extraction/run/{project_id}
  - GET /api/v1/extraction/{project_id}
  - POST /api/v1/export/{project_id}
  - GET /api/v1/audit-log/{project_id}
  - GET /api/v1/gateway/health
- Tests:
  - FreeLLMAPI success/failure
  - extraction success/fallback
  - invalid schema type
  - export workbook
  - gateway health endpoint
  - no-direct-provider guard
- Fixed issues:
  - extraction_service.py broken string/syntax
  - routes.py B008 Depends
  - import sort
  - StrEnum
  - line length
  - Enum value export

Validation:

```text
pytest: 13 passed, 45 warnings
ruff check: All checks passed
ruff format --check: 21 files already formatted
git status: branch main up-to-date with origin/main; working tree clean
git tag phase2-pass: already exists; push origin phase2-pass = Everything up-to-date
```

## Remaining Warnings After Phase 2

- `datetime.utcnow()` deprecated warning on Python 3.14.4.
- FastAPI/Starlette TestClient warning related to httpx/httpx2.

Do not spend Phase 3 scope on these warnings unless they become failures.
