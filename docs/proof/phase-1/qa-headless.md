# Bằng chứng QA headless Phase 1

- Mã luật trên `origin/main` tại thời điểm kiểm tra: `c872ef2`.
- Test tích hợp của Kaylez: `c686e7e`, file [test_integration.py](../../../tests/test_integration.py).
- Chạy trên Windows với Python 3.13.17. Test HTTP sử dụng kết nối loopback.

## Cách chạy lại

Trên Linux hoặc macOS, từ thư mục gốc của repo:

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
PYTHONPATH=tests:. python3 -m unittest test_integration -v
```

Trên máy Windows đã kiểm chứng, `python3` là alias WindowsApps. Lượt chạy dùng trình thông dịch đã cài cho tiến trình con, với các tham số CLI lấy từ `game.contract.json`.

```powershell
$env:PYTHONPATH = 'tests;.'
$env:NO_PROXY = '127.0.0.1,localhost'
@'
import helpers
import sys
import unittest

read_command = helpers.headless_cmd

def windows_command():
    command = read_command()
    if command[0] == "python3":
        return [sys.executable, *command[1:]]
    return command

helpers.headless_cmd = windows_command
suite = unittest.defaultTestLoader.discover("tests")
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
'@ | python -
```

## Kết quả trên mã main

Trích kết quả lần chạy đầy đủ trên mã luật `c872ef2` với bộ test tích hợp:

```text
Ran 50 tests in 9.855s
FAILED (failures=8)
Methods passed: 43/50; assertion failures: 8; errors: 0
```

**43/50 phương thức test đạt.** Cả 41 test có sẵn, gồm test HTTP, đều qua. Hai ca QA qua là cập bến ở bước cuối với JSONL và file kho giống từng byte, và giữ nguyên file kho khi chạm giới hạn bước. Bảy phương thức QA chưa qua, trong đó test lịch khách có hai subtest đỏ.

| Test QA | Kết quả quan sát | Yêu cầu theo PRD-0 |
|---|---|---|
| `test_hai_nut_vua_moc_lai_o_buoc_cuoi_roi_chuyen_kho` | Có `node_regrown` và `gather_end` ở tick 1 | Phát thêm `gather` giữa hai sự kiện. Một bông súng phải vào kho và quán đọc được. |
| `test_bat_ca_o_buoc_cuoi_uu_tien_id_va_chuyen_kho` | Chỉ thấy `gather_end` ở tick 1 | Chọn F2 trước F10 khi cùng khoảng cách. Phát `fish_caught` trước khi chốt kho. |
| `test_gio_thieu_cho_giu_ca_va_khong_dat_hoi_chieu` | Thiếu `hold_full` | Phát `hold_full` cho F1 với `action: "catch"`, `required: 3`, `free: 1`. Cá và giỏ giữ nguyên, hồi chiêu vẫn 0. |
| `test_oxygen_empty_co_payload_theo_contract` | Sự kiện ở tick 1 mang `{"pos":[20.0,5.0]}` | Dữ liệu sự kiện là `{"oxygen_ticks":0}`. |
| `test_ngat_bo_gio_theo_lifo_va_xuat_kho_rong` | Kho rỗng và quán đọc được. `faint.data` mang `pos` và bảng đếm `lost`. | Dữ liệu `faint` có `cause: "choke"`, `hp: 0` và `lost: ["bong_sung","ca_linh","ca_loc"]`. |
| `test_quan_goi_mon_theo_kho_va_lich_khach` | Hai subtest đều thiếu sự kiện ở tick 120 của preset | Kho có một cá lóc phát `customer_arrived` và giữ đúng công thức. Kho rỗng phát `no_dish`. |
| `test_quan_phuc_vu_o_tick_het_kien_nhan_va_dong_ca` | Chỉ thấy `quan_end` ở tick 1 | `served` rồi `paid` với lý do `closing` trước `quan_end`. Khách trả giá món và boa bằng 0. |

## Kiểm tra các nhánh đang phát triển

Dùng các bản sao tạm từ `git archive`, chép bộ test QA vào từng bản rồi chạy riêng các ca liên quan. Mỗi dòng dưới đây gắn với commit đã chạy.

| Bản luật | Kết quả | Phát hiện |
|---|---|---|
| `origin/letheanh/gather-harvest` tại `e04b3fa` | 3 ca chạy, 3 lỗi assertion | Hái và bắt ở bước cuối đã chuyển đúng kho sang quán. Trạng thái giỏ, cá và hồi chiêu đúng khi thiếu chỗ. Sự kiện `gather` dùng `count` và `hold_count` thay vì `amount`. `fish_caught` dùng `count` và `hold_count` thay vì `yield`. `hold_full` vẫn thiếu `action`, `fish_id`, `required` và `free`. |
| `origin/minhthu27/quan-service` tại `116cf99` | 1 ca chạy, 1 lỗi assertion | Headless thoát mã 1 vì `KeyError: 'dish'` tại `_use_table`. Fixture hợp lệ theo mục D dùng `dish_id` cho khách và object món cho `hand`. |

Ma trận hiện dùng bằng chứng sơ bộ. Chạy lại sau khi gộp các lát và lưu kết quả trên commit bàn giao Phase 1.
