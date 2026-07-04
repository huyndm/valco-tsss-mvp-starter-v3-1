# CHECKLIST TRƯỚC KHI CHẠY ANTIGRAVITY

## 1. Kiểm repo

```powershell
cd C:\Users\Windows\Desktop\valco\VALCO_TSSS_MVP_PHASE2_READY
git status
git tag
```

Yêu cầu:

- Branch `main`.
- Có tag `phase1-pass`.
- Có tag `phase2-pass`.
- Working tree clean hoặc phải biết rõ file nào thay đổi.

## 2. Kiểm backend baseline

```powershell
cd C:\Users\Windows\Desktop\valco\VALCO_TSSS_MVP_PHASE2_READY\backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

## 3. Kiểm file rule đã gắn vào repo

Root repo phải có:

```text
AGENTS.md
REPO_CONTEXT.md
SKILL_REPO.md
VALCO_RULES.md
PROJECT_WORKFLOW.md
BASELINE_PHASE1_PHASE2.md
CODE_UI_DEBUGFIX_RULES.md
ROADMAP_PHASES.md
QUALITY_GATES.md
PHASE3_TASK.md
PROMPTS\ANTIGRAVITY_MASTER_PROMPT.md
PROMPTS\PHASE3_EXECUTION_PROMPT.md
```
