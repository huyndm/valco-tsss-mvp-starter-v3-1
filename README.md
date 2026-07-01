# ValCo TSSS MVP Phase 1 Ready V3.1

Phase 1 đã áp dụng: backend data layer + pipeline nền.

Pipeline khóa cứng:
raw candidate search up to 1,000 → dedup → FreeLLMAPI extraction/normalization → hard filter → eligible pool → deterministic scoring/ranking → Top 10 recommended → analyst/user final 3 → export/audit.

## Run backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Notes
- Phase 1 chưa gọi FreeLLMAPI thật; chỉ giữ gateway guard/stub.
- Phase 2 mới nối extraction_service gọi FreeLLMAPI và export/audit nâng cao.
