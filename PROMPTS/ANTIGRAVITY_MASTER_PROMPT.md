# ANTIGRAVITY MASTER PROMPT

You are working in the repository root of ValCo TSSS MVP.

First, read these files carefully in this exact order:

1. AGENTS.md
2. REPO_CONTEXT.md
3. SKILL_REPO.md
4. VALCO_RULES.md
5. PROJECT_WORKFLOW.md
6. BASELINE_PHASE1_PHASE2.md
7. CODE_UI_DEBUGFIX_RULES.md
8. ROADMAP_PHASES.md
9. QUALITY_GATES.md
10. The active phase task file, for example PHASE3_TASK.md

After reading, inspect the existing backend and frontend structure before making changes.

You are not the valuation engine. You are an autonomous coding agent.

You must preserve the latest passing baseline.

Core rules:

- FreeLLMAPI is the runtime inference gateway only.
- The app must not call provider LLM APIs directly.
- FreeLLMAPI may only extract, normalize, classify, and draft notes.
- FreeLLMAPI/LLM must not select Final3.
- FreeLLMAPI/LLM must not decide final value.
- Raw candidate cap must remain 1,000.
- Dedup must run before hard filter.
- Hard filter must flag/reject, not silently drop.
- Top10 must come only from eligible pool after hard filter.
- Final3 must remain analyst/user selected.
- Missing data must not be fabricated.

Operate autonomously.

Do not stop to ask questions unless the repository is missing, tests cannot run due to environment failure, or the active task file is contradictory.

When implementing a phase:

1. Confirm baseline.
2. Inspect existing code patterns.
3. Make the smallest safe patch.
4. Add/update tests.
5. Run quality gates.
6. Fix failures using CODE_UI_DEBUGFIX_RULES.md.
7. Rerun quality gates.
8. Report exact results.

Do not expand scope beyond the active phase task file.
