# Kế hoạch Phase 2 (TICKET-02 — Một ngày ở chợ nổi)

- **Mục tiêu:** contract v1.1 với số chuẩn; cá bơi/sinh, Cá Sấu, 2 bếp/4 bàn, 6 món; chế độ `day` (kế hoạch D1–D5, Shop, pause); menu/HUD. Tag `phase-2` trước 1:55.
- **Nguyên tắc tránh conflict:** mỗi việc một file riêng; `gather.py` và khung chạy (`runner`, `headless`, `inputs`) do Lead giữ và đã nối sẵn lời gọi.

## Việc / người / phụ thuộc

| Việc | Người | File | Phụ thuộc |
|---|---|---|---|
| Contract v1.1 (số chuẩn, 6 nguyên liệu, 6 món, day_plan, shop, monsters), nối lời gọi gather theo thứ tự 4.5, sinh cá đầu ca/theo lịch, `faint` v1.1 | @justapea25 | `game.contract.json`, `chonoi/contract.py`, `gather.py`, `gather_fish.py` (phần sinh) | — (làm đầu tiên) |
| Chế độ `day` + pause (đổi pha, `day_plan`, bàn giao kho, cấp nâng cấp), tích hợp, gắn tag | @justapea25 | `chonoi/day.py` (mới), `runner.py`, `headless.py`, `inputs.py` | contract v1.1, Shop |
| Cá bơi (đổi hướng theo seed, phản xạ mép), bắt cá 3 loài, hái kèo nèo | @LETHESHIYING | `gather_fish.py` (`swim`), `gather_harvest.py` | contract v1.1 |
| Cá Sấu: patrol/chase/hit/recoil, bất tử, mất hàng LIFO, ngất do quái | @minhthu27 | `gather_monsters.py` | contract v1.1 |
| Quán v1.1: 2 bếp/4 bàn, bếp nhận đơn cũ nhất, lọc món theo kế hoạch ngày, luật đóng ca | @viethoang126 | `quan.py`, `quan_customers.py`, `quan_service.py` | contract v1.1 |
| Shop: mua oxygen/hp, `bought`/`buy_failed`, `shop_done`, tự đóng 600 tick; QA: cập nhật test P1 theo số chuẩn, smoke tích hợp (phút 20, 35), `verification/phase-2.md` | @Kaylez-TXL | `chonoi/shop.py` (mới), `tests/`, `docs/proof/phase-2/` | contract v1.1 |
| PO: `clarify.md`; giao diện: menu, DayIntro/EveningIntro/DayResult/Summary, pause, HUD | @linkiewinkie | `chonoi/web/index.html`, `chonoi/live.py` | snapshot v1.1 |

Mở rộng (nhóm 6 cần ≥ 2 trong cả buổi): để Phase 3–4 khi lõi đúng — ưu tiên `burn` (quán) và `net` (bắt cá).

## Rủi ro
- `day` phụ thuộc mọi lát → tích hợp sớm bằng fixture cố định, mỗi lát giữ test xanh trên `main`.
- Test ẩn kiểm lại Phase 1 với số chuẩn → test cũ đổi phải ghi lý do (đã đổi: số đàn cá đầu ca 6 → 8).
