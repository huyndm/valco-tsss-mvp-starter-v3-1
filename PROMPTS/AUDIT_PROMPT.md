# AUDIT PROMPT

Audit the current repository against the full ValCo TSSS MVP rules.

Read:

- AGENTS.md
- REPO_CONTEXT.md
- SKILL_REPO.md
- VALCO_RULES.md
- PROJECT_WORKFLOW.md
- BASELINE_PHASE1_PHASE2.md
- CODE_UI_DEBUGFIX_RULES.md
- ROADMAP_PHASES.md
- QUALITY_GATES.md

Check:

1. Latest baseline is preserved.
2. Existing routes are not broken.
3. FreeLLMAPI remains gateway-only.
4. App does not call provider LLM APIs directly.
5. Raw candidate cap remains 1,000.
6. Dedup occurs before hard filter.
7. Hard filter flags/rejects and does not silently drop.
8. Top10 comes only from eligible pool.
9. Final3 remains analyst/user selected.
10. Missing data is not fabricated.
11. Active phase scope has not expanded.
12. Tests exist for new route/service behavior.
13. UI does not imply LLM final3/final value selection.
14. Debug/fix loop did not weaken tests or business rules.

Run quality gates from backend folder and report exact results.
