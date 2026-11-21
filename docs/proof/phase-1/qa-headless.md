# Bằng chứng QA headless Phase 1

- Commit mã luật trên `main` tại thời điểm kiểm tra: `c3441f9` (`origin/main`).
- Commit của bộ [test tích hợp](../../../tests/test_integration.py): `c82ea72`. Log ghi mã `c686e7e` trước khi rebase. Nội dung file test giống nhau ở hai commit.
- Hệ điều hành và phiên bản Python: Windows, Python 3.13.17.

## Cách chạy lại

Trên Linux hoặc macOS, từ thư mục gốc của repo:

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
PYTHONPATH=tests:. python3 -m unittest test_integration -v
```

Nếu `python3` trỏ tới alias WindowsApps, dùng trình thông dịch Python đã cài cho tiến trình con. Các tham số CLI vẫn lấy từ `game.contract.json`. Test HTTP dùng kết nối loopback.

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

Ghi kết quả lần chạy đầy đủ và dẫn tới log thực tế.

- Số test đạt trên tổng số test: **41/41** với bộ test trên `origin/main`. **43/50** khi thêm test tích hợp QA vào bản sao cùng commit.
- Số ca thất bại và lỗi: **7 phương thức QA chưa qua**, trong đó một phương thức có hai subtest đỏ. Unittest ghi 8 assertion failures và 0 errors ở lần chạy trên mã `main`.
- Log: [unittest.txt](unittest.txt), gồm hai lượt trên `origin/main` và hai lượt kiểm tra nhánh đang phát triển.

| Test QA | Kết quả quan sát | Yêu cầu theo PRD-0 |
|---|---|---|
| Cập bến ở bước cuối và bàn giao tất định | Phát `gather_end` với `docked`. Hai lượt cho ra cùng byte JSONL ở hai pha và cùng byte file kho. | Cập bến được ưu tiên trước hết giờ. `quan` nạp đúng số lượng từ file kho. |
| Chạm giới hạn bước | File kho có sẵn giữ nguyên từng byte. | Chỉ ghi kho khi `gather_end`. |
| Hái ở bước cuối | Có `node_regrown` và `gather_end`. Thiếu `gather`. | Nút vừa mọc có thể hái ngay. Một bông súng vào kho và quán đọc được. |
| Bắt cá ở bước cuối | Chỉ có `gather_end`. | Chọn F2 trước F10 khi cùng khoảng cách. Phát `fish_caught` và tính cá vào kho. |
| Giỏ thiếu chỗ | Thiếu `hold_full`. | Báo thiếu chỗ cho F1. Giữ nguyên đàn, giỏ và hồi chiêu. |
| Hết oxy | `oxygen_empty.data` hiện là `{"pos":[20.0,5.0]}`. | Dữ liệu sự kiện cần `{"oxygen_ticks":0}`. |
| Ngất và bỏ giỏ | Kho rỗng và quán nạp được. `faint.data` có `pos` và bảng đếm `lost`. | Dữ liệu cần `cause: "choke"`, `hp: 0` và mảng `lost` theo thứ tự LIFO. |
| Lịch khách với kho đủ và kho rỗng | Hai subtest đều thiếu sự kiện ở tick 120. | Kho đủ phát `customer_arrived` và giữ đúng công thức. Kho rỗng phát `no_dish`. |
| Phục vụ đúng tick hết kiên nhẫn và đóng ca | Chỉ có `quan_end` ở tick 1. | Phát `served` rồi `paid` với lý do `closing` trước `quan_end`. Boa bằng 0. |

## Kiểm tra các nhánh đang phát triển

Dùng các bản sao tạm từ `git archive`, chép bộ test QA vào từng bản rồi chạy riêng các ca liên quan. Ghi rõ commit đã chạy ở mỗi dòng.

| Bản luật | Kết quả | Phát hiện |
|---|---|---|
| `origin/letheanh/gather-harvest` tại `483664e` | 0/3 test QA đạt | Ca hái và bắt đã qua kiểm tra bàn giao kho. Ca thiếu chỗ giữ đúng đàn, giỏ và hồi chiêu. Ba ca còn đỏ ở dữ liệu `gather.amount`, `fish_caught.yield` và các trường `hold_full`. |
| `origin/minhthu27/quan-service` tại `116cf99` | 0/1 test QA đạt | Headless thoát mã 1 với `KeyError: 'dish'` khi tương tác bàn. Fixture dùng trường `dish_id` và object món trên tay theo PRD-0 mục D. |

Chạy lại sau khi gộp các lát, lưu kết quả trên commit bàn giao Phase 1 và cập nhật [ma trận truy vết](../../verification/phase-1.md) trước khi gắn tag.
