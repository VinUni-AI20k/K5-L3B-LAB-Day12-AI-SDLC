# Smoke tích hợp Phase 2 — gather → quán

- Bản kiểm thử: `751da31`.
- Môi trường: Windows PowerShell, Python 3.11.9.
- Seed: 42.

## Fixture và lệnh chạy

`gather-scenario.json`:
```json
{"gather":{"hold":["ca_loc","bong_sung","bong_sung"],"random_fish":false}}
```

`inputs.json`:
```json
{"frames":[{"tick":0,"interact":true}]}
```

Các lệnh dưới đây dùng đường dẫn tới hai fixture trong thư mục tạm:

```powershell
python3 -m chonoi.headless --mode gather --seed 42 --ticks 1 --scenario $scenario --inputs $inputs --inventory-out $inventory --out $gatherOut
python3 -m chonoi.headless --mode quan --seed 42 --ticks 0 --inventory $inventory --out $quanOut
```

## Kết quả baseline

- Cả hai tiến trình thoát với mã 0.
- `gather_end` ở tick 1 có `reason: "docked"` và inventory `{"items":{"bong_sung":2,"ca_loc":1}}`.
- File kho xuất ra khớp inventory của sự kiện.
- Snapshot đầu của quán ở tick 0 có `stock: {"bong_sung":2,"ca_loc":1}`.
- Kết luận: đạt trên `751da31`. Chạy lại trên bản tích hợp Test Contract v1.1 để chốt kết quả bàn giao.

## Kiểm chứng trên nhánh quán Phase 2

- Regression toàn bộ suite trên nhánh quán `2090b6e`: 48/48 đạt trong 10,446 giây, chạy bằng `python3 -m unittest discover -s tests -v` với `PYTHONPATH=tests;.`. Kết quả gồm hai ca QA Phase 1. Ba ca QA Phase 2 trong PR #7 chờ chạy trên bản tích hợp.

- Bản kiểm thử: `origin/codex/quan-phase-2` tại `2090b6e`.
- Môi trường: Windows PowerShell, Python 3.11.9.
- Kết quả: 14/14 test đạt trong 0,901 giây, gồm 12 ca quán và 2 ca bàn giao kho.

```powershell
$env:PYTHONPATH = 'tests;.'
python3 -m unittest -v tests.test_quan tests.test_smoke_p1.Integration.test_inv_01_gather_writes_inventory_quan_reads_it tests.test_smoke_p1.Integration.test_inv_01_not_written_when_tick_limit_first
```

- Snapshot quán có 2 bếp và 4 bàn. Các ca thứ tự nhận đơn, món mới, lọc món theo kế hoạch Ngày trong quán và dọn ca đều đạt.
- Quán đọc đúng kho tại tick 0. Khi gather dừng do giới hạn tick trước khi kết thúc, file kho đích giữ nguyên.
- Kết quả thuộc nhánh quán tại `2090b6e`. Chờ chạy lại trên bản tích hợp Phase 2.

## Bàn giao nguyên liệu mới tại `9f4c078`

- **Gather → quán:** Dùng seed 42, `gather.hold=["ca_keo","ca_keo","keo_neo"]`, `random_fish:false` và `interact:true` ở input tick 0. Gather trả mã 2 với lỗi `hold phải là mảng id nguyên liệu hợp lệ`. Luồng dừng ở bước kiểm tra fixture gather.
- **Quán độc lập:** Nạp trực tiếp `{"items":{"ca_keo":2,"keo_neo":1}}` bằng `--inventory`, chạy với seed 42 và `--ticks 0`. Snapshot tick 0 có `stock: {"ca_keo":2,"keo_neo":1}`. Kết quả: đạt.