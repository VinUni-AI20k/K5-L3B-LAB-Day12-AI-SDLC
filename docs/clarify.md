# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 11:52 | Ở Phase 2 (`v1.1`), `invuln_ticks` trong `gather.player` và `--mode day` có còn bị từ chối ở headless không? | Không: `v1.1` mở `--mode day` và cho phép `invuln_ticks >= 0` trong `gather.player` (giá trị âm vẫn thoát mã `2`). | PO (`ngthanhtamtb`) |
| 2 | 2026-11-21 11:52 | Khi Cá Sấu Năm Chèo húc trúng (`monster_hit`), thứ tự rơi `floor(len(hold) * loss_ratio)` thực hiện thế nào và khi `hp == 0` thì sao? | Rơi từ cuối mảng `hold` (LIFO, món mới nhất rơi trước); `invuln_ticks` đặt `90`, cá sấu chuyển `recoil` trong `recoil_ticks` (`60`). Nếu `hp == 0`, xóa sạch phần còn lại và phát `faint` (`cause: "monster"`), `gather_end` (`reason: "fainted"`). | PO (`ngthanhtamtb`) |
