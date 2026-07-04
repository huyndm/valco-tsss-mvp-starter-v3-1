# REPO_CONTEXT.md

## Repository

```text
https://github.com/huyndm/valco-tsss-mvp-starter-v3-1
```

Branch:

```text
main
```

Known local folders:

```text
C:\Users\Windows\Desktop\valco\VALCO_TSSS_MVP_PHASE1_READY
C:\Users\Windows\Desktop\valco\VALCO_TSSS_MVP_PHASE2_READY
```

## Stable Tags

```text
phase1-pass
phase2-pass
```

Do not delete, move, or overwrite these tags.

## Tool Context

- Claude Projects/GitHub: used for reading repo/rule and audit/plan/patch.
- Claude Code CLI: installed but normal/free account was not usable without subscription/API/cloud provider.
- Gemini CLI: no longer supported individual/free login at the time tested.
- Antigravity CLI: installed and now usable when quota is available.
- PowerShell: if activate is blocked, use direct `.venv\Scripts\python.exe` commands.

## Existing Phase 2 Routes To Preserve

```text
/health
/api/v1/tsss/pipeline
POST /api/v1/extraction/run/{project_id}
GET  /api/v1/extraction/{project_id}
POST /api/v1/export/{project_id}
GET  /api/v1/audit-log/{project_id}
GET  /api/v1/gateway/health
```
