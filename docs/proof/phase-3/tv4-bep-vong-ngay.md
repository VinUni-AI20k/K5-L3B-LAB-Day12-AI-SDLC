# TV4 · Bếp, giá và vòng ngày

## Lệnh và kết quả

```sh
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

Cây làm việc trên contract v1.1 chạy 98 test, 97 đạt, 1 bỏ qua do cần ghép schema cá thể. Test HTTP mở cổng localhost tạm thời.

Trên bản ghép tạm từ `b237586`, áp diff của TV2 (`513ea6c`), TV3 (`43b48f2`) và phần TV4. Dùng phương thức nấu của TV4 thay phương thức tạm của TV3. Bản ghép có tuning freshness từ TV3, còn manifest và adapter file vẫn ở v1.1.

```sh
PYTHONPATH=tests:. python3 -m unittest tests.test_tv4_freshness_p3 tests.test_gather_freshness_p3 tests.test_quan_fresh_p3 -v
```

**14/14 đạt**, gồm đủ 3 test TV4.

| Ca kiểm | Kết quả |
|---|---|
| Tiêu ID đã giữ và chốt giá một lần | Lẩu cá linh dùng đúng `I8, I2, I3, I10` theo kind rồi ID. `I4` vẫn trong kho. Giá chốt 84 giữ qua `served` và `paid`. Boa 16, tổng thu 100. |
| Trung bình ngay sát biên floor | Gỏi giá niêm yết 40. Fresh `[79.99999999999999, 80]` cho giá 31. Fresh `[80, 80]` cho giá 32. |
| Bàn giao kho, pause và Shop | Snapshot quán ở `phase_tick: 0` khớp `gather_end.inventory.items`. Sau khi nấu hết `I10`, Shop chỉ còn `I2`, một cá thể ươn. Fresh của nó giữ nguyên qua các bước Shop, pause và resume. |
| ID mẫu qua ngày | D1 giữ thứ tự `I10, I2`. D2 cấp `I11, I12` theo thứ tự mẫu với fresh ban đầu, kể cả khi ID cao nhất D1 đã tiêu. Đơn fixture chuyển tham chiếu từ `I10` sang `I11` và nấu đúng món. |

## Ca biên còn lỗi trên bản ghép

Dựng quán với một cá lóc fresh `50.25` đã giữ cho cá lóc nướng trui, đứng ở B1 và bấm E tại frame `tick: 59`. Sau 60 bước, fresh theo ticket là 50 và giá phải là 30. Bản ghép đo `49.9999999999998` và phát `cook_started.base_price: 29`. Sai số phát sinh trong phép trừ float lặp ở `chonoi/freshness.py` của nhánh TV3. Phép tính giá của TV4 giữ độ chính xác của giá trị được truyền vào.

TV1/TV3 cần chốt biểu diễn hao tươi dùng chung đủ chính xác rồi kiểm lại ca này. Smoke bàn giao qua file và từ chối kho đếm v1.2 chờ adapter của TV1. [Test TV4](../../../tests/test_tv4_freshness_p3.py)

## Review tích hợp PR #17

Đã resolve xung đột với main chứa adapter TV1 và kho cá thể TV2/TV3. Dùng price_for_items để tính giá từ chính xác các cá thể giữ chỗ. decay_units dùng decay_items của TV1 để tránh tích lũy sai số float. Bổ sung regression cá lóc fresh=50.25 sau đúng 60 bước quán có fresh=50 và giá 30, đạt.

Cấp lại ID fixture qua ngày chọn theo version nội bộ, giữ đường chạy v1.1 trong giai đoạn chuyển tiếp. Test vòng ngày cá thể đặt version 1.2 rõ ràng.

Bản cuối đạt 121/121 test, gồm live/live_day và 4 test TV4. [Log review](pr17-review.log). Manifest hiện giữ v1.1, việc bật toàn bộ v1.2 và kiểm smoke file/day qua CLI thuộc bước nghiệm thu tích hợp Phase 3 tiếp theo.
