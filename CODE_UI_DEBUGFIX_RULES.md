# CODE_UI_DEBUGFIX_RULES.md

## Code Build Rules

- Inspect before editing.
- Use existing code style and architecture.
- Reuse existing models/services/routes.
- Keep patches minimal.
- Do not rewrite the project.
- Do not rename public routes unless active phase requires it.
- Do not remove tests.
- Do not modify stable business rules to make tests pass.
- Add tests for new routes and critical guardrails.

## Backend Route Rules

- Use deterministic service calls.
- Validate project existence where applicable.
- Preserve existing Phase 2 routes.
- Keep raw candidate cap 1,000.
- Dedup route must execute before hard filter in workflow usage.
- Hard filter route must preserve rejected/flagged records rather than silently dropping.
- Scoring/top10 route must source only from eligible candidates.

## UI Build Rules

- Build only minimal dashboard required by active phase.
- Keep pages simple and functional.
- Do not over-design.
- Avoid complex state management unless project already has it.
- UI should reflect workflow stages clearly:
  1. Project
  2. Subject asset
  3. Raw candidates
  4. Extraction results
  5. Eligible/top10
  6. Export/audit
  7. Gateway health
- UI must not imply that LLM selects final3 or final value.
- UI should leave final3 as analyst/user decision.

## DebugFix Loop

When failure occurs:

1. Copy exact failing command and error.
2. Locate failing test/file/function.
3. Determine if failure is from new change or environment.
4. Patch smallest code area.
5. Rerun the focused failing test.
6. Rerun full pytest.
7. Rerun ruff check.
8. Rerun ruff format --check.
9. If format fails, run ruff format and rerun gates.

## Forbidden Debug Shortcuts

- Do not delete tests to pass.
- Do not weaken business guardrails.
- Do not add broad try/except to hide bugs.
- Do not suppress all warnings globally.
- Do not bypass no-direct-provider guard.
- Do not fabricate data in tests or fallback unless explicitly synthetic test fixture.
