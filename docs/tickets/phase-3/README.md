# Tickets — Phase 3 (contract v1.2, change request "Mùa Nước Nổi")

Spec: `docs/specs/phase-3.md` · Quyết định: `docs/adr/0001-kho-ca-the-va-do-tuoi.md`.
Điều kiện vào: `phase-1` và `phase-2` đã tag; `phase-2` xong thì ticket 04 mới có nghĩa.

| # | Ticket | Blocked by | Người | Ghi chú |
|---|---|---|---|---|
| 01 | Adapter kho cá thể + contract v1.2 | — | Cao Minh | Mở đường; main phải xanh suốt |
| 02 | Lặn: id/fresh/hao/`spoiled`/LIFO | 01 | Nhật Minh | |
| 03 | Quán: kho cá thể, giữ theo id, giá theo tươi | 01 | Đức Minh | Phần khó nhất |
| 04 | Bàn giao `day` + Chợ + CHANGELOG | 01, (02, 03) | Cao Minh | Cần P2 xong |
| 05 | HUD độ tươi / hàng ươn | 01 (mềm 02, 03) | Vinh | Client-only |
| 06 | QA migration + regression + ngưỡng 30 | 01 | Văn Minh | Cổng chặn |
| 07 | Mở rộng: dòng nước lũ (`current`) | 02 | Nhật Minh | ≥1 mục cho nhóm 5 |
| 08 | Mở rộng: khách đặt trước (`reservations`) | 03 | Đức Minh | Mục thứ 2 nếu đủ thời gian |

**Nhịp tích hợp:** 01 trước (kèm test migration đỏ → xanh), rồi 02/03/05 song song, 06 chạy liên tục,
04 khi P2 có `day`, cuối cùng 07/08. Bật v1.2 chỉ khi 02 và 03 cùng xong.

**Chống conflict:** `chonoi/inventory.py` + `contract.py` + `runner.py` → chỉ Cao Minh.
`gather*.py` → Nhật Minh. `quan*.py` → Đức Minh. `web/index.html` → Vinh. `tests/` → người làm lát + Văn Minh giữ cổng.
