# SELF CHECK PROMPT

Before final response, self-check:

## Rule Files Read

Confirm these were read:

- AGENTS.md
- REPO_CONTEXT.md
- SKILL_REPO.md
- VALCO_RULES.md
- PROJECT_WORKFLOW.md
- BASELINE_PHASE1_PHASE2.md
- CODE_UI_DEBUGFIX_RULES.md
- ROADMAP_PHASES.md
- QUALITY_GATES.md
- active phase task file

## Baseline Check

- Phase 1 baseline knowledge retained.
- Phase 2 baseline knowledge retained.
- Existing Phase 2 routes preserved.
- No direct provider LLM call introduced.

## Code/UI/DebugFix Check

- Code build rules followed.
- UI rules followed if UI changed.
- DebugFix loop followed if tests failed.
- No test deletion or weakening.
- No scope expansion.

## Quality Gate

Report exact results of:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```
