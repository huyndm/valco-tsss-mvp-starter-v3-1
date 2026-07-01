# ValCo TSSS MVP Phase 2 Ready V3.1

Phase 2 đã áp dụng trên nền Phase 1:

```text
raw candidate search up to 1,000
→ dedup
→ FreeLLMAPI extraction/normalization
→ hard filter
→ eligible pool
→ deterministic scoring/ranking
→ Top 10 recommended
→ analyst/user final 3
→ export/audit
```

## Phase 2 đã thêm
- FreeLLMAPI async chat client + gateway health.
- extraction_service.py với Pydantic schema và fallback an toàn, không bịa dữ liệu.
- export_service.py xuất Excel audit workbook bằng openpyxl.
- API routes: extraction, export, audit-log, gateway health.
- Tests cho gateway, extraction, export, no-direct-provider.

## Chạy backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Ghi chú
- FreeLLMAPI endpoint mặc định: `http://localhost:3001/v1/chat/completions`.
- App không gọi trực tiếp provider LLM.
- LLM không được chọn final 3 TSSS.
