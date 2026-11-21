# Nhật ký dùng AI (theo phase và theo người)

> Mỗi người tự thêm dòng của mình sau mỗi việc dùng AI; TV6 gom và kiểm cuối phase. Token lấy từ `/cost` (Claude Code) hoặc trang usage.

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | thanhhale288 | Claude Code / Opus 5.5 | Đọc repo, research Dave the Diver làm tham chiếu thiết kế; viết `docs/plan/phase-1.md`, thỏa thuận `TEAM.md`, `clarify.md`, `standup.md`; chỉnh nhẹ HUD `chonoi/web/index.html` | (điền từ `/cost`) | AI không đọc được lab board (artifact của người khác) nên không có PRD-0; các câu trong `clarify.md` là giả định từ starter, phải đối chiếu PRD-0 bằng tay |
| 1 | thanhhale288 | Claude Code / Opus 5.5 (lead) + Orca workers: Claude ×2, Cursor ×1 | Điều phối 3 agent song song trên branch `tv6/phase-1-team-ai`, mỗi agent một vùng file: **spec** (Spec Kit specify→clarify→plan→tasks→analyze → `specs/001-phase-1-core/`, 26 FR, AC-P1-01..23, 36 task), **research** (`docs/research/phase-1.md`: bản đồ 14 TODO, Test Contract, edge case), **code** (Cursor: HUD gather/quan trong `chonoi/web/`) | (điền từ `/cost` + usage Cursor) | Spec dựa trên giả định vì không có PRD-0 (analyze báo 1 HIGH: luật quán + thứ tự bước là GIẢ ĐỊNH); research phát hiện `team_size`=4 ≠ 6 người, tên/data event chưa có nguồn; HUD hiện `—` cho trường sim chưa có (boa, `shift_earned`) |
