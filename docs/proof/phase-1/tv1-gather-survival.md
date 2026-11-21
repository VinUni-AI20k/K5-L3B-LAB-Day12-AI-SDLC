# TV1 · Kiểm chứng sinh tồn ở ca sáng

Chạy `python -m unittest discover -s tests` trên bản triển khai TV1. Kết quả 35/35 test đạt, gồm ba ca headless sau.

| Ca theo PRD-0 mục F | Kết quả |
|---|---|
| Lặn với 1 tick oxy | `dive` và `oxygen_empty` ở tick 1. `choke` ở tick 60, còn 2 Máu. |
| Nổi khi bộ đếm ngạt đang là 59 | Phát `surface`, hồi 6 tick oxy, đưa bộ đếm về 0 và giữ 3 Máu. |
| Ngất cùng bước với tương tác ở bến và hết giờ | Phát `choke` → `faint` → `gather_end`. Mất đồ theo LIFO, file kho rỗng và lý do kết thúc là `fainted`. |

[Test headless của TV1](../../../tests/test_gather_survival.py)
