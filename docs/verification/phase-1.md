# Ma trận truy vết Phase 1

Kiểm tra ngày 21/11/2026 trên mã game và test tại commit `c872ef2`, với Python 3.12.14 trên Windows. Ma trận dùng tên hành vi trong repo. Mã AC chính thức chờ đối chiếu PRD-0 theo [Clarify #5](../clarify.md).

| Hành vi | Cách kiểm chứng | Bằng chứng | Kết quả trên commit kiểm chứng |
|---|---|---|---|
| Headless khởi động ở cả hai mode, có snapshot tick 0 và đúng một dòng `end` | Nhóm test `Contract` | [Log unittest](../proof/phase-1/unittest.txt) | Đạt theo test công khai |
| Cùng seed và đầu vào cho JSONL giống từng byte | Test có input cho `gather`. Chạy lại fixture mặc định ở cả hai mode với seed 1, 600 tick. | [Log unittest](../proof/phase-1/unittest.txt), [so byte và SHA-256](../proof/phase-1/headless.txt) | Đạt cho các lượt đã chạy |
| Đầu vào hoặc kho sai trả mã 2 | Các test `Contract`, `ScenarioModes` và `Integration` truyền mode, input, scenario hoặc kho sai | [Log unittest](../proof/phase-1/unittest.txt) | Đạt theo test công khai |
| Di chuyển, đổi hướng, chặn mép và hết giờ khi đi hái | Nhóm test `Movement` | [Log unittest](../proof/phase-1/unittest.txt) | Đạt theo test công khai |
| Lặn, nổi, oxy, ngạt, ngất và giỏ | `test_gather_oxy` kiểm tra mốc sự kiện và số liệu. Hai test giỏ gọi trực tiếp `_add_to_hold`. | [Log unittest](../proof/phase-1/unittest.txt) | Đạt theo các test của lát 1 |
| Cập bến xuất kho và quán đọc kho đúng | `test_inv_01_gather_writes_inventory_quan_reads_it` nạp sẵn giỏ rồi chuyển kho qua file. Test kèm theo xác nhận chưa ghi kho khi chạm giới hạn tick. | [Log unittest](../proof/phase-1/unittest.txt) | Đạt theo test công khai |
| Hái nút, mọc lại và bắt cá | Cần chạy replay có `interact` ngoài bến và `catch` dưới nước, rồi đối chiếu sự kiện và giỏ | [Khung lát 2](../../chonoi/sim/gather_harvest.py) | Chưa kiểm chứng trên bản tích hợp. `try_gather` và `try_catch` đang là hàm khung. |
| Khách vào, gọi món và bỏ đi | Cần kiểm tra khách đến khi còn bàn, giữ chỗ, hết kiên nhẫn và thay đổi kho/uy tín | [Khung lát 3](../../chonoi/sim/quan_customers.py) | Chưa kiểm chứng trên bản tích hợp. Logic khách đang là hàm khung. |
| Nấu, bưng, phục vụ và thu tiền | Cần replay từ `cook_started` đến `paid` và đối chiếu nguyên liệu, tiền, boa, uy tín | [Khung lát 4](../../chonoi/sim/quan_service.py) | Chưa kiểm chứng trên bản tích hợp. Logic phục vụ đang là hàm khung. |
| Danh sách thành viên | Chạy `python3 tools/check_team.py` | [TEAM.md](../../TEAM.md) | Chưa đạt. Bốn thành viên còn thiếu tên. |

## Chạy lại

```sh
python3 tools/phase_evidence.py tests --out playground/phase-1/unittest.txt
python3 tools/phase_evidence.py headless --out playground/phase-1/headless.txt
```

## Đánh giá ngắn

41/41 unittest đạt. Hai mode mặc định cho JSONL khớp từng byte và dừng ở tick 600 với `tick_limit`. Test chuyển kho bắt đầu bằng giỏ có sẵn, nên luồng hái/bắt cá → cập bến → nấu → phục vụ vẫn cần replay trên commit tích hợp các lát. Ghi mã commit và cập nhật bằng chứng sau khi Lead gộp.
