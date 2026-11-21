# Truy vết Phase 3 (TICKET-03, Test Contract v1.2 — Lõi "Độ tươi")

Lệnh: `PYTHONPATH=tests:. python3 -m unittest discover -s tests` → 151 test, OK (xem `docs/proof/phase-3/proof_output.txt`).
Bằng chứng chạy lại: `bash docs/proof/phase-3/run_proof.sh`. Chưa commit/tag tại thời điểm ghi — phải chạy lại ở commit gắn tag.

| AC | Nội dung | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P3-01 | Quán hao 0.25/s chính xác (60 tick = −0.25), ngưỡng 30 chưa ươn | `test_quan_p3.test_ac_p3_01` | Đạt |
| AC-P3-02 | spoiled ở kho phát một lần, theo id, hàng ươn vẫn trong kho, kẹp 0 | `test_ac_p3_02` | Đạt |
| AC-P3-03 | Giữ chỗ tươi nhất, hòa theo id | `test_ac_p3_03` | Đạt |
| AC-P3-04 | Phần giữ vừa ươn → nhả, giữ lại một lần; không đủ → unfulfillable, khách vẫn chờ | `test_ac_p3_04` | Đạt |
| AC-P3-05 | cook_started tiêu đúng id giữ, items sắp kind rồi id, base_price = floor(giá × mean fresh/100) | `test_ac_p3_05` | Đạt |
| AC-P3-06 | Boa = floor(giá đã chốt × 0.2) | `test_ac_p3_06` | Đạt |
| AC-P3-07 | Hàng ươn không nấu được (unfulfillable, no_dish) | `test_ac_p3_07` | Đạt |
| AC-P3-08 | Fixture sai (reserved trỏ hàng ươn / id lạ / dùng chung / sai công thức, kho đếm, fresh ngoài miền, id trùng, kind lạ) → mã 2 | `test_ac_p3_08` | Đạt |
| AC-P3-09 | Pause dừng hao tươi | `test_ac_p3_09` | Đạt |
| AC-P3-30 | Smoke bàn giao file gather → quan --ticks 0: id/kind/fresh khớp file | `test_smoke_p3.test_ac_p3_30`, `docs/proof/phase-3/{kho.json,quan.jsonl}` | Đạt (fresh 99.99167 ±0.01) |
| AC-P3-31 | quan v1.2 từ chối file kho đếm (mã 2) | `test_ac_p3_31`, `proof_output.txt` | Đạt |
| AC-P3-32 | day: bàn giao cùng tick gather_end, không hao thêm; day --days 2 chạy | `test_ac_p3_32`, `docs/proof/phase-3/day2.jsonl` | Đạt (proof day2 dừng ở tick_limit 30000, days_completed=1 — chưa kiểm hết Ngày 2 không input) |
| Regression | P1–P2 còn hiệu lực qua `tests/v12_compat.py`; giá cũ 60/200 đổi 59/199 theo luật giá chốt | `test_quan_p1/p2`, `test_day_p2`, `test_smoke_p2` | Đạt |

Chưa có test riêng: id mới ở Ngày 2 cho gather.hold (dựa `GatherSim(reissue_hold_ids)` của lát Lặn), snapshot Shop dạng cá thể (chỉ kiểm thủ công qua code).
