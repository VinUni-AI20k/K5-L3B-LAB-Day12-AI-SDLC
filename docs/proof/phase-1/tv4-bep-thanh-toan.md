# TV4 · Bếp và thanh toán

Kiểm chứng bằng CLI headless với khách dựng sẵn và `random_customers: false`, theo PRD-0 mục D–F. Các tick dưới đây lấy từ JSONL mà test đọc và đối chiếu. Lịch sinh khách thuộc TV3.

| Tình huống | Kết quả với preset của nhóm |
|---|---|
| Nấu lẩu từ kho có 4 cá linh và 1 bông điên điển | Tick 1 trừ 3 cá và 1 bông, xóa giữ chỗ. Tick 601 phát `dish_ready` rồi `dish_picked` cho cùng đơn C7. |
| Bưng lẩu cho khách rồi đợi ăn xong | Tick 631 phục vụ. Tick 1230 tiền vẫn bằng 0. Tick 1231 thu 120 tiền món và 24 tiền boa, giải phóng bàn. Điểm cuối là 444. |
| Phục vụ khi kiên nhẫn vừa về 0 | Tick 1 vẫn phục vụ được. Khi đóng cửa ở tick 2, khách trả 60, boa 0. |
| Phục vụ đúng bước cuối | Thứ tự `served → paid → quan_end`, chỉ thu một lần. Sau giảm kiên nhẫn còn 1800/3600 tick thì boa 12 trên giá 60. Còn 1799 thì boa 0. |
| Hết kiên nhẫn trùng lúc đóng cửa khi chưa phục vụ | Khách rời với `closing`, bỏ món đang cầm, uy tín giữ ở 3. |
| Ăn vừa xong đúng bước cuối | Thu với `finished_eating` trước khi đóng ca. Uy tín từ 4.9 tăng đến trần 5, điểm cuối 572. |
| Bếp và bàn cùng cách người chơi 1.5 m | Chọn bếp trước. Tay vẫn giữ món của bàn khi bếp idle và không có đơn reserved. |
| Fixture có món sai đơn, trùng món, thiếu món hoặc timer nấu mâu thuẫn | CLI thoát mã 2 trước khi tạo JSONL. |

Chạy lại riêng 6 test TV4 bằng `PYTHONPATH=tests:. python3 -m unittest tests.test_quan_kitchen -v`. Bộ test toàn dự án chạy bằng `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`, kết quả 41/41 đạt trên cây làm việc. Test live cần mở được cổng localhost tạm thời.

[Mã kiểm chứng và fixture](../../../tests/test_quan_kitchen.py)
