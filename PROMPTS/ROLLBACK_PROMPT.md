# ROLLBACK PROMPT

Use this only if a phase patch breaks baseline.

Inspect git state:

```powershell
git status
git log --oneline --decorate -10
git tag
```

Do not delete or move stable tags.

Rollback meaning:

- `phase1-pass`: clean backend data layer foundation.
- `phase2-pass`: clean FreeLLMAPI extraction/export/audit foundation.

If the current active phase breaks tests and cannot be safely patched, propose rollback to the latest stable tag and explain:

1. Current branch and commit.
2. Current failing tests.
3. Suspected breaking files.
4. Recommended rollback target.
5. Commands needed.

Do not run destructive git commands without explicit user approval.
