# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | NguyenMinhPhuc (TV5) | Claude Code (Opus 5.5) + subagent general-purpose | Tóm tắt đề/lab (README, STARTER, contract, smoke test) | chưa đo | Người đọc lại phần tóm tắt trước khi dùng. |
| 1 | NguyenMinhPhuc (TV5) | Claude Code (Opus 5.5) + subagent general-purpose | Lập plan TV5 (`.claude/plans/001-tv5-qa-harness-phase1.md`) | chưa đo | PRD-0 chưa có → plan dựa trên contract + bảng vai trò TV5. |
| 1 | NguyenMinhPhuc (TV5) | Claude Code (Opus 5.5) + subagent general-purpose | Viết test luật P1 (`tests/test_rules_p1.py`) | chưa đo | Test dựa trên giả định tạm trong `docs/clarify.md`; cần chỉnh khi PO trả lời / PRD-0 mở. |
| 1 | NguyenMinhPhuc (TV5) | Claude Code (Opus 5.5) + subagent general-purpose | Skill pre-push-check (`.agents/skills/`) | chưa đo | Người cần chạy thử skill trước khi dựa vào nó. |
| 1 | NguyenMinhPhuc (TV5) | Claude Code (Opus 5.5) + subagent general-purpose | Khung ma trận AC (`docs/verification/phase-1.md`) và câu hỏi clarify (`docs/clarify.md`) | chưa đo | PRD-0 chưa có → AC tạm, cần người đối chiếu ID chính thức. |
