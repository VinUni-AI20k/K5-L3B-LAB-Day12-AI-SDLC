# Bằng chứng Lát 2 — Phát (`trdphat`)

Ngày 2026-11-21, nhánh `p1/lat2-phat`, nền Hưng Lát 1 commit `8d0556b`; đã gộp main `ba94fe7` trước khi mở PR.

## Kết quả thật

- Toàn bộ **71 test PASS** sau khi gộp main, gồm 20 test luật Lát 2 và 2 test tích hợp kho mới; xem [unittest.txt](unittest.txt).
- Smoke hái/bắt/cập bến: gather ở tick 1, 3, 5; fish_caught ở tick 36, 66; gather_end docked ở tick 181. Xem [gather-events.json](gather-events.json) và [gather-end.json](gather-end.json).
- [catch.json](catch.json) là file kho thật do runner ghi: `bong_dien_dien=1`, `bong_sung=2`, `ca_linh=3`, `ca_loc=1`.
- Tiến trình quán riêng nạp file trên, snapshot tick 0 có stock trùng file kho và `gather_end.inventory`; xem [quan-snapshot.json](quan-snapshot.json).
- Test `test_collect_dock_export_and_load_in_separate_quan_process` chạy hai lần cùng seed và so byte của cả JSONL lẫn file kho.
- [team-check.txt](team-check.txt): mã 1 vì Minh còn handle `…`; handle Phát đã điền `trdphat`.

## Chạy lại

Tại thư mục gốc repo, với `python3` trong PATH:

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 -m chonoi.headless --mode gather --seed 42 --ticks 240 --scenario tests/fixtures/gather_lat2/dock.json --inputs tests/fixtures/gather_lat2/inputs.json --inventory-out docs/proof/phase-1/lat2-phat/catch.json --out docs/proof/phase-1/lat2-phat/gather.jsonl
python3 -m chonoi.headless --mode quan --seed 42 --ticks 0 --inventory docs/proof/phase-1/lat2-phat/catch.json --out docs/proof/phase-1/lat2-phat/quan.jsonl
python3 tools/check_team.py
```

Phiên này dùng Windows / Python 3.13.17, venv tạm `%TEMP%\doctorx-phat-python` có launcher `python3.exe` (máy chỉ có lệnh `python`, alias `python3` mặc định mở Store). PowerShell thiết lập trước khi chạy các lệnh Python trên:

```powershell
$env:PATH = (Join-Path $env:TEMP 'doctorx-phat-python/Scripts') + ';' + $env:PATH
$env:PYTHONPATH = 'tests;.'
$env:PYTHONUTF8 = '1'
```

`PYTHONUTF8=1` đồng bộ mã hóa giữa tiến trình test và các tiến trình headless khi đọc stderr tiếng Việt. Lượt thử chỉ đặt `PYTHONIOENCODING` đã gặp lỗi giải mã ở thread đọc subprocess; đã sửa môi trường và chạy lại sạch, log cuối lưu ở trên. JSONL đầy đủ bị `.gitignore` bỏ qua theo quy ước repo; các file JSON trích xuất trong thư mục này giữ sự kiện và snapshot cần review.

## Phạm vi kiểm chứng

| Yêu cầu | Kiểm thử |
|---|---|
| Hái nút ready gần nhất; hòa theo ID tự nhiên; chỉ mặt nước | `test_gather_lat2.GatherLat2` — nearest, tie, radius, surface |
| Yield lấy từ tuning; giỏ giữ thứ tự và không nhận một phần | node_yield, fish_yield, full_hold |
| Nút mọc lại và cooldown hết đúng bước | regrow_counter, simultaneous_regrowth, catch_cooldown |
| Cạnh lên, vị trí sau di chuyển, ưu tiên bến/ngất/hết giờ | held_buttons, surface_and_dive, action_radius, dock, faint, last_tick |
| Kho thật, quán đọc lại, cùng seed giống byte | `test_gather_lat2_inventory.GatherInventory` |

## Điểm cần chốt khi tích hợp

Đã review implementation bằng agent; Hưng cần review chéo trước khi đẩy theo TEAM.md. Bước tiếp theo là đẩy nhánh `p1/lat2-phat` và mở PR vào `main`.

Payload đã khớp hợp đồng Integrator trên main: `gather {node_id, kind, amount}`, `fish_caught {fish_id, kind, yield}`, `hold_full {required, free}`. Test đổi payload để kiểm đúng hợp đồng hiện hành, giữ nguyên các kiểm tra luật. Còn giả định cooldown chỉ bắt đầu khi bắt thành công, xem `docs/clarify.md`. Dùng API giỏ thực tế của Hưng (`can_hold`/`push_hold`/`free_hold_slots`); tên helper trong tài liệu hợp đồng khác với code đã bàn giao, cần Hưng/Diệp đối chiếu khi review. Không đổi tuning hoặc schema kho.
