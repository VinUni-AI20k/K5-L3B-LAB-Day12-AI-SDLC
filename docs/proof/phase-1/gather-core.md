# Gather core · Ticket 02

Kiểm trên nhánh `feat/cao-minh` với Python 3.12.5. Trên Windows, suite dùng `PYTHONPATH=tests;.` và một launcher `python3.exe` trong môi trường ảo tạm để chạy đúng `headless_cmd` của repo.

```powershell
$env:PYTHONPATH = 'tests;.'
python3 -m unittest discover -s tests -v
```

Kết quả thực tế:

```text
Ran 37 tests in 13.039s

OK
```

| Hành vi | Kết quả kiểm qua headless |
|---|---|
| Hồi oxy ở mặt nước | Oxy từ 1790 lên 1796 rồi 1800, giữ ở mức tối đa đến tick 1800. |
| Đi qua biên mặt nước | `dive` trước `oxygen_empty` ở tick 1; `dive` và `surface` có vị trí sau khi di chuyển. |
| Ngạt và ngất | `oxygen_empty` ở tick 1, sau đó `choke` ở tick 60, 120 và 180. Tick 180 phát `faint` rồi `gather_end`. Giỏ mất theo thứ tự nhặt sau bỏ trước và file kho là `{"items":{}}`. |
| Nổi đúng bước sẽ ngạt | Hồi 6 tick oxy, reset bộ đếm ngạt, giữ 1 Máu. |
| Ngất cùng tick với E, Space và hết giờ | Kết thúc với `fainted`, đàn cá vẫn còn. Giỏ rỗng cho `lost: []`. |
| Hồi quy | Qua kiểm di chuyển và chặn biên, hết giờ giữ giỏ, giới hạn tick giữ file kho, JSONL tất định và smoke hai tiến trình Gather → Quán. |

Năm ca Gather core nằm trong [test_gather_core.py](../../../tests/test_gather_core.py).
