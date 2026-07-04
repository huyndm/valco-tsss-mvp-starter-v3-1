# QUALITY_GATES.md

## Mandatory Backend Quality Gate

From backend folder:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

If format check fails:

```powershell
.\.venv\Scripts\python.exe -m ruff format .
.\.venv\Scripts\python.exe -m ruff format --check .
```

Then rerun:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

## Baseline Protection Checklist

Before final response, confirm:

- Existing Phase 2 routes still exist.
- FreeLLMAPI direct-provider guard still exists.
- Raw cap 1,000 remains enforced.
- Dedup-before-hard-filter remains enforced by route logic/tests.
- Top10 still comes from eligible pool.
- Final3 remains analyst/user selected.
- Missing data is not fabricated.
