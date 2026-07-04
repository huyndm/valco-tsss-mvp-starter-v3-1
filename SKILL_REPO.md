# SKILL_REPO.md

## Purpose

This file converts the ValCo Claude Code Enterprise Brain + UI DebugFix Integrated V3.1 context into agent-readable project skills.

The agent must treat this as the repository skill layer.

## Skill 1 — Baseline Preservation Skill

Before every patch:

1. Inspect current repo structure.
2. Identify existing models/services/routes/tests.
3. Preserve previous phase behavior.
4. Avoid full rewrites.
5. Use smallest safe patch.
6. Keep tests and ruff clean.

## Skill 2 — TSSS Deterministic Pipeline Skill

The TSSS workflow is deterministic after extraction:

```text
raw candidates up to 1,000
→ dedup
→ extraction/normalization
→ hard filter
→ eligible pool
→ deterministic scoring/ranking
→ Top10 recommended
→ analyst/user final3
→ export/audit
```

The agent must never shortcut raw candidates directly into Top10.

## Skill 3 — FreeLLMAPI Gateway Skill

FreeLLMAPI is a gateway only.

Allowed:

- extract
- normalize
- classify
- draft note

Forbidden:

- select final3
- decide final value
- bypass deterministic filters
- bypass analyst/user decision
- call provider APIs directly

## Skill 4 — Evidence/Audit Skill

Every workflow decision must be traceable.

- Hard filter must flag/reject, not silently drop.
- Final3 override must have audit log.
- Export must include audit workbook sheets.
- Missing data must be explicit, not fabricated.

## Skill 5 — Backend Code Builder Skill

When adding backend features:

1. Follow existing FastAPI route patterns.
2. Reuse SQLModel models/session patterns.
3. Reuse service layer if available.
4. Add schemas only when needed.
5. Keep route behavior deterministic.
6. Add route tests for success and important guardrails.
7. Do not introduce direct provider calls.

## Skill 6 — Frontend UI Builder Skill

When adding frontend dashboard:

1. Build minimal functional pages only.
2. Do not over-design.
3. Keep UI aligned with workflow stages.
4. Show data/status clearly.
5. Provide manual analyst/user actions where required.
6. Do not create UI that implies LLM chooses final3 or final value.
7. Do not add complex state management unless existing app uses it.

Required Phase 3 minimal UI:

- ProjectListPage
- SubjectAssetInputPage
- ManualRawCandidateInputPage
- RawCandidatePoolPage
- ExtractionResultsPage
- ExportAuditPage
- GatewayHealthPanel

## Skill 7 — DebugFix Integrated Skill

When checks fail:

1. Read exact failure.
2. Identify root cause.
3. Patch smallest code section.
4. Rerun focused failing test.
5. Rerun full quality gate.
6. Do not mask failures by weakening tests unless test expectation is provably wrong.
7. Do not delete tests to pass.
8. Do not suppress warnings unless active phase requires it.

## Skill 8 — Scope Control Skill

Never implement future-phase work unless explicitly approved in active phase task.

Examples forbidden in Phase 3:

- crawler
- RAG
- advanced observability
- production auth/roles
- deployment pipeline
- document ingestion automation
- final valuation engine
- LLM-selected final3

## Skill 9 — Missing Data Safety Skill

If data is missing:

- do not fabricate;
- use null/TODO/safe fallback;
- mark insufficient_data where appropriate;
- during extraction fallback, copy only fields already present from RawCandidate.

## Skill 10 — Reporting Skill

Every final response must include:

- files created;
- files modified;
- tests added/modified;
- commands run;
- exact results;
- remaining warnings;
- baseline preservation check;
- scope compliance check.
