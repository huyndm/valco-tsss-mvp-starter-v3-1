# VALCO Antigravity Autonomous Pack V2 FULL

Bộ V2 FULL dùng để gắn vào repo Antigravity/Gemini/AI coding agent để agent tự vận hành theo **toàn bộ quy trình dự án ValCo TSSS MVP**, bao gồm:

- Project workflow toàn repo.
- Skill repo/rule V3.1.
- Code builder discipline.
- UI dashboard discipline.
- Debug/fix loop.
- Phase 1 baseline data.
- Phase 2 baseline data.
- Phase 3 task scope.
- Quality gates pytest/ruff.
- Audit/rollback prompts.

## Cách dùng nhanh

Giải nén toàn bộ nội dung thư mục này vào root repo:

```text
C:\Users\Windows\Desktop\valco\VALCO_TSSS_MVP_PHASE2_READY
```

Hoặc chạy:

```powershell
.\install_to_repo.ps1 "C:\Users\Windows\Desktop\valco\VALCO_TSSS_MVP_PHASE2_READY"
```

Sau đó mở Antigravity tại root repo và paste:

```text
PROMPTS\ANTIGRAVITY_MASTER_PROMPT.md
```

Khi chạy Phase 3 paste tiếp:

```text
PROMPTS\PHASE3_EXECUTION_PROMPT.md
```

## Điểm khác V1

V2 FULL bổ sung rõ các phần V1 còn thiếu/mỏng:

- `SKILL_REPO.md`: skill repo/rule V3.1 ở dạng agent-readable.
- `CODE_UI_DEBUGFIX_RULES.md`: luật dựng code, UI và debug/fix loop.
- `BASELINE_PHASE1_PHASE2.md`: dữ liệu quan trọng Phase 1 và Phase 2 tách riêng để agent không bỏ sót.
- `REPO_CONTEXT.md`: repo/tag/local folder/routes/test results tập trung.
- `PROMPTS/SELF_CHECK_PROMPT.md`: prompt tự kiểm trước/sau khi sửa.
