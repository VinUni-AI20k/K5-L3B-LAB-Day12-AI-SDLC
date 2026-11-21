# Ma trận kiểm chứng Phase 2 (`Test Contract v1.1`)

| AC | Hạng mục kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Số liệu chuẩn `v1.1` | `contract_version: "1.1"`, 6 nguyên liệu, 6 món, 2 bếp `B1–B2`, 4 bàn `T1–T4`, `day_plan` D1–D5, `shop` | `game.contract.json`, `chonoi/contract.py`, `tests/test_smoke_p1.py` | Đạt |
| Gather v1.1: cá bơi & sinh thêm | 8 đàn đầu ca theo seed, bơi `1.5 m/s`, đổi hướng bước 120, phản xạ mép, sinh `360·k` trần 12 | `tests/test_gather_v11.py` | Đạt |
| Thủy quái `ca_sau` M1/M2 & Máu | M1 ngày 1 / M2 ngày 3, patrol/chase/hit LIFO `floor(n/2)`/invuln 90/recoil 60/ngất `cause:"monster"` | `tests/test_gather_v11.py` | Đạt |
| Vòng Ngày `day` & Shop | `--mode day --days 1..5`, `day_plan` D1–D5, Shop mua `oxygen`/`hp`, `buy_failed`, nâng cấp áp dụng Ngày kế | `tests/test_day_shop_pause.py`, [day1.jsonl](../proof/phase-2/day1.jsonl) | Đạt (`--days 1` chạy ~1s <= 20s) |
| Tạm dừng `pause`/`resumed` | `pause` trên 3 mode (kể cả Shop) đóng băng `sim_tick`/`phase_tick`/timer; `resumed` chạy gameplay ngay bước đó | `tests/test_day_shop_pause.py` | Đạt |
| Smoke tích hợp v1.1 & hồi quy | `gather --inventory-out` -> `quan --inventory`, giữ nguyên test P1–P2 (ghi rõ lý do cập nhật 3 test v1.0) | [integration.gather.jsonl](../proof/phase-2/integration.gather.jsonl), [integration.inventory.json](../proof/phase-2/integration.inventory.json), [integration.quan.jsonl](../proof/phase-2/integration.quan.jsonl) | Đạt: `85/85` test OK, `check_team.py` đạt |

> Ghi chú cập nhật test cũ: `test_smoke_p1.py` (cập nhật 8 đàn cá và cho phép `--mode day`), `test_gather_items.py::Catch` (thêm `random_fish: false` do v1.1 cá tự bơi khỏi điểm fixture), `test_quan_customers.py` (cố định 1 bàn ở test khách duy nhất do v1.1 mở 4 bàn).
