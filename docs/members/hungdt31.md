# hungdt31 — phản tư cá nhân (≤ 200 từ)

- Vai trò trong nhóm: `qa` (Test, smoke 2 tiến trình, verification) · QA Lead · Dự phòng `client/ui`
- Tôi đã làm (kèm link commit):
  - Phase 1 (`3280d75`): chạy `check_team.py`, unittest, smoke 2 mode, ma trận kiểm chứng đầu tiên.
  - Phase 1 (nhánh `test/p1-qa-verification`): ma trận AC đầy đủ cho 49 test ([phase-1.md](../verification/phase-1.md)); smoke e2e thật gather → kho → quan (money 264, rep 3.6), có kiểm tất định từng byte; viết skill `.agents/skills/qa-verify-phase`.
- Tôi đã review (kèm link):
  - (Cập nhật link PR đã review)
- AI sai ở đâu và tôi phát hiện thế nào:
  - AI nghi `score` 564 là lỗi. Đọc `chonoi/runner.py:34` thì thấy dùng `floor(reputation)`, nên kết quả đúng.
  - Bằng chứng `*.jsonl` trước đây bị `.gitignore` chặn nên chưa từng được commit. Tôi phát hiện khi chạy `git ls-files docs/proof`.
  - PR #8 (bump contract v1.1) vào `main` làm đỏ 16 test. Tôi phát hiện khi chạy lại test trước khi gắn tag.
- Điều tôi học được:
  - Kiểm đúng commit sẽ gắn tag, đừng kiểm "main lúc này". Phải kiểm tra bằng chứng đã thật sự được commit.
