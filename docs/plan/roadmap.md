# Lộ trình 4 phase (đọc từ lab board)

Người ghi: Võ Hồng Lương (D). Chi tiết từng phase: [Phase 2](phase-2.md), [Phase 3](phase-3.md), [Phase 4](phase-4.md); Phase 1 xong, xem `docs/verification/phase-1.md`. Trạng thái việc ở Google Sheet, tab "Phân công".

| Phase | Tài liệu | Giờ | Bản chất | Contract | Hạn tag |
|---|---|---|---|---|---|
| 1 | PRD-0 | 0:00–1:00 | Lõi: `gather` và `quan` độc lập, kho đếm | v1.0 | `phase-1` 1:00 (đã gắn) |
| 2 | Ticket-02 | 1:00–1:55 | Mở rộng: số chuẩn, Cá Sấu, 2 bếp 4 bàn 6 món, `--mode day`, Shop, pause, HUD | v1.1 | `phase-2` 1:55 |
| 3 | Ticket-03 | 1:55–2:30 | Change request làm vỡ schema: kho cá thể có độ tươi | v1.2 | `phase-3` 2:30 |
| 4 | Ticket-04 | 2:30–3:00 | Hiệu năng, cảnh báo, soak, đóng gói, Release | v1.3 | `phase-4` và Release `v1.0.0` 3:00 |

## Việc xuyên suốt (không đợi phase nào)

- Mỗi người ≥ 3 commit có nội dung bằng tài khoản có trong `TEAM.md` (hiện B và C chưa đủ; tài khoản của B lệch `TEAM.md`).
- Hồ sơ cá nhân `docs/members/<handle>.md`, nhật ký AI, standup giữa phase, retro nhanh Phase 2 (Ticket-02 mục 5) và retro cuối Phase 4.
- Mỗi phase có `docs/verification/phase-n.md` khớp commit gắn tag; hồi quy các phase trước còn hiệu lực; test cũ bị thay phải ghi lý do.
- `main` luôn chạy được, nhất là lúc gắn tag.

## Phụ thuộc giữa các phase (để làm sớm)

1. **Phase 3 làm vỡ schema kho** (đề của Phase 2 chưa nói trước). Gợi ý của nhóm, không phải của đề: ở Phase 2, giữ đọc và ghi kho qua một chỗ duy nhất (`chonoi/inventory.py`) và cho sim giữ giỏ và kho qua một lớp nhỏ, để đổi sang cá thể ở Phase 3 mà không sửa khắp nơi. Tránh viết tay danh sách `hold` và `stock` rải rác trong code Phase 2.
2. **Phase 4 cần `--mode day` và UI chạy được từ clone sạch:** viết README và lệnh chạy ngay từ Phase 2 để không dồn đến phút cuối.
3. **Soak (Phase 4) dùng chế độ `day` của Phase 2:** `day` phải chạy ổn định nhiều Ngày, id cá thể và số Ngày tiếp tục xuyên suốt; thử `day --days 5` thường xuyên.
4. **Bench (Phase 4) cần cảnh lặn vẽ được:** giữ cảnh vẽ tách khỏi sim (chỉ đọc snapshot) từ Phase 2.

## Thứ tự phân công đề xuất (cả 4 phase)

| Người | Phase 2 | Phase 3 | Phase 4 |
|---|---|---|---|
| A (Nhật) | cá bơi và sinh cá, Shop | gather cá thể, `day` bàn giao | bench |
| B (Tú) | quán 2 bếp 4 bàn 6 món | quán cá thể, giữ chỗ theo id | đóng gói (README, CHANGELOG, CREDITS, LICENSE, CI) |
| C (Cường) | Cá Sấu và Máu, menu và HUD | HUD độ tươi | cảnh báo, tương phản cao, điều phối retro |
| D (Lương) | contract v1.1, `day`, smoke, tag | schema và adapter, smoke, hồi quy, tag | contract v1.3, soak, clone sạch, Release |

D giữ vai Integrator nên là điểm nghẽn ở cả ba phase; khi trễ, người dự phòng trong `TEAM.md` nhận việc (C dự phòng D, D dự phòng C, A và B dự phòng nhau).
