# PHASE 3 EXECUTION PROMPT

Implement Phase 3 only.

Read and follow:

- AGENTS.md
- REPO_CONTEXT.md
- SKILL_REPO.md
- VALCO_RULES.md
- PROJECT_WORKFLOW.md
- BASELINE_PHASE1_PHASE2.md
- CODE_UI_DEBUGFIX_RULES.md
- ROADMAP_PHASES.md
- QUALITY_GATES.md
- PHASE3_TASK.md

Do not break Phase 2 baseline.
Do not implement crawler, RAG, advanced observability, or unrelated features.
Do not allow LLM or FreeLLMAPI to select final3 or decide final value.
Keep FreeLLMAPI as the runtime inference gateway only.
The app must not call provider LLM APIs directly.

Implement the missing backend workflow routes listed in PHASE3_TASK.md.
Implement the minimal frontend dashboard pages/panels listed in PHASE3_TASK.md.
Add the required backend tests.

After coding, run from the backend folder:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

If any check fails, fix and rerun until all pass.

Final response must include:

1. Files created.
2. Files modified.
3. Tests added or modified.
4. Commands run and exact results.
5. Remaining warnings, if any.
6. Confirmation that Phase 2 baseline was preserved.
7. Confirmation that Phase 3 scope was not expanded.
8. Confirmation that SKILL_REPO.md and CODE_UI_DEBUGFIX_RULES.md were followed.
