# PROJECT_WORKFLOW.md

## Full Project Workflow

The agent must operate in this sequence:

1. Read repository control files.
2. Confirm repo context and baseline.
3. Inspect current backend/frontend structure.
4. Identify active phase scope.
5. Plan smallest safe patch.
6. Implement backend changes.
7. Implement frontend changes only if active scope requires UI.
8. Add/update tests.
9. Run quality gates.
10. Debug/fix if gates fail.
11. Rerun quality gates.
12. Report exact results.

## No-Question Operating Rule

Do not ask for routine clarifications. Use existing repo structure and active phase file.
Ask only for true blockers.

## Rollback Meaning

- `phase1-pass`: clean backend data layer foundation.
- `phase2-pass`: clean FreeLLMAPI extraction/export/audit foundation.

## PowerShell Venv Rule

If PowerShell blocks activate scripts, do not activate venv. Use:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```
