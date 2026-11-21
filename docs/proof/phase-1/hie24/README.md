# Kiểm chứng issue #3 — Hie24 — Phase 1 Quán

Ngày kiểm chứng: 2026-11-21 (Asia/Saigon). Nhánh: `hie24/phase-1-quan`.

Nguồn: [issue #3](https://github.com/tuancdk/K5-L3B-LAB-Day12-AI-SDLC/issues/3),
[PRD-0 trên lab board](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg#phase-1),
Test Contract v1.0 D/E/F.Quán/G; đọc trực tiếp bằng Playwright qua Edge đã đăng nhập.

Phạm vi mã nguồn: `chonoi/sim/quan.py`, test mới `tests/test_quan_rules.py`.
Không thay contract, schema kho, luật gather, UI, scenario validator hay test cũ.

## Kết quả thật

[unittest.log](unittest.log): **63 test, OK, exit code 0**, gồm 31 test mới cho Quán và 32 test sẵn có.
Môi trường: Windows, Python 3.13.5 (Anaconda), chỉ thư viện chuẩn.
Đã đọc lại diff; `git diff --check` không phát hiện lỗi whitespace.

| Hạng mục issue / PRD | Kiểm chứng trong `tests/test_quan_rules.py` | Kết quả |
|---|---|---|
| Lịch khách theo phase_tick; fixture; ID tiếp nối; bàn bận; no_dish | `test_arrival_exact_schedule_then_full_patience_and_reserved_stock`, `test_schedule_uses_phase_tick_not_shortened_duration`, `test_departure_before_arrival_reuses_table_and_continues_ids`, `test_occupied_table_skips_arrival_without_no_dish`, `test_no_dish_empty_event_repeats_only_at_scheduled_ticks` | Đạt |
| Tồn vật lý, giữ chỗ và kho khả dụng; chọn món bằng Streams | `test_snapshot_defaults_reservations_physical_stock_and_no_fixture_mutation`, `test_available_stock_excludes_other_orders_reservations`, `test_seeded_selection_covers_three_dishes` | Đạt |
| Đơn cũ nhất, thứ tự id; tiêu kho một lần; payload và cook time | `test_oldest_order_then_numeric_table_id_and_snapshot_id_sort`, `test_cook_consumes_reserved_once_and_interact_requires_rising_edge`, `test_cook_items_sorted_and_price_and_time_come_from_tuning` | Đạt |
| Bếp chín đúng tick; nhặt ngay; tuổi món; tay không trống | `test_cook_ready_exact_tick_and_pick_same_tick`, `test_ready_age_and_no_burn`, `test_pick_requires_empty_hand_and_does_not_serve_in_same_interact` | Đạt |
| Một interact; đối tượng gần nhất; ưu tiên bếp; đúng mép bán kính; đúng đơn | `test_nearest_unusable_target_does_not_fall_back`, `test_equal_distance_stove_wins_over_table`, `test_interact_radius_inclusive_and_outside_is_rejected`, `test_wrong_order_cannot_be_served` | Đạt |
| Boa sau giảm timer; floor; trả tiền khi ăn xong; giới hạn uy tín | `test_tip_boundary_after_decrement_and_awarded_only_on_payment`, `test_tip_is_floored_and_base_price_is_payload_price`, `test_reputation_is_clamped_at_both_limits` | Đạt |
| Deadline phục vụ, nhả giữ chỗ, hủy món, không hoàn nguyên liệu nấu | `test_service_on_patience_zero_tick_is_accepted`, `test_patience_leaving_releases_raw_but_never_refunds_cooked_items`, `test_unfulfillable_order_waits_and_cannot_cook` | Đạt |
| Đóng ca: phục vụ/trả ngay, waiting không trừ uy tín, ưu tiên ăn xong, không sinh khách | `test_closing_can_serve_pay_then_end_on_same_tick`, `test_closing_waiting_customer_never_penalizes_even_at_zero_patience`, `test_eating_finish_has_priority_over_closing_and_does_not_spawn` | Đạt |
| Headless thật, cùng seed giống byte, snapshot/end cuối | Ba test trong lớp `QuanHeadless` | Đạt |
| Gather → file kho → Quán, cùng các smoke/unit/live test sẵn có | Toàn bộ suite trong `unittest.log`, gồm `test_inv_01_gather_writes_inventory_quan_reads_it` | Đạt |

Luồng headless hoàn chỉnh đã kiểm chính xác: `cook_started@1`, `dish_ready@361`,
`dish_picked@361`, `served@511`, `paid@1111`; nhận 72 nghìn, uy tín 3.2, điểm 372.
Luồng đóng ca một tick kiểm thứ tự `served`, `paid(reason=closing)`, `quan_end`,
cùng một snapshot cuối tại tick 1 và `end.reason=time`.
Test tất định chạy hai tiến trình với seed -17 trong 4000 tick và so toàn bộ byte JSONL;
có cả khách đến, khách rời, đóng ca; đổi thứ tự khóa stock vẫn giống byte.

## Chạy lại

Linux/macOS, tại gốc repo:

```sh
PYTHONPATH=tests:. python3 -B -m unittest discover -s tests -v
```

Hoặc ghi lại log này bằng `python3 -B docs/proof/phase-1/hie24/verify.py`.
Script chỉ chạy suite và lưu nguyên stdout/stderr, trả đúng mã thoát của test.

Windows: contract vẫn giữ `python3` cho CI Ubuntu. Môi trường tạm đã dùng:

```powershell
$quanEnvPath = Join-Path $env:TEMP 'lab12-hie24-python'
& 'C:\Users\nguye\anaconda3\python.exe' -m venv --without-pip $quanEnvPath
Copy-Item -LiteralPath (Join-Path $quanEnvPath 'Scripts\python.exe') -Destination (Join-Path $quanEnvPath 'Scripts\python3.exe')
$env:PATH = (Join-Path $quanEnvPath 'Scripts') + ';' + $env:PATH
$env:PYTHONUTF8 = '1'
python3 -B docs/proof/phase-1/hie24/verify.py
```

`PYTHONUTF8=1` áp dụng cả subprocess, tránh lỗi giải mã stderr tiếng Việt bằng cp1258.
Lần thử đầu thiếu biến này đã có cảnh báo giải mã dù assertion pass; log bàn giao
là lần chạy sạch UTF-8, exit code 0. Đây là thiết lập môi trường, không sửa test để xanh.

## Ghi chú tích hợp

- `stock` trong snapshot là tồn vật lý, bao gồm phần reserved. Kho khả dụng dùng để chọn món
  bằng tồn vật lý trừ tổng reserved. Khi nấu mới tiêu stock và xóa giữ chỗ của đơn đó.
- Khách dựng sẵn được chuẩn hóa mặc định theo D; đơn reserved thiếu reserved lấy công thức,
  xét theo `order_tick` rồi id bàn. Các trạng thái dùng đúng `reserved/assigned/unfulfillable/served`.
- Payload món giữ `{order_id, dish_id, base_price}`. Event dùng đúng tên/data ở mục E.
- Issue #4 vẫn phụ trách kiểm fixture/contract mâu thuẫn trước khi ghi output;
  thay đổi này xử lý luật trên fixture hợp lệ, không sửa các file của người làm validation.
- Một số unit test mở rộng dữ liệu bàn riêng trong bộ nhớ để kiểm thứ tự và giữ chỗ;
  preset Phase 1 trong `game.contract.json` vẫn một bếp B1, một bàn T1.
- Chưa chạy CI Linux hay test ẩn; kết quả nêu trên là suite công khai chạy thực tế trên Windows.
- AI đã triển khai luật, test và ghi chứng cứ bằng Codex; không đo được token/chi phí.
  Người dùng cần tự đọc lại trước khi push theo AGENTS.md; chưa tự nhận đã có human review.
