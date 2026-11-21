# Sz3RO — Vũ Văn Trường (mở rộng P4: leaderboard, phụ đề SFX)

## Phần mình làm
- Hai mục mở rộng TICKET-04, làm sau Release v1.0.0 (không gắn lại tag):
  - Bảng xếp hạng cục bộ: `--leaderboard`/`--player-name` ở headless, `--export-leaderboard` ở `run_cmd`, top 10 ở GUI.
  - Phụ đề SFX: phím U, tự bật khi tắt tiếng, phụ đề cho ba cảnh báo.
- 17 test, ma trận AC-P4-X01..X09, giả định C-P4-06..10.

## Đã giúp ai
- Thêm mình vào `TEAM.md` (`team_size` 4) để `check_team` không báo lỗi thiếu người.
- Rebase lên commit mới của Minh, giữ cả hai mục trong nhật ký AI khi xung đột.

## AI sai ở đâu
- Lúc gõ tên ở màn tổng kết, phím H/T vẫn là phím tắt. Phát hiện khi đọc lại `main.js`, kiểm lại bằng script Chrome headless.
- `pkill -f` khớp luôn chính shell của nó → không dùng nữa.

## Bài học
Chia commit nhỏ theo từng lát và chạy `pre-push-check` trước mỗi lần push. Ghi rõ khi sửa file khung (`chonoi/live.py`). Kiểm qua script `?debug` chưa thay được chơi tay.

## Commit & bằng chứng
`b47e962` · `8317e0f` · `67c5d8f` · `30fc2b9` · `3660aa9` · `1c4bcd6` · `a3698dd` · `11b611e` · `aa0800f`. Bằng chứng: `docs/proof/phase-4/ext/`.
